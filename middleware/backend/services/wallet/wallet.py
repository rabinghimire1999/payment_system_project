# backend/services/wallet/wallet.py

import re
from typing import Dict, Optional  # Added Optional
from backend.infrastructure.rafiki_client import rafiki_client
from backend.core.config import settings

CREATE_WALLET_ADDRESS = """
mutation CreateWalletAddress($input: CreateWalletAddressInput!) {
  createWalletAddress(input: $input) {
    walletAddress {
      id
    }
  }
}
"""


class WalletService:
    def _generate_slug(self, name: str) -> str:
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "-", slug)
        return slug

    async def create_wallet(
        self,
        tenant_id: str,
        asset_id: str,
        public_name: str,
        address: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> Dict:
        # If no address is provided, fallback to default (older coops)
        if not address:
            slug = self._generate_slug(public_name)
            address = f"{settings.RAFIKI_WALLET_BASE_URL.rstrip('/')}/{slug}"

        variables = {
            "input": {
                "tenantId": tenant_id,
                "assetId": asset_id,
                "publicName": public_name,
                "address": address,  # Uses the prefix-based address
            }
        }

        # Execute with the tenant's secret
        response = await rafiki_client.execute(
            query=CREATE_WALLET_ADDRESS,
            variables=variables,
            tenant_id=tenant_id,
            secret=secret,
        )

        wallet_data = response.get("createWalletAddress", {}).get("walletAddress")
        if not wallet_data:
            raise Exception(f"Wallet Address creation failed. Response: {response}")

        return {
            "id": wallet_data["id"],
            "url": address,
        }
