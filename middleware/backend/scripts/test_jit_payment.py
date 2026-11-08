import asyncio
import logging
import sys
from backend.services.payments.payment_manager import PaymentManager
from backend.infrastructure.db_adapter import db_adapter

# Set up clean logging to see the "Brain" working
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def test_jit_flow():
    orchestrator = PaymentManager()

    SENDER_DB_ID = "140"
    RECEIVER_DB_ID = "141"
    TRANSFER_AMOUNT = 10.00

    print("\n" + "=" * 60)
    print(f"🚀 STARTING AUTOMATED JIT TRANSFER TEST")
    print(f"Sender ID   : {SENDER_DB_ID}")
    print(f"Receiver ID : {RECEIVER_DB_ID}")
    print(f"Amount      : {TRANSFER_AMOUNT} NPR")
    print("=" * 60 + "\n")

    try:
        logger.info("Triggering PaymentManager (Initiation Phase)...")
        init_result = await orchestrator.execute_transfer(
            sender_id=SENDER_DB_ID, receiver_id=RECEIVER_DB_ID, amount=TRANSFER_AMOUNT
        )

        internal_tx_id = init_result["transaction_id"]
        rafiki_id = init_result["payment_id"]

        print(f"\n INITIATION SUCCESSFUL")
        print(f"Internal TX ID: {internal_tx_id}")
        print(f"Rafiki Pay ID : {rafiki_id}")
        print(f"Current Status: {init_result['status']}")
        print("\n Now waiting for Rafiki Webhooks to trigger the Brain...")

        final_db_status = "PENDING"
        for attempt in range(15):
            await asyncio.sleep(2)

            tx_record = await db_adapter.get_transaction(internal_tx_id)
            final_db_status = tx_record.get("status")

            logger.info(f"Checking DB Status (Attempt {attempt+1}): {final_db_status}")

            if final_db_status == "COMPLETED":
                print(" JIT AUTOMATION SUCCESSFUL!")
                print("1. Rafiki created the payment.")
                print("2. Webhook detected the creation.")
                print("3. Brain 'Fueled' the account and settled the move.")
                print("4. DB was updated automatically to COMPLETED.")
                break

            if final_db_status == "FAILED":
                print("\n❌ AUTOMATION FAILED: Transaction marked as FAILED in DB.")
                break

        if final_db_status == "PENDING":
            print("\n TIMEOUT: Webhook was never received or failed to relay.")

        # --- 4. VERIFY FINAL BALANCES ---
        logger.info("Fetching final balances for proof...")
        s_bal = await db_adapter.get_balance(SENDER_DB_ID)
        r_bal = await db_adapter.get_balance(RECEIVER_DB_ID)
        print(
            f"Final Balances -> Sender: {s_bal.get('balance')} | Receiver: {r_bal.get('balance')}"
        )

    except Exception as e:
        print(f"\n❌ SCRIPT ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_jit_flow())
