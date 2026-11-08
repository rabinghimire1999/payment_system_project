import asyncio
import time
from backend.services.wallet.tenant import TenantService
from backend.services.wallet.asset import AssetService
from backend.services.wallet.wallet import WalletService

async def test_full_enrollment_chain():
    tenant_service = TenantService()
    asset_service = AssetService()
    wallet_service = WalletService()
    
    # Unique details for this test run
    unique_suffix = int(time.time())
    coop_name = f"Idea Coop {unique_suffix}"
    coop_email = f"admin_{unique_suffix}@ideacoop.com"
    
    print(f"🚀 Starting FULL Enrollment for: {coop_name}")
    
    try:
        # STEP 1: Create Tenant
        print("Creating Tenant...")
        tenant_res = await tenant_service.create_tenant(
            name=coop_name, 
            email=coop_email
        )
        t_id = tenant_res['tenant_id']
        t_secret = tenant_res['api_secret']
        print(f"   ✅ Tenant Created: {t_id}")

        # STEP 2: Create Asset (NPR) for this Tenant
        print("Creating NPR Asset...")
        asset_res = await asset_service.create_npr_asset(tenant_id=t_id)
        a_id = asset_res['id']
        print(f"   ✅ Asset Created: {a_id}")

        # STEP 3: Create Wallet Address
        print("Creating Wallet Address...")
        wallet_res = await wallet_service.create_wallet(
            tenant_id=t_id, 
            asset_id=a_id, 
            public_name=coop_name
        )
        w_url = wallet_res['url']
        w_id = wallet_res['id']
        print(f"   ✅ Wallet URL: {w_url}")

        print("🎉 Wallet Creation SUCCESSFUL!")
        print(f"Final Data for Team C (Database):")
        print(f"Name:           {coop_name}")
        print(f"Tenant ID:      {t_id}")
        print(f"Tenant Secret:  {t_secret}")
        print(f"Asset ID:       {a_id}")
        print(f"Wallet URL:     {w_url}")
        print(f"Wallet ID:      {w_id}")
        print("-" * 40)

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_full_enrollment_chain())