from backend.infrastructure.rafiki_client import rafiki_client
from typing import Dict, Any

# Step 3: Creating the payment record
# Added metadata to the return fields for verification
CREATE_OUTGOING_PAYMENT = """
mutation CreateOutgoingPayment($input: CreateOutgoingPaymentInput!) {
  createOutgoingPayment(input: $input) {
    payment { 
      id 
      state 
      metadata
    }
  }
}
"""

# For the Polling/Status check
GET_OUTGOING_PAYMENT = """
query GetOutgoingPayment($id: String!) {
  outgoingPayment(id: $id) {
    id
    state
    error
    metadata
  }
}
"""


class OutgoingPaymentService:
    async def create(
        self,
        tenant_id: str,
        secret: str,
        wallet_id: str,
        quote_id: str,
        internal_tx_id: str,
        tx_type: str = "COOP",
    ) -> str:
        """
        Creates the instruction to send money.
        """
        variables = {
            "input": {
                "walletAddressId": wallet_id,
                "quoteId": quote_id, 
                "metadata": {
                    "internal_transaction_id": internal_tx_id,
                    "transaction_type": tx_type,  
                },
            }
        }

        res = await rafiki_client.execute(
            query=CREATE_OUTGOING_PAYMENT,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )

        payment_data = res.get("createOutgoingPayment", {}).get("payment")
        if not payment_data:
            raise Exception("Failed to retrieve payment object from Rafiki")

        return payment_data["id"]

    async def get_status(
        self, payment_id: str, tenant_id: str, secret: str
    ) -> Dict[str, Any]:
        """
        Used for manual status verification or background polling.
        """
        variables = {"id": payment_id}

        res = await rafiki_client.execute(
            query=GET_OUTGOING_PAYMENT,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )
        return res["outgoingPayment"]
