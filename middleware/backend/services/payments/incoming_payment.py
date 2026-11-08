from backend.infrastructure.rafiki_client import rafiki_client

CREATE_INCOMING_PAYMENT = """
mutation CreateIncomingPayment ($input: CreateIncomingPaymentInput!) {
    createIncomingPayment(input: $input) {
    payment { 
      id 
      walletAddressId
    }
  }
}
"""


class IncomingPaymentService:
    async def create(
        self,
        tenant_id: str,
        secret: str,
        wallet_id: str,
        amount: int,
        code: str,
        scale: int,
        internal_tx_id: str,
        tx_type: str = "COOP",
    ) -> str:
        """
        Creates an invoice (Incoming Payment) for the receiver.
        Adds metadata to link back to our internal transaction.
        """
        variables = {
            "input": {
                "walletAddressId": wallet_id,
                "incomingAmount": {
                    "value": str(amount),
                    "assetCode": code,
                    "assetScale": scale,
                },
                "metadata": {
                    "internal_transaction_id": internal_tx_id,
                    "transaction_type": tx_type,  # <--- ADDED FLAG
                    "description": f"Transfer to {wallet_id}",
                },
            }
        }

        response = await rafiki_client.execute(
            query=CREATE_INCOMING_PAYMENT,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )

        return response["createIncomingPayment"]["payment"]["id"]
