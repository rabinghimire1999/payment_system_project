# test_flow.py
import hmac, hashlib, time, json, requests

SECRET = "iyIgCprjb9uL8wFckR+pLEkJWMB7FJhgkvqhTQR/964="
TENANT_ID = "438fa74a-fa7d-4317-9ced-dde32ece1787"
URL = "http://localhost:3001/graphql"

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
    return requests.post(URL, json=body, headers=headers)


# Step 1: Create Incoming Payment
ip_body = {
    "query": """
    mutation CreateIncomingPayment($input: CreateIncomingPaymentInput!) {
          createIncomingPayment(input: $input) {
            payment {
              id
              state
              receivedAmount {
                value
                assetCode
              }
            }
          }
        }
        """,
        "variables": {
            "input": {
                "walletAddressId": "ffd519a8-ed75-4153-87bd-a916a6504d40",
                "incomingAmount": {
                    "value": "1000",
                    "assetCode": "USD",
                    "assetScale": 2
                }
            }
        }
    }

print("\nCreating Incoming Payment...")
r1 = send(ip_body)
incoming_payment = r1.json()


print(json.dumps(incoming_payment, indent=2))
incoming_payment_id = None

if "data" in incoming_payment:
    incoming_payment_id = (
        incoming_payment["data"]
        ["createIncomingPayment"]
        ["payment"]
        ["id"]
    )
else:
    print("❌ Incoming Payment Failed:")
    print(json.dumps(incoming_payment, indent=2))
    exit(1)
    
# Step 2: Create Quote
quote_body = {
    "query": "mutation CreateQuote($input: CreateQuoteInput!) { createQuote(input: $input) { quote { id } } }",
    "variables": {
        "input": {
            "walletAddressId": "ffd519a8-ed75-4153-87bd-a916a6504d40",
            "receiver": "https://cloud-nine-wallet-backend/timon/vxm-krmg9vjmu2dktk93o/incoming-payments/e4e4a9a1-15ea-4e8c-82c8-d74e352ca074",
            "debitAmount": {
                "assetCode": "USD",
                "assetScale": 2,
                "value": "1000"
            }
        }
    }
}

print("Creating Quote...")
r = send(quote_body)
print(json.dumps(r.json(), indent=2))

quote_id = r.json().get("data", {}).get("createQuote", {}).get("quote", {}).get("id")

if quote_id:
    # Step 3: Create Outgoing Payment
    op_body = {
        "query": "mutation CreateOutgoingPayment($input: CreateOutgoingPaymentInput!) { createOutgoingPayment(input: $input) { payment { id state } } }",
        "variables": {
            "input": {
                "walletAddressId": "ffd519a8-ed75-4153-87bd-a916a6504d40",
                "quoteId": quote_id
            }
        }
    }
    print("\nCreating Outgoing Payment...")
    r2 = send(op_body)
    print(json.dumps(r2.json(), indent=2))