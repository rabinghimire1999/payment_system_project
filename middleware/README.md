# Interledger Payment Gateway

## 🚀 Overview

The **Interledger Payment Gateway** is a high-performance financial orchestrator designed to bridge traditional Core Banking Systems (CBS) with the modern **Interledger Protocol (ILP)** via **Rafiki**.

It enables cross-institutional value movement, automated member onboarding, and real-time liquidity management using a dual-ledger system.

### Key Features

- **Multi-Tenant Identity:** Automated creation of Rafiki Tenants and unique Payment Pointers for every fsp.
- **Atomic Cross-Coop Transfers:** 4-step transaction orchestration (Incoming → Quote → Outgoing → Settlement).
- **Shadow Ledgering:** A high-integrity PostgreSQL ledger that tracks NPR balances and provides detailed transaction history.
- **Asynchronous Webhooks:** Real-time event handling from the Rafiki network to finalize ledger states.

---

## 🏗 Architecture

The project follows a microservices pattern split across three primary layers:

1.  **Transformer (Entry Point):** The public-facing REST API (FastAPI) that handles schema validation, security, and request routing.
2.  **Middleware (The Brain):** The core orchestration engine that manages Rafiki GraphQL calls and business logic.
3.  **Database Service:** The source of truth for fsp identities, internal balances, and audit trails.
4.  **Rafiki (Settlement Engine):** The ILP engine that handles the actual movement of digital value.

---

## 🛠 Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **PostgreSQL 15+**
- **PNPM** (for Rafiki Testnet local environment)

---

## ⚙️ Installation & Setup

### 1. Start the Rafiki Testnet

Follow the instructions in the [Rafiki Testnet Repository](https://github.com/interledger/testnet).

```bash
cd rafiki-testnet/local
pnpm run local:setup
```

_The Admin API will be available at `https://rafiki-backend.testnet.test/graphql`._

### 2. Configure Environment Variables

Create a `.env` file in the `middleware/` root directory:

```env
DATABASE_SERVICE_URL=http://192.168.x.x:8000/v1
RAFIKI_ADMIN_URL=https://rafiki-backend.testnet.test/graphql
ADMIN_API_SECRET=your-rafiki-admin-key
OPERATOR_TENANT_ID=your-operator-uuid
OPERATOR_HMAC_SECRET=your-signature-secret
```

### 3. Install Dependencies

```bash
cd middleware
pip install -r requirements.txt
```

---

## 🚀 Running the Project

### Development Mode (Direct)

Run the launcher from the `middleware/` root to ensure all modules are in the Python path:

```bash
PYTHONPATH=. python run_transformer.py
```

### Production Mode (Docker)

```bash
docker-compose up --build -d
```

The API will be accessible at `http://<server-ip>:8001`.

---

## 🧪 Testing the Flow

We have provided specialized scripts in `backend/scripts/` to test each phase of the Financial Service Provider lifecycle.

| Script Name           | Purpose                                                      |
| :-------------------- | :----------------------------------------------------------- |
| `test_rafiki_conn.py` | Verifies the HMAC handshake and creates a test Tenant/Asset. |
| `test_enrollment.py`  | Tests the full 3-step enrollment (DB → Tenant → Wallet).     |
| `test_funding_db.py`  | Funds a specific fsp ID in both Rafiki and the DB.   |
| `test_payment_db.py`  | Orchestrates a full transfer between two DB IDs.             |

**How to run a test:**

```bash
# Run from the middleware root
python -m backend.scripts.test_payment_db
```

---

## API Endpoints

### fsp Profile

- `POST /api/v1/fsp/enroll`: Legal identity registration.
- `GET /api/v1/fsp/all`: List all active fsps (sanitized).
- `GET /api/v1/fsp/{id}`: Detailed profile view.

### Wallet Services

- `POST /api/v1/wallet/create`: Activates the Rafiki wallet and asset.
- `GET /api/v1/fsp/balance_inquiry/{id}`: Real-time balance check.
- `POST /api/v1/fsp/{id}/credit`: Operator-led account funding.

### Transaction Engine

- `POST /api/v1/payment/transfer`: Triggers cross-coop settlement.
- `GET /api/v1/payment/history/{id}`: Labeled Debit/Credit history.

---

## 📖 Glossary

- **ASE:** Account Servicing Entity (Financial Service Provider).
- **Shadow Ledger:** Our internal database that tracks the "User-facing" truth.
- **Settlement:** The actual ILP value movement occurring within Rafiki.
- **Payment Pointer:** The public URL used to identify a wallet .

---

**Interledger Payment Gateway Team | 2026**
