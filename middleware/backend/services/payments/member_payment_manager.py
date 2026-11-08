import logging
import asyncio
from backend.services.payments.incoming_payment import IncomingPaymentService
from backend.services.payments.quote import QuoteService
from backend.services.payments.outgoing_payment import OutgoingPaymentService
from backend.services.payments.liquidity_management import liquidity_mgmt_service
from backend.infrastructure.db_adapter import db_adapter
from backend.infrastructure.fsp_adapter import coop_adapter

logger = logging.getLogger(__name__)


class MemberPaymentManager:
    def __init__(self):
        self.incoming_service = IncomingPaymentService()
        self.quote_service = QuoteService()
        self.outgoing_service = OutgoingPaymentService()

    async def execute_member_transfer(
        self, sender_member_id: str, receiver_member_id: str, amount: float
    ):
        # 1. Fetch Member Data
        sender_res = await db_adapter.get_member(sender_member_id)
        receiver_res = await db_adapter.get_member(receiver_member_id)
        sender_member = sender_res.get("data")
        receiver_member = receiver_res.get("data")

        # 2. Fetch Parent Coop Data
        sender_coop = await db_adapter.get_fsp(sender_member["fsp_id"])
        receiver_coop = await db_adapter.get_fsp(
            receiver_member["fsp_id"]
        )
        s_meta = sender_coop.get("rafiki_metadata") or {}
        r_meta = receiver_coop.get("rafiki_metadata") or {}

        s_secret = s_meta.get("tenants_secret") or s_meta.get("tenants_secrect")
        r_secret = r_meta.get("tenants_secret") or r_meta.get("tenants_secrect")

        # 3. Balance Check
        if not await coop_adapter.check_balance(
            sender_member["account_number"], amount
        ):
            raise Exception(
                f"Insufficient funds in member account: {sender_member['name']}"
            )

        # 4. INITIALIZE DB TRANSACTION
        tx_data = {
            "sender_member_id": int(sender_member_id),
            "receiver_member_id": int(receiver_member_id),
            "amount": amount,
            "payment_id": None,
        }
        logger.info("Step 0: Initializing Member Transaction record...")
        tx_res = await db_adapter.create_member_transaction(tx_data)

        # --- THE FIX: Extract nested ID ---
        tx_inner_data = tx_res.get("data", {})
        internal_tx_id = tx_inner_data.get("id")

        if not internal_tx_id:
            raise Exception(
                f"Database did not return a valid transaction ID. Response: {tx_res}"
            )

        try:
            # --- RAFIKI ORCHESTRATION ---
            scale = s_meta.get("asset_scale", 2)
            raw_amount_units = int(amount * (10**scale))

            # Step 1: Incoming
            inc_id = await self.incoming_service.create(
                tenant_id=r_meta["tenant_id"],
                secret=r_secret,
                wallet_id=receiver_member["wallet_address_id"],
                amount=raw_amount_units,
                code=s_meta["asset_code"],
                scale=scale,
                internal_tx_id=str(internal_tx_id),
                tx_type="MEMBER",
            )
            receiver_url = (
                f"{receiver_member['wallet_address']}/incoming-payments/{inc_id}"
            )

            # Step 2: Quote
            quote = await self.quote_service.create(
                tenant_id=s_meta["tenant_id"],
                secret=s_secret,
                wallet_id=sender_member["wallet_address_id"],
                receiver_url=receiver_url,
            )

            # Step 3: Outgoing
            payment_id = await self.outgoing_service.create(
                tenant_id=s_meta["tenant_id"],
                secret=s_secret,
                wallet_id=sender_member["wallet_address_id"],
                quote_id=quote["id"],
                internal_tx_id=str(internal_tx_id),
                tx_type="MEMBER",
            )

            await asyncio.sleep(1.5)

            # Step 4: Final Settlement
            await liquidity_mgmt_service.fund_outgoing_payment(
                payment_id=payment_id, tenant_id=s_meta["tenant_id"], secret=s_secret
            )

            # --- CONCLUSION ---
            await db_adapter.update_member_transaction_status(
                tx_id=internal_tx_id, status="pending", payment_id=payment_id
            )

            return {
                "success": True,
                "transaction_id": internal_tx_id,
                "payment_id": payment_id,
            }

        except Exception as e:
            logger.error(f"❌ Member Transfer failed: {str(e)}")
            # Only attempt to update status if we successfully created the record
            if internal_tx_id:
                await db_adapter.update_member_transaction_status(
                    tx_id=internal_tx_id, status="FAILED", payment_id=""
                )
            raise e
