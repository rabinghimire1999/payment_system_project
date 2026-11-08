import asyncio
import logging
import sys
from backend.services.payments.funding_manager import funding_manager

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test_integrated_funding():
    COOP_DB_ID = "3" 
    AMOUNT_NPR = 500.00 

    print(f"\nFunding {AMOUNT_NPR} NPR to Coop ID: {COOP_DB_ID}")

    try:
        result = await funding_manager.deposit_funds(
            fsp_id=COOP_DB_ID, 
            amount=AMOUNT_NPR
        )

        print("INTEGRATED FUNDING SUCCESSFUL")
        print(f"fsp : {result['fsp_name']}")
        print(f"Amount Added: {result['amount_funded_npr']} NPR")
        print(f"DB Balance  : {result['new_db_balance']} NPR")
        print("="*50)

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_integrated_funding())