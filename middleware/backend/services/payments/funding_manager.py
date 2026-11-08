import logging
from backend.services.wallet.liquidity import liquidity_service  
from backend.infrastructure.db_adapter import db_adapter

logger = logging.getLogger(__name__)

class FundingManager:
    async def deposit_funds(self, fsp_id: str, amount: float, account_number: str):
        """
        Orchestrates funding.
        Rafiki receives: amount * 10^scale (e.g., 50000)
        Database receives: amount (e.g., 500.00)
        """
        logger.info(f"🚀 Starting integrated funding for Coop ID: {fsp_id}")

        # 1. FETCH COOP METADATA
        coop = await db_adapter.get_fsp(fsp_id)
        meta = coop.get("rafiki_metadata", {})
        asset_id = meta.get("asset_id")
        scale = meta.get("asset_scale", 2) # Usually 2 for NPR

        if not asset_id:
            raise Exception(f"Asset ID missing for fsp {fsp_id}")

        # --- THE MATH SECTION ---
        # For Rafiki: 500.00 becomes 50000 (Smallest unit/Paisa)
        rafiki_units = int(amount * (10 ** scale))
        
        # For Database: 500.00 stays 500.00
        db_amount = amount 

        try:
            # Step 1: Fund Rafiki with Units
            logger.info(f"Step 1: Funding Rafiki Asset {asset_id} with {rafiki_units} units")
            await liquidity_service.fund_asset(
                asset_id=asset_id, 
                amount=rafiki_units # Send 50000 to Rafiki
            )

            # Step 2: Update DB balance with Decimal
            logger.info(f"Step 2: Updating DB balance for Coop {fsp_id} with {db_amount} NPR")
            db_res = await db_adapter.update_balance(
                coop_id=fsp_id,
                amount=db_amount, # Send 500.00 to Team C
                entry_type="LIQUIDITY DEPOSIT"
            )

            return {
                "success": True,
                "fsp_name": coop.get("fsp_name"),
                "new_db_balance": db_res.get("balance"), # Team C returns the new balance
                "amount_funded_npr": db_amount
            }

        except Exception as e:
            logger.error(f"❌ Integrated funding failed: {str(e)}")
            raise e

funding_manager = FundingManager()