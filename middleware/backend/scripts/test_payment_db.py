import asyncio
import logging
import sys
from backend.services.payments.payment_manager import PaymentManager
from backend.infrastructure.db_adapter import db_adapter

# Set up clean logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def test_database_level_transfer():
    orchestrator = PaymentManager()

    SENDER_DB_ID = "101" 
    RECEIVER_DB_ID = "102"
    TRANSFER_AMOUNT = 50.00

    print("\n" + "="*60)
    print(f"🚀 STARTING DATABASE-INTEGRATED TRANSFER TEST")
    print(f"Sender ID   : {SENDER_DB_ID}")
    print(f"Receiver ID : {RECEIVER_DB_ID}")
    print(f"Amount      : {TRANSFER_AMOUNT} NPR")
    print("="*60 + "\n")

    try:
        logger.info("Triggering PaymentManager...")
        result = await orchestrator.execute_transfer(
            sender_id=SENDER_DB_ID,
            receiver_id=RECEIVER_DB_ID,
            amount=TRANSFER_AMOUNT
        )

        print("DATABASE TRANSFER SUCCESSFUL")
        print(f"Transaction ID: {result['transaction_id']}")
        print(f"Final Status:   {result['status']}")
        
        logger.info("Verifying updated balances in Database...")
        s_bal = await db_adapter.get_balance(SENDER_DB_ID)
        r_bal = await db_adapter.get_balance(RECEIVER_DB_ID)
        
        print(f"\nFinal Shadow Ledger State:")
        # FIX: Changed 'balance' to 'amount'
        print(f"  - Sender Balance   : {s_bal.get('balance')} NPR")
        print(f"  - Receiver Balance : {r_bal.get('balance')} NPR")
        print("="*60)

    except Exception as e:
        print("DATABASE TRANSFER FAILED")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_database_level_transfer())