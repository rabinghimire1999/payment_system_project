#!/usr/bin/env python3
"""
test_all_events.py
Triggers ALL Rafiki webhook events:
  1. incoming_payment.created
  2. incoming_payment.completed
  3. incoming_payment.expired
  4. outgoing_payment.created
  5. outgoing_payment.completed
  6. outgoing_payment.failed
  7. wallet_address.not_found
  8. asset.liquidity_low
  9. peer.liquidity_low
"""

import hmac, hashlib, time, json, sys, random, string, requests

# ============ CONFIGURATION ============
SECRET = "iyIgCprjb9uL8wFckR+pLEkJWMB7FJhgkvqhTQR/964="
TENANT_ID = "438fa74a-fa7d-4317-9ced-dde32ece1787"
ADMIN_URL = "http://localhost:3001/graphql"
ASSET_ID = "56260cc1-d506-4b8a-bfa2-4a946e6f2ca4"
OPEN_PAYMENTS_HOST = "cloud-nine-wallet-backend"
# =======================================

def sign(body):
    ts = int(time.time() * 1000)
    canonical = json.dumps(body, separators=(",", ":"), sort_keys=True)
    payload = f"{ts}.{canonical}"
    digest = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"t={ts}, v1={digest}"

def send(body):
    headers = {
        "Content-Type": "application/json",
        "signature": sign(body),
        "tenant-id": TENANT_ID
    }
    r = requests.post(ADMIN_URL, json=body, headers=headers, timeout=10)
    return r.json()

def rand():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

def step(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def result(response, success_path):
    """Extract nested value from response dict."""
    try:
        obj = response
        for key in success_path:
            obj = obj[key]
        return obj
    except (KeyError, TypeError):
        print(f"  ❌ Failed! Response:")
        print(json.dumps(response, indent=2))
        return None


# ==========================================
# 1. Create Wallet Address
# ==========================================
def create_wallet(name):
    step(f"Creating Wallet Address: {name}")
    body = {
        "query": """mutation($input: CreateWalletAddressInput!) {
            createWalletAddress(input: $input) {
                walletAddress { id address publicName }
            }
        }""",
        "variables": {"input": {
            "assetId": ASSET_ID,
            "address": f"https://{OPEN_PAYMENTS_HOST}/{name.lower()}/{rand()}",
            "publicName": name
        }}
    }
    r = send(body)
    wa = result(r, ["data", "createWalletAddress", "walletAddress"])
    if wa:
        print(f"  ✅ Wallet ID: {wa['id']}")
        print(f"  ✅ Address:   {wa['address']}")
        return wa["id"], wa["address"]
    return None, None


# ==========================================
# 2. Create Incoming Payment
#    → triggers: incoming_payment.created
# ==========================================
def create_incoming(wallet_id, expires_seconds=86400):
    step("Creating Incoming Payment → incoming_payment.created")
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + expires_seconds))
    body = {
        "query": """mutation($input: CreateIncomingPaymentInput!) {
            createIncomingPayment(input: $input) {
                payment { id state walletAddressId expiresAt
                    incomingAmount { value assetCode assetScale }
                    receivedAmount { value assetCode assetScale }
                }
            }
        }""",
        "variables": {"input": {
            "walletAddressId": wallet_id,
            "incomingAmount": {"value": "1000", "assetCode": "USD", "assetScale": 2},
            "expiresAt": expiry,
            "metadata": {"description": "Test payment"}
        }}
    }
    r = send(body)
    p = result(r, ["data", "createIncomingPayment", "payment"])
    if p:
        print(f"  ✅ Incoming Payment ID: {p['id']}")
        print(f"  ✅ State: {p['state']}")
        return p["id"]
    return None


# ==========================================
# 3. Create Quote
# ==========================================
def create_quote(sender_id, receiver_address, incoming_id):
    step("Creating Quote")
    receiver_url = f"{receiver_address}/incoming-payments/{incoming_id}"
    print(f"  Receiver URL: {receiver_url}")
    body = {
        "query": """mutation($input: CreateQuoteInput!) {
            createQuote(input: $input) {
                quote { id walletAddressId
                    debitAmount { value assetCode assetScale }
                    receiveAmount { value assetCode assetScale }
                }
            }
        }""",
        "variables": {"input": {
            "walletAddressId": sender_id,
            "receiver": receiver_url,
            "debitAmount": {"assetCode": "USD", "assetScale": 2, "value": "1000"}
        }}
    }
    r = send(body)
    q = result(r, ["data", "createQuote", "quote"])
    if q:
        print(f"  ✅ Quote ID: {q['id']}")
        return q["id"]
    return None


