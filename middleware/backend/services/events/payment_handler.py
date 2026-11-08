import logging
from backend.infrastructure.db_adapter import db_adapter
from backend.services.payments.liquidity_management import liquidity_mgmt_service

logger = logging.getLogger(__name__)


async def _get_coop_from_event_data(data: dict):
    """
    Finds the fsp owner of a wallet ID.
    Supports both direct fsp wallets and Member wallets.
    """
    wallet_id = data.get("walletAddressId")
    if not wallet_id:
        raise Exception("walletAddressId missing in event data")

    # 1. Fetch all fsps to check if it's a direct Coop wallet
    all_coops = await db_adapter.get_all_fsps()
    for coop in all_coops:
        meta = coop.get("rafiki_metadata") or {}
        if meta.get("wallet_address_id") == wallet_id:
            return coop

    # 2. --- THE FIX: Check if it belongs to a MEMBER ---
    logger.info(f"Wallet {wallet_id} not found in Coops. Checking Members...")

    # We need a way to find a member by their Rafiki Wallet ID
    # Ensure Team C has implemented: GET /internal/member/wallet/{wallet_id}
    member_res = await db_adapter.get_member_by_rafiki_id(wallet_id)

    if member_res and member_res.get("data"):
        member = member_res["data"]
        parent_coop_id = member.get("fsp_id")

        # Now fetch the parent fsp to get the secrets needed for withdrawal
        return await db_adapter.get_fsp(str(parent_coop_id))

    return None


async def handle_outgoing_created(data: dict, event_tenant_id: str = None):
    """
    [JIT FUELING]
    """
    payment_id = data.get("id")
    metadata = data.get("metadata") or {}
    internal_tx_id = metadata.get("internal_transaction_id")
    amount_units = data.get("debitAmount", {}).get("value")

    logger.info(f"JIT: Fueling Transaction {internal_tx_id}...")

    try:
        # --- FIX: Find coop by Wallet ID since tenant_id is None ---
        coop = await _get_coop_from_event_data(data)
        if not coop:
            raise Exception(
                f"fsp not found for wallet {data.get('walletAddressId')}"
            )

        meta = coop["rafiki_metadata"]
        tenant_id = meta["tenant_id"]
        asset_id = meta["asset_id"]
        secret = meta.get("tenants_secret") or meta.get("tenants_secrect")

        # # 1. MINT THE MONEY
        # await liquidity_mgmt_service.fund_asset_liquidity(asset_id, int(amount_units))

        # 2. SETTLE THE PAYMENT
        await liquidity_mgmt_service.fund_outgoing_payment(
            payment_id, tenant_id, secret
        )

        logger.info(f"JIT: Settlement triggered for {payment_id}")

    except Exception as e:
        logger.error(f"❌ JIT: Fueling failed for {payment_id}: {e}")


async def handle_outgoing_completed(data: dict):
    metadata = data.get("metadata") or {}
    internal_id = metadata.get("internal_transaction_id")
    tx_type = metadata.get("transaction_type")
    payment_id = data.get("id")

    if data.get("state") != "COMPLETED":
        return

    try:
        if tx_type == "MEMBER":
            logger.info(f"Finalizing Member Transaction {internal_id}")
            await db_adapter.update_member_transaction_status(
                tx_id=str(internal_id), status="COMPLETED", payment_id=payment_id
            )
        else:
            logger.info(f"Finalizing fsp Transaction {internal_id}")
            await db_adapter.update_transaction_status(
                tx_id=str(internal_id), status="COMPLETED", rafiki_payment_id=payment_id
            )
    except Exception as e:
        logger.error(f"❌ Webhook DB Update failed: {e}")


async def handle_incoming_completed(data: dict, event_tenant_id: str = None):
    """
    [RECEIVER RELEASE]
    Fired when money arrives at an Incoming Payment (invoice).
    This function releases the 'trapped' money into the tenant's spendable asset pool.
    """
    payment_id = data.get("id")
    wallet_id = data.get("walletAddressId")

    # 1. Extract metadata to understand the context
    metadata = data.get("metadata") or {}
    tx_type = metadata.get(
        "transaction_type", "COOP"
    )  # Default to COOP if flag missing
    internal_tx_id = metadata.get("internal_transaction_id")

    logger.info(f"Money arrived for {tx_type} | Internal ID: {internal_tx_id}")
    logger.info(f"Target Wallet: {wallet_id}")

    try:
        # 2. Find the fsp that owns this wallet
        # We need their tenant_id and secret to authorize the withdrawal
        coop = await _get_coop_from_event_data(data)

        if not coop:
            logger.error(
                f"Webhook Error: No fsp found for Wallet {wallet_id}"
            )
            return

        meta = coop.get("rafiki_metadata") or {}
        tenant_id = meta.get("tenant_id")
        # Handle Team C typo 'secrect' if it still exists in your DB
        secret = meta.get("tenants_secret") or meta.get("tenants_secrect")

        if not tenant_id or not secret:
            logger.error(
                f"❌ Webhook Error: Missing Rafiki credentials for Coop {coop.get('id')}"
            )
            return

        # 3. TRIGGER WITHDRAWAL: Moves money from 'Payment Object' -> 'Asset Pool'
        logger.info(f"Releasing funds from Incoming Payment {payment_id}...")

        success = await liquidity_mgmt_service.withdraw_incoming_payment(
            incoming_payment_id=payment_id,
            tenant_id=tenant_id,
            secret=secret,
        )

        if success:
            logger.info(
                f"Liquidity successfully released to {coop.get('fsp_name')}'s pool."
            )

            # 4. Optional: Action based on Type
            if tx_type == "MEMBER":
                # This is where you would trigger a push notification to a member's phone
                logger.info(
                    f"Logic: Notifying Member about incoming payment {internal_tx_id}"
                )
            else:
                logger.info(f"Logic: Notifying fsp Admin about settlement")

    except Exception as e:
        # Handle the case where the withdrawal was already processed by a previous script/event
        if "already exists" in str(e).lower() or "conflict" in str(e).lower():
            logger.info(
                f"Funds for payment {payment_id} were already released. Skipping."
            )
        else:
            logger.error(f"❌ Critical Failure during Receiver Release: {str(e)}")


async def handle_outgoing_failed(data: dict):
    """
    Fired when a payment fails in Rafiki.
    """
    payment_id = data.get("id")
    metadata = data.get("metadata") or {}
    internal_tx_id = metadata.get("internal_transaction_id")
    error_msg = data.get("error", "Unknown Rafiki Error")

    logger.error(f"Rafiki Payment {payment_id} FAILED: {error_msg}")

    if internal_tx_id:
        # Mark as FAILED in Team C Database so the polling script stops
        await db_adapter.update_transaction_status(
            tx_id=str(internal_tx_id), status="FAILED", rafiki_payment_id=payment_id
        )
