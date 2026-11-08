import logging
import asyncio
from backend.services.payments.incoming_payment import IncomingPaymentService
from backend.services.payments.quote import QuoteService
from backend.services.payments.outgoing_payment import OutgoingPaymentService
from backend.services.payments.liquidity_management import liquidity_mgmt_service
from backend.infrastructure.db_adapter import db_adapter
from backend.infrastructure.fsp_adapter import coop_adapter

logger = logging.getLogger(__name__)


class PaymentManager:
    def __init__(self):
        self.incoming_service = IncomingPaymentService()
        self.quote_service = QuoteService()
        self.outgoing_service = OutgoingPaymentService()

    async def execute_transfer(self, sender_id: str, receiver_id: str, amount: float):
        """
        Orchestrates transfer without checking internal DB balances.
        """
        # 1. Fetch metadata
        sender = await db_adapter.get_fsp(sender_id)
        receiver = await db_adapter.get_fsp(receiver_id)

        if not sender or not receiver:
            raise Exception("fsp records not found.")

        s_meta = sender.get("rafiki_metadata", {})
        r_meta = receiver.get("rafiki_metadata", {})
        s_secret = s_meta.get("tenants_secret") or s_meta.get("tenants_secrect")
        r_secret = r_meta.get("tenants_secret") or r_meta.get("tenants_secrect")

        # --- STEP 1: REAL-WORLD CHECK (The new 'Fuel' logic) ---
        # We verify if the Coop has money in their ACTUAL bank, not our DB.
        if not await coop_adapter.check_balance(sender["account_number"], amount):
            raise Exception(
                f"Denied by fsp Bank: Insufficient funds in {sender['account_number']}"
            )

        scale = s_meta.get("asset_scale", 2)
        raw_amount_units = int(amount * (10**scale))

        # --- STEP 2: CREATE PENDING LOG ---
        # We create the record so we have an ID to track.
        # Team C should just save this without doing a balance check.
        tx_data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "amount": amount,
            "currency": s_meta.get("asset_code", "NPR"),
            "status": "PENDING",
        }
        tx_record = await db_adapter.create_transaction(tx_data)
        internal_tx_id = tx_record["id"]

        try:
            # --- PHASE 1: RAFIKI SETUP ---
            inc_id = await self.incoming_service.create(
                tenant_id=r_meta["tenant_id"],
                secret=r_secret,
                wallet_id=r_meta["wallet_address_id"],
                amount=raw_amount_units,
                code=s_meta["asset_code"],
                scale=scale,
                internal_tx_id=str(internal_tx_id),
                tx_type="COOP",
            )

            receiver_url = f"{r_meta['wallet_address_url']}/incoming-payments/{inc_id}"

            quote = await self.quote_service.create(
                tenant_id=s_meta["tenant_id"],
                secret=s_secret,
                wallet_id=s_meta["wallet_address_id"],
                receiver_url=receiver_url,
            )

            payment_id = await self.outgoing_service.create(
                tenant_id=s_meta["tenant_id"],
                secret=s_secret,
                wallet_id=s_meta["wallet_address_id"],
                quote_id=quote["id"],
                internal_tx_id=str(internal_tx_id),
                tx_type="COOP",
            )

            # Link Payment ID in DB
            await db_adapter.update_transaction_status(
                internal_tx_id, "PENDING", payment_id
            )

            logger.info(
                f"Transfer {internal_tx_id} accepted. Webhook will handle fueling."
            )

            return {
                "success": True,
                "transaction_id": internal_tx_id,
                "payment_id": payment_id,
                "status": "PROCESSING",
                "message": "Transaction accepted and awaiting settlement.",
            }

        except Exception as e:
            logger.error(f"❌ Transfer setup failed: {str(e)}")
            await db_adapter.update_transaction_status(internal_tx_id, "FAILED", "")
            raise e
