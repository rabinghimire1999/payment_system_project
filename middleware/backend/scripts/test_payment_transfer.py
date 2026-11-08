import asyncio
import logging
from backend.services.payments.incoming_payment import IncomingPaymentService
from backend.services.payments.quote import QuoteService
from backend.services.payments.outgoing_payment import OutgoingPaymentService
from backend.services.payments.liquidity_management import liquidity_mgmt_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_manual_service_flow():
    incoming_svc = IncomingPaymentService()
    quote_svc = QuoteService()
    outgoing_svc = OutgoingPaymentService()

    sender_data = {
        "tenant_id": "c0b43151-c74b-4790-9bed-6a5c62470e88",
        "secret": "csQgHEcLRHiJ8qEmIdveQMOuKLT0DQAJYTuXLDVQ4Xw=",
        "wallet_id": "09276df5-108f-4473-b77e-909412f03bcd",
        "wallet_url": "https://rafiki-backend.testnet.test/idea-coop-1780814677",
        "code": "NPR", "scale": 2
    }

    receiver_data = {
        "tenant_id": "34b2b856-0b0a-46e5-9cb6-31c715634367",
        "secret": "vzQ3Zs4jIH3BxMezEQbnFMWIJjamxBwfO3Ez5jpAHqs=",
        "wallet_id": "853e9900-36fa-41f6-868d-5c1ff2f56357",
        "wallet_url": "https://rafiki-backend.testnet.test/idea-coop-1780814699"
    }

    amount_units = 150 

    try:
        print("🚀 STARTING MANUAL SERVICE-BY-SERVICE TEST")

        print("Step 1: Calling IncomingPaymentService...")
        inc_id = await incoming_svc.create(
            tenant_id=receiver_data["tenant_id"],
            secret=receiver_data["secret"],
            wallet_id=receiver_data["wallet_id"],
            amount=amount_units,
            code=sender_data["code"],
            scale=sender_data["scale"]
        )
        receiver_url = f"{receiver_data['wallet_url']}/incoming-payments/{inc_id}"
        print(f"✅ Created: {receiver_url}")

        print("Step 2: Calling QuoteService...")
        quote_id = await quote_svc.create(
            tenant_id=sender_data["tenant_id"],
            secret=sender_data["secret"],
            wallet_id=sender_data["wallet_id"],
            receiver_url=receiver_url
        )
        print(f"✅ Quote ID: {quote_id}")

        print("Step 3: Calling OutgoingPaymentService...")
        pay_id = await outgoing_svc.create(
            tenant_id=sender_data["tenant_id"],
            secret=sender_data["secret"],
            wallet_id=sender_data["wallet_id"],
            quote_id=quote_id
        )
        print(f"✅ Payment Created: {pay_id}")

        print("Waiting for indexing...")
        await asyncio.sleep(1)
        print("Step 4: Calling LiquidityManagementService...")
        await liquidity_mgmt_service.fund_outgoing_payment(
            payment_id=pay_id,
            tenant_id=sender_data["tenant_id"],
            secret=sender_data["secret"]
        )
        print("SETTLEMENT TRIGGERED!")
        print("\n FULL VERIFIED")

    except Exception as e:
        print(f" TEST FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_manual_service_flow())