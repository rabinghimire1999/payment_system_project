import uuid
import logging
from typing import Dict
from backend.infrastructure.rafiki_client import rafiki_client

logger = logging.getLogger(__name__)

DEPOSIT_ASSET_LIQUIDITY = """
mutation DepositAssetLiquidity($input: DepositAssetLiquidityInput!) {
  depositAssetLiquidity(input: $input) {
    success
  }
}
"""


class LiquidityService:
    async def fund_asset(self, asset_id: str, amount: int) -> Dict:
        """
        Deposits liquidity into a Rafiki Asset.
        Requires both 'id' and 'idempotencyKey'.
        """
        # Generate two unique UUIDs
        # 1. The ID for the actual ledger entry
        transfer_id = str(uuid.uuid4())
        # 2. The ID for the API request idempotency
        i_key = str(uuid.uuid4())

        variables = {
            "input": {
                "assetId": asset_id,
                "amount": str(amount),
                "id": transfer_id,
                "idempotencyKey": i_key,
            }
        }

        logger.info(f"Attempting to deposit {amount} units to Asset: {asset_id}")

        response = await rafiki_client.execute(
            query=DEPOSIT_ASSET_LIQUIDITY, variables=variables
        )

        result = response.get("depositAssetLiquidity", {})

        if not result or not result.get("success"):
            raise Exception("Liquidity deposit failed: Rafiki returned success=False")

        logger.info(f"Successfully deposited liquidity. Transfer ID: {transfer_id}")

        return {
            "success": True,
            "transfer_id": transfer_id,
            "idempotency_key": i_key,
            "amount": amount,
        }


# Instantiate the service
liquidity_service = LiquidityService()
