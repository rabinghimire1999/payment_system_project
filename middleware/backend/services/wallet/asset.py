from typing import Dict
from backend.infrastructure.rafiki_client import rafiki_client

# Fixed: Removed the fields that were causing the 400 error
CREATE_ASSET = """
mutation CreateAsset($input: CreateAssetInput!) {
  createAsset(input: $input) {
    asset {
      id
      code
      scale
      tenantId
    }
  }
}
"""


class AssetService:
    async def create_npr_asset(self, tenant_id: str, tenant_secret: str) -> Dict:
        """
        Creates an NPR asset.
        FIX: Added tenant_secret and passed it to the execute method.
        """
        variables = {"input": {"tenantId": tenant_id, "code": "NPR", "scale": 2}}

        # IMPORTANT: We must pass tenant_id and secret to the client
        # so it can build the correct x-tenant-id header and signature.
        response = await rafiki_client.execute(
            query=CREATE_ASSET,
            variables=variables,
            tenant_id=tenant_id,
            secret=tenant_secret,
        )

        return response["createAsset"]["asset"]
