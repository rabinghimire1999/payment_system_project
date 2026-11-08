import asyncio
import logging
import sys
from backend.services.payments.member_payment_manager import MemberPaymentManager
from backend.infrastructure.db_adapter import db_adapter

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def test_member_transfer():
    manager = MemberPaymentManager()

    # --- SETUP: Use real IDs from your Database ---
    # Member X from Coop A
    SENDER_MEMBER_ID = "11"
    # Member Y from Coop B
    RECEIVER_MEMBER_ID = "12"

    AMOUNT = 5.00  # 5.00 NPR

    print("\n" + "=" * 60)
    print(f"🚀 STARTING MEMBER-TO-MEMBER TRANSFER TEST")
    print(f"Sender Member ID   : {SENDER_MEMBER_ID}")
    print(f"Receiver Member ID : {RECEIVER_MEMBER_ID}")
    print(f"Amount             : {AMOUNT} NPR")
    print("=" * 60 + "\n")

    try:
        # Trigger the orchestration
        result = await manager.execute_member_transfer(
            sender_member_id=SENDER_MEMBER_ID,
            receiver_member_id=RECEIVER_MEMBER_ID,
            amount=AMOUNT,
        )

        print(" INITIATION SUCCESSFUL ")
        print(f"Internal Tx ID: {result['transaction_id']}")
        print(f"Rafiki Pay ID : {result['payment_id']}")
        print("\nNow wait for the Webhook to finalize the status...")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_member_transfer())
