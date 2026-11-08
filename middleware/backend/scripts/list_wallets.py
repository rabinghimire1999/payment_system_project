import asyncio
import json
from backend.infrastructure.rafiki_client import rafiki_client

QUERY_WALLETS = """
query {
  walletAddresses {
    nodes {
      id
      address
      publicName
    }
  }
}
"""

async def list_all():
    print("🔍 Fetching all Wallet Addresses from Rafiki...")
    try:
        res = await rafiki_client.execute(query=QUERY_WALLETS)
        nodes = res.get("walletAddresses", {}).get("nodes", [])
        
        if not nodes:
            print("📭 No wallets found. You need to run enrollment!")
            return

        for node in nodes:
            print(f"ID: {node['id']} | Address: {node['address']} | Name: {node['publicName']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_all())