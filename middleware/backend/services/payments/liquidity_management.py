import uuid
import logging
from typing import Dict, Any
from backend.infrastructure.rafiki_client import rafiki_client

logger = logging.getLogger(__name__)

# 1. NEW: To "Fuel" the fsp's NPR bucket (JIT Mode)
DEPOSIT_ASSET_LIQUIDITY = """
mutation DepositAssetLiquidity($input: DepositAssetLiquidityInput!) {
  depositAssetLiquidity(input: $input) {
    success
  }
}
"""

# 2. To move money from the bucket to the specific payment
DEPOSIT_OUTGOING_PAYMENT_LIQUIDITY = """
mutation DepositOutgoingPaymentLiquidity($input: DepositOutgoingPaymentLiquidityInput!) {
  depositOutgoingPaymentLiquidity(input: $input) {
    success
  }
}
"""

# 3. To release received money into the receiver's bucket
CREATE_INCOMING_PAYMENT_WITHDRAWAL = """
mutation CreateIncomingPaymentWithdrawal($input: CreateIncomingPaymentWithdrawalInput!) {
  createIncomingPaymentWithdrawal(input: $input) {
    success
  }
}
"""


class LiquidityManagementService:

    # --- STEP A: FUEL THE ASSET ---
    async def fund_asset_liquidity(self, asset_id: str, amount_units: int) -> bool:
        """
        [OPERATOR ACTION] Adds 'fuel' to the fsp's NPR asset pool.
        This is called first in the JIT model.
        """
        variables = {
            "input": {
                "assetId": asset_id,
                "amount": str(amount_units),
                "id": str(uuid.uuid4()),
                "idempotencyKey": str(uuid.uuid4()),
            }
        }
        logger.info(f"JIT: Fueling Asset {asset_id} with {amount_units} units")

        # No tenant_id/secret passed: signed by Operator
        response = await rafiki_client.execute(
            query=DEPOSIT_ASSET_LIQUIDITY, variables=variables
        )
        return response.get("depositAssetLiquidity", {}).get("success", False)

    # --- STEP B: SETTLE THE PAYMENT ---
    async def fund_outgoing_payment(
        self, payment_id: str, tenant_id: str, secret: str
    ) -> bool:
        """
        [TENANT ACTION] Moves funds from the 'fueled' pool into the payment object.
        """
        variables = {
            "input": {
                "outgoingPaymentId": payment_id,
                "idempotencyKey": str(uuid.uuid4()),
            }
        }
        logger.info(f"JIT: Settling Payment {payment_id} for Tenant {tenant_id}")

        response = await rafiki_client.execute(
            query=DEPOSIT_OUTGOING_PAYMENT_LIQUIDITY,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )
        return response.get("depositOutgoingPaymentLiquidity", {}).get("success", False)

    # --- STEP C: RELEASE TO RECEIVER ---
    async def withdraw_incoming_payment(
        self, incoming_payment_id: str, tenant_id: str, secret: str
    ) -> bool:
        """
        [TENANT ACTION] Releases received funds into the receiver's spendable pool.
        """
        variables = {
            "input": {
                "incomingPaymentId": incoming_payment_id,
                "idempotencyKey": str(uuid.uuid4()),
                "timeoutSeconds": "60",
            }
        }
        logger.info(
            f"JIT: Releasing Incoming Payment {incoming_payment_id} for Receiver {tenant_id}"
        )

        response = await rafiki_client.execute(
            query=CREATE_INCOMING_PAYMENT_WITHDRAWAL,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )
        return response.get("createIncomingPaymentWithdrawal", {}).get("success", False)


liquidity_mgmt_service = LiquidityManagementService()
