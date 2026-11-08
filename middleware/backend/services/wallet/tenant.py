# services/tenant.py

import secrets
from typing import Dict
from backend.infrastructure.rafiki_client import RafikiClient
from backend.core.config import settings
import base64

rafiki_client = RafikiClient()

CREATE_TENANT = """
mutation CreateTenant($input: CreateTenantInput!) {
  createTenant(input: $input) {
    tenant {
      id
      publicName
      email
    }
  }
}
"""

SET_WALLET_ADDRESS_URL = """ 
mutation CreateTenantSettings($value: String!) { 
  createTenantSettings(input: { 
    settings: [{ key: WALLET_ADDRESS_URL, value: $value }] 
  }) { 
    settings { key value } 
  } 
} 
""" 


class TenantService: 
    def generate_api_secret(self) -> str: 
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8') 
    async def create_tenant(self, name: str, email: str) -> Dict: 
        api_secret = self.generate_api_secret() 
        variables = {'input': { 
            'email': email, 'publicName': name, 'apiSecret': api_secret 
        }} 
        response = await rafiki_client.execute( 
            query=CREATE_TENANT, variables=variables 
        ) 
        tenant_data = response['createTenant']['tenant'] 
        return { 
            'tenant_id': tenant_data['id'], 
            'name': tenant_data['publicName'], 
            'email': tenant_data['email'], 
            'api_secret': api_secret 
        } 

    async def set_wallet_address_url(self, tenant_id: str, 
        tenant_secret: str, base_url: str): 
        await rafiki_client.execute( 
            query=SET_WALLET_ADDRESS_URL, 
            variables={'value': base_url}, 
            tenant_id=tenant_id, 
            secret=tenant_secret 
        )