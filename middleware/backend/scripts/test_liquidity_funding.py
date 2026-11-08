import asyncio
from backend.services.wallet.liquidity import LiquidityService

async def test_funding():
    service = LiquidityService()
    
    # Use the same Asset ID from your successful enrollment
    TARGET_ASSET_ID = "db730412-5d71-4f2f-bcad-37ec9c4682b8" 
    
    # Let's fund 500 units
    AMOUNT_TO_FUND = 5000000

    print(f"🚀 Starting Liquidity Funding for Asset: {TARGET_ASSET_ID}...")
    
    try:
        result = await service.fund_asset(
            asset_id=TARGET_ASSET_ID, 
            amount=AMOUNT_TO_FUND
        )
        
        print("\nFUNDING SUCCESSFUL!")
        print("-" * 40)
        print(f"Status Code: SUCCESS")
        print(f"Transfer ID: {result['transfer_id']}")
        print(f"Asset ID:    {TARGET_ASSET_ID}")
        print(f"Amount:      {result['amount']} (Units)")
        print("-" * 40)
        print("The fsp now has liquidity to perform transfers.")

    except Exception as e:
        print(f"❌ FUNDING FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_funding())