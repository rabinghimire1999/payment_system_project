import asyncio
import time
import random
import logging
import sys
from backend.services.wallet.enrollment_manager import EnrollmentManager

# Set up logging to track orchestration steps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def test_stepped_orchestration():
    manager = EnrollmentManager()
    
    # 1. GENERATE FULL KYC DATA (Matching Team C's Database Schema)
    timestamp = int(time.time())
    kyc_payload = {
        "name": f"ipg Coop {timestamp}",
        "registration_number": f"REG{timestamp}",
        "pan_number": str(random.randint(100000000, 999999999)),
        "registration_authority": "Department of fsps",
        "registration_date": "2026-06-10",
        "fsp_type": "SAVING",
        "fsp_code": f"C-{random.randint(100, 999)}",
        "email": f"admin_{timestamp}@gmail.com"
    }

    print("\n" + "="*60)
    print(f"🚀 STARTING STEPPED ENROLLMENT TEST")
    print(f"Coop Name : {kyc_payload['name']}")
    print(f"PAN Number: {kyc_payload['pan_number']}")
    print("="*60 + "\n")

    try:
        # --- PHASE 1: ENROLLMENT (DB Record + Rafiki Tenant) ---
        print("1️⃣  Running Phase 1: Enrollment & Tenant Creation...")
        enroll_res = await manager.enroll_fsp(kyc_payload)
        
        db_id = enroll_res["id"]
        print(f"   ✅ DB Record Created with ID: {db_id}")
        print(f"   ✅ Rafiki Tenant generated and stored.")

        # Give the DB and Rafiki a moment to breathe
        await asyncio.sleep(1)

        # --- PHASE 2: ACTIVATION (Rafiki Asset + Wallet Address) ---
        print("\n2️⃣  Running Phase 2: Wallet Activation...")
        activate_res = await manager.activate_fsp_wallet(str(db_id))

        # --- FINAL RESULTS ---
        print("STEPPED ORCHESTRATION SUCCESSFUL")
        print(f"Database Internal ID: {db_id}")
        print(f"Final Status        : {activate_res.get('status')}")
        print(f"Rafiki Wallet URL   : {activate_res.get('wallet_url')}")
        print("="*60)
        print("The fsp is now fully activated and ready for funding.")

    except Exception as e:
        print("TEST FAILED")
        print(f"Error Detail: {str(e)}")
        logger.error("Traceback follows:", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_stepped_orchestration())