from backend.infrastructure.rafiki_client import rafiki_client
from typing import Dict, Any

CREATE_QUOTE = """
mutation CreateQuote($input: CreateQuoteInput!) {
  createQuote(input: $input) {
    quote { 
      id 
      receiver
      debitAmount {
        value
        assetCode
        assetScale
      }
      receiveAmount {
        value
        assetCode
        assetScale
      }
    }
  }
}
"""


class QuoteService:
    async def create(
        self, tenant_id: str, secret: str, wallet_id: str, receiver_url: str
    ) -> Dict[str, Any]:
        """
        Creates a Quote (The Handshake).
        This calculates the path and fees between the Sender and the Receiver's Invoice.
        """
        variables = {"input": {"walletAddressId": wallet_id, "receiver": receiver_url}}

        res = await rafiki_client.execute(
            query=CREATE_QUOTE, variables=variables, tenant_id=tenant_id, secret=secret
        )

        quote_data = res.get("createQuote", {}).get("quote")
        if not quote_data:
            raise Exception("Failed to retrieve quote object from Rafiki")

        return quote_data
