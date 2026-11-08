import logging
from backend.services.wallet.enrollment_manager import EnrollmentManager
from backend.services.payments.funding_manager import funding_manager
from fastapi import HTTPException
import json

logger = logging.getLogger(__name__)


class WalletService:
    def __init__(self):
        self.manager = EnrollmentManager()

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

    async def wallet_create(self, payload):
        """
        STEP 3: Takes the ID and creates the Rafiki Wallet + Asset.
        """
        data = payload.model_dump(mode="json")
        fsp_id = data.get("fsp_id")

        try:
            result = await self.manager.activate_fsp_wallet(fsp_id)

            return {
                "status": "success",
                "message": "Asset and Wallet created successfully",
                "wallet_url": result["wallet_url"],
            }
        except Exception as e:
            logger.error(f"❌ Wallet Activation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))

    async def wallet_load(self, payload):
        """
        ENTRY POINT: Loads liquidity into the wallet.
        """
        data = payload.model_dump(mode="json")
        coop_id = data.get("fsp_id")
        ac_num = data.get("account_number")
        amount_npr = data.get("amount")

        logger.info(f"Entry Point: Requesting load for Coop {coop_id} (AC: {ac_num})")

        try:
            result = await funding_manager.deposit_funds(
                fsp_id=coop_id, account_number=ac_num, amount=amount_npr
            )

            return {
                "status": "success",
                "message": f"Successfully funded {amount_npr} NPR",
                "data": {
                    "fsp": result["fsp_name"],
                    "current_balance": result["new_db_balance"],
                },
            }
        except Exception as e:
            logger.error(f"❌ Wallet Load failed: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))
