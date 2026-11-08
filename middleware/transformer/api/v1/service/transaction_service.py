import logging
from typing import Dict, Any
import json
from fastapi import HTTPException
from backend.services.payments.payment_manager import PaymentManager
from backend.infrastructure.db_adapter import db_adapter

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self):
        self.payment_manager = PaymentManager()

    def _parse_error(self, e: Exception) -> str:
        """Helper to extract the clean error message from the exception string."""
        error_str = str(e)
        if "Database Service Error:" in error_str:
            try:
                json_part = error_str.split("Database Service Error: ")[1]
                error_json = json.loads(json_part)
                return error_json.get("detail", json_part)
            except:
                return error_str
        return error_str

    # --- 1. Payment Transfer ---
    async def payment_transfer(self, payload) -> Dict[str, Any]:
        """
        ENTRY POINT: Orchestrates a cross-fsp transfer.
        This calls the Brain, which handles Rafiki and Team C's ledger.
        """
        data = payload.model_dump(mode="json")

        sender_id = str(data.get("sender_id"))
        receiver_id = str(data.get("receiver_id"))
        amount = float(data.get("amount"))

        logger.info(
            f"Entry Point: Transfer initiated. {amount} NPR from {sender_id} to {receiver_id}"
        )

        try:
            result = await self.payment_manager.execute_transfer(
                sender_id=sender_id, receiver_id=receiver_id, amount=amount
            )

            return {
                "status": "success",
                "message": "Transfer completed successfully",
                "data": {
                    "transaction_id": result["transaction_id"],
                    "payment_id": result["payment_id"],
                    "internal_status": result["status"],
                },
            }

        except Exception as e:
            logger.error(f"❌ Transfer failed: {str(e)}")
            # Raise 400 for business logic errors (e.g., Insufficient funds)
            raise HTTPException(status_code=400, detail=self._parse_error(e))

    # --- 2. Payment Status ---
    async def payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        ENTRY POINT: Checks the status of an existing transaction in our DB.
        """
        logger.info(
            f"Entry Point: Checking status for Transaction ID: {transaction_id}"
        )

        try:
            tx = await db_adapter.get_transaction(transaction_id)

            return {
                "status": "success",
                "data": {
                    "transaction_id": transaction_id,
                    "state": tx.get("status"),
                    "amount": tx.get("amount"),
                    "currency": tx.get("currency"),
                    "rafiki_id": tx.get("rafiki_payment_id"),
                },
            }
        except Exception as e:
            logger.error(f"❌ Status check failed for {transaction_id}: {str(e)}")
            raise HTTPException(status_code=404, detail=self._parse_error(e))

    async def get_history(self, fsp_id: str) -> Dict[str, Any]:
        """
        ENTRY POINT: Fetches transaction history.
        Determines if the coop is the sender or receiver using the new nested metadata.
        """
        logger.info(
            f"Entry Point: Fetching detailed history for Coop ID: {fsp_id}"
        )

        try:
            raw_transactions = await db_adapter.get_fsp_transactions(
                fsp_id
            )

            processed_history = []
            for tx in raw_transactions:
                # 1. Access the nested metadata
                sender_meta = tx.get("sender_metadata") or {}
                receiver_meta = tx.get("receiver_metadata") or {}

                # 2. Determine if the user we are looking at is the Sender or Receiver
                # We compare against the ID inside the metadata
                is_sender = str(sender_meta.get("id")) == str(fsp_id)

                # 3. Identify the "Counterparty" (The other fsp)
                # If I am the sender, the counterparty is the receiver (and vice versa)
                cp_meta = receiver_meta if is_sender else sender_meta

                entry = {
                    "transaction_id": tx.get("id"),
                    "date": tx.get("created_at"),
                    "amount": tx.get("amount"),
                    "currency": tx.get("currency"),
                    "status": tx.get("status"),
                    # Dashboard Logic: DEBIT (Money Out) / CREDIT (Money In)
                    "type": "DEBIT" if is_sender else "CREDIT",
                    # Clean data for the Frontend list
                    "counterparty_name": cp_meta.get("fsp_name"),
                    "counterparty_account": cp_meta.get("account_number"),
                    "description": f"{'Sent to' if is_sender else 'Received from'} {cp_meta.get('fsp_name')}",
                    # Technical details (Hidden or shown on 'Click for details')
                    "rafiki_payment_id": tx.get("rafiki_payment_id"),
                    "direction": "OUTGOING" if is_sender else "INCOMING",
                }
                processed_history.append(entry)

            return {
                "status": "success",
                "data": {
                    "fsp_id": fsp_id,
                    "count": len(processed_history),
                    "activity": processed_history,
                },
            }

        except Exception as e:
            logger.error(f"❌ History fetch failed for {fsp_id}: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))