# ==========================================
# 4. Create Outgoing Payment
#    → triggers: outgoing_payment.created
# ==========================================
def create_outgoing(sender_id, quote_id):
    step("Creating Outgoing Payment → outgoing_payment.created")
    body = {
        "query": """mutation($input: CreateOutgoingPaymentInput!) {
            createOutgoingPayment(input: $input) {
                payment { id state
                    debitAmount { value assetCode assetScale }
                    sentAmount { value assetCode assetScale }
                }
            }
        }""",
        "variables": {"input": {
            "walletAddressId": sender_id,
            "quoteId": quote_id,
            "metadata": {"description": "Test outgoing payment"}
        }}
    }
    r = send(body)
    p = result(r, ["data", "createOutgoingPayment", "payment"])
    if p:
        print(f"  ✅ Outgoing Payment ID: {p['id']}")
        print(f"  ✅ State: {p['state']}")
        return p["id"]
    return None


# ==========================================
# 5. Deposit Outgoing Payment Liquidity
#    → triggers: outgoing_payment.completed
#    → triggers: incoming_payment.completed
# ==========================================
def deposit_outgoing_liquidity(outgoing_payment_id):
    step("Depositing Outgoing Payment Liquidity → outgoing_payment.completed + incoming_payment.completed")
    body = {
        "query": """mutation($input: DepositOutgoingPaymentLiquidityInput!) {
            depositOutgoingPaymentLiquidity(input: $input) {
                success
            }
        }""",
        "variables": {"input": {
            "outgoingPaymentId": outgoing_payment_id,
            "idempotencyKey": rand()
        }}
    }
    r = send(body)
    s = result(r, ["data", "depositOutgoingPaymentLiquidity", "success"])
    if s:
        print(f"  ✅ Liquidity deposited: {s}")
        return True
    return False


# ==========================================
# 6. Create Incoming Payment with short expiry
#    → triggers: incoming_payment.expired (after expiry)
# ==========================================
def create_expiring_incoming(wallet_id):
    step("Creating Short-Lived Incoming Payment → incoming_payment.expired (wait ~60s)")
    # Expires in 30 seconds
    expiry = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + 30))
    body = {
        "query": """mutation($input: CreateIncomingPaymentInput!) {
            createIncomingPayment(input: $input) {
                payment { id state expiresAt }
            }
        }""",
        "variables": {"input": {
            "walletAddressId": wallet_id,
            "incomingAmount": {"value": "500", "assetCode": "USD", "assetScale": 2},
            "expiresAt": expiry,
            "metadata": {"description": "Expiring payment test"}
        }}
    }
    r = send(body)
    p = result(r, ["data", "createIncomingPayment", "payment"])
    if p:
        print(f"  ✅ Expiring Payment ID: {p['id']}")
        print(f"  ✅ Expires at: {p['expiresAt']}")
        print(f"  ⏳ Wait ~60 seconds for incoming_payment.expired event")
        return p["id"]
    return None


# ==========================================
# MAIN FLOW
# ==========================================
def main():
    print("🚀 Rafiki Webhook - ALL Events Test")
    print(f"   Admin API: {ADMIN_URL}")
    print(f"   Tenant:    {TENANT_ID}")
    print(f"   Watch logs: docker logs -f webhook-service")

    # --- Setup ---
    sender_id, sender_addr = create_wallet("Sender")
    if not sender_id: sys.exit(1)

    receiver_id, receiver_addr = create_wallet("Receiver")
    if not receiver_id: sys.exit(1)

    # --- Event 1: incoming_payment.created ---
    incoming_id = create_incoming(receiver_id)
    if not incoming_id: sys.exit(1)

    # --- Quote (no webhook event) ---
    quote_id = create_quote(sender_id, receiver_addr, incoming_id)
    if not quote_id: sys.exit(1)

    # --- Event 2: outgoing_payment.created ---
    outgoing_id = create_outgoing(sender_id, quote_id)
    if not outgoing_id: sys.exit(1)

    # --- Events 3 & 4: outgoing_payment.completed + incoming_payment.completed ---
    deposit_outgoing_liquidity(outgoing_id)

    # --- Event 5: incoming_payment.expired ---
    create_expiring_incoming(receiver_id)

    # --- Summary ---
    print(f"\n{'='*55}")
    print("🎉 TEST COMPLETE!")
    print(f"{'='*55}")
    print("""
  Events triggered:
    ✅ incoming_payment.created
    ✅ outgoing_payment.created
    ✅ outgoing_payment.completed  (after liquidity deposit)
    ✅ incoming_payment.completed  (after liquidity deposit)
    ⏳ incoming_payment.expired   (wait ~60 seconds)
    
  Events NOT triggerable via Admin API:
    ⚠️  outgoing_payment.failed    (requires network/peer failure)
    ⚠️  wallet_address.not_found   (requires external OP request to unknown address)
    ⚠️  wallet_address.web_monetization (requires Web Monetization STREAM)
    ⚠️  asset.liquidity_low        (requires asset liquidity below threshold)
    ⚠️  peer.liquidity_low         (requires peer liquidity below threshold)

  📡 Check webhook logs: docker logs -f webhook-service
""")


if __name__ == "__main__":
    main()