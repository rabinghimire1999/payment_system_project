# Interledger Payment Gateway (IPG)

<p align="center">
<img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
<img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx" />
<img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
<img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux" />
</p>

### Secure, Scalable Payment Processing and Settlement Middleware

## Overview

The **Interledger Payment Gateway (IPG)** is a high-performance,
microservices-based financial orchestration platform designed to connect
banks, financial institutions, payment service providers, merchants, and
digital wallets through the **Interledger Protocol (ILP)** using
**Rafiki**.

The platform provides a unified integration layer for payment
initiation, transaction orchestration, identity management, internal
accounting (Shadow Ledger), liquidity management, and secure payment
settlement.

By leveraging Interledger, the gateway enables different financial
networks and payment systems to communicate and exchange value without
requiring every participating institution to establish a direct
integration with every other institution.

The platform is designed around a modular architecture that supports
multiple financial institutions, payment providers, and payment
applications.

### Key Features

-   **Multi-Tenant Identity Management:** Automated creation and
    management of Rafiki Tenants, accounts, assets, and unique Payment
    Pointers.
-   **Cross-Institutional Payments:** Enables payment transfers between
    participating institutions through the Interledger network.
-   **Payment Orchestration:** Coordinates the payment lifecycle,
    including Incoming Payments, Quotes, Outgoing Payments, and
    settlement.
-   **Shadow Ledger:** A PostgreSQL-based internal accounting system
    that maintains account balances, transaction records, and financial
    history.
-   **Asynchronous Webhooks:** Processes Rafiki events to coordinate
    payment execution and synchronize transaction states.
-   **Liquidity Management:** Coordinates asset and payment liquidity to
    facilitate successful transactions.
-   **Secure Communication:** Uses JWT authentication, API keys, and
    HMAC-SHA256 request signing.
-   **Microservices Architecture:** Separates API handling, business
    logic, database operations, and event processing for scalability and
    maintainability.

------------------------------------------------------------------------

## Understanding the Interledger Protocol (ILP)

### What Is Interledger?

The **Interledger Protocol (ILP)** is an open protocol designed to
enable payments across different financial networks, currencies, and
ledger systems.

It works similarly to how the Internet Protocol (IP) enables computers
on different networks to communicate. Interledger enables participants
on different payment networks to exchange value through a network of
intermediaries called **connectors**.

For example:

-   Institution A maintains customer accounts in one banking system.
-   Institution B maintains customer accounts in another banking system.
-   Both institutions connect to the Interledger network through
    compatible infrastructure.
-   A customer at Institution A initiates a payment to a recipient at
    Institution B.
-   The payment is routed through one or more connectors to reach the
    destination.

The participating institutions do not need to use the same banking
software, ledger technology, or payment infrastructure.

### How Interledger Works

Interledger uses a packet-based payment mechanism. Instead of
transferring the entire payment through one centralized system, the
protocol sends conditional payment packets through a network of
connected participants.

The core components are:

  -----------------------------------------------------------------------
  Component                           Description
  ----------------------------------- -----------------------------------
  Sender                              The participant initiating a
                                      payment.

  Receiver                            The participant receiving a
                                      payment.

  Connector                           An intermediary that forwards
                                      payment packets between
                                      participants.

  Ledger                              An underlying system that maintains
                                      accounts and balances.

  ILP Address                         A network address used to identify
                                      a payment destination.

  Payment Pointer                     A user-facing identifier that helps
                                      locate a recipient's payment
                                      endpoint.
  -----------------------------------------------------------------------

### Interledger Technology Layers

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Application Layer       Open Payments, SPSP     Payment initiation,
                                                  discovery, and
                                                  authorization.

  Transport Layer         STREAM                  Secure communication,
                                                  packet delivery, and
                                                  payment reliability.

  Interledger Layer       ILPv4                   Conditional payment
                                                  packet routing between
                                                  participants.

  Link Layer              Authenticated peer      Communication between
                          connections             directly connected
                                                  network participants.

  Settlement Layer        Bank ledgers, payment   Underlying balances and
                          systems, and other      settlement
                          ledgers                 arrangements.
  -----------------------------------------------------------------------

Each layer has a specific responsibility, allowing different payment
systems to interoperate without requiring them to share the same
underlying infrastructure.

### ILP Packet Types

ILPv4 defines three primary packet types.

#### 1. Prepare

A Prepare packet represents a proposed conditional transfer of value.

It contains:

-   Destination ILP address.
-   Amount to be transferred.
-   Cryptographic condition.
-   Expiration time.
-   Optional application-specific data.

The sender forwards this packet to a connector, which attempts to route
it toward the destination.

#### 2. Fulfill

A Fulfill packet indicates that the payment condition has been
satisfied.

It contains a cryptographic fulfillment corresponding to the condition
included in the original Prepare packet.

Connectors validate the fulfillment and relay it back through the
payment path. A valid fulfillment received before expiration confirms
the corresponding conditional transfer.

#### 3. Reject

A Reject packet indicates that a payment packet could not be processed
successfully.

A packet may be rejected because:

-   The connector cannot route the payment.
-   Available liquidity or credit is insufficient.
-   The receiver does not accept the payment.
-   The packet has expired.
-   Another processing or validation error occurs.

A rejected or expired packet does not complete the corresponding
conditional transfer.

### Interledger Payment Flow: Step by Step

Consider a customer sending a payment from Institution A to a recipient
at Institution B.

1.  **Payment Initiation:** The sender initiates a payment through
    Institution A's payment application or API.
2.  **Recipient Discovery:** The payment application identifies the
    recipient using a Payment Pointer or another supported payment
    identifier.
3.  **Payment Setup:** The sender and receiver establish the necessary
    payment information, including the destination, amount, and payment
    conditions.
4.  **Packet Preparation:** The sending system generates ILP Prepare
    packets containing the destination, amount, cryptographic condition,
    and expiration time.
5.  **Routing Through Connectors:** Packets are forwarded through one or
    more Interledger connectors. Each connector determines the next hop
    using its routing information and applies applicable exchange rates
    and fees.
6.  **Receiver Validation:** The receiving system validates the incoming
    payment and determines whether it can accept the transfer.
7.  **Payment Fulfillment:** If accepted, the receiver returns an ILP
    Fulfill packet containing the cryptographic fulfillment.
8.  **Fulfillment Propagation:** Connectors validate the fulfillment and
    relay it backward through the payment path.
9.  **Balance Updates:** Successful conditional transfers are reflected
    in the accounting balances between participating peers. Underlying
    ledgers and settlement arrangements manage liquidity and outstanding
    obligations.
10. **Payment Completion:** The sending and receiving systems update
    their transaction records and communicate the final payment status.

If the payment cannot be completed, the receiver or a connector returns
a Reject packet, or the packet expires.

### Understanding Conditional Payments

One of the most important features of Interledger is its use of
cryptographic conditions and fulfillments.

A sender creates a secret value and generates a cryptographic condition
from it. The condition is included in the Prepare packet.

The receiver must provide the corresponding fulfillment to satisfy that
condition.

This creates a coordinated payment mechanism:

-   The sender prepares the payment.
-   Connectors forward the conditional payment.
-   The receiver accepts the payment.
-   The fulfillment travels backward through the payment path.
-   Each participating connector validates the fulfillment before
    confirming its corresponding balance adjustment.

This mechanism helps prevent a connector from independently completing
only one part of a successfully fulfilled payment path.

### Currency and Payment Network Interoperability

Interledger is designed to work across different assets and underlying
ledger systems.

For example:

-   Institution A may maintain balances in Currency A.
-   Institution B may maintain balances in Currency B.
-   A connector may support the exchange between the two assets.

During payment routing, connectors can apply configured exchange rates
and fees to determine the amount forwarded to the next participant.

The Interledger Protocol itself does not provide a universal currency
conversion service. Exchange rates and liquidity are provided by
participating connectors and their associated services.

This enables interoperability without requiring all participants to
maintain accounts in the same currency or operate on the same ledger
technology.

------------------------------------------------------------------------

## How Rafiki Fits into Interledger

**Rafiki** is an open-source implementation of the Interledger
technology stack. It enables financial service providers to connect
their existing account infrastructure to Interledger.

Rather than building an Interledger connector, payment routing
infrastructure, and related services from scratch, institutions can use
Rafiki to provide Interledger-compatible payment capabilities.

Rafiki provides functionality for:

-   Tenant and account management.
-   Asset configuration.
-   Payment Pointer generation.
-   Incoming Payment creation.
-   Outgoing Payment creation.
-   Quotes and payment execution.
-   Interledger packet processing.
-   Liquidity and accounting management.
-   Webhook event notifications.

### Important Rafiki Components

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  Rafiki Backend                      Manages payment operations, account
                                      interactions, and administrative
                                      functionality.

  Interledger Connector               Sends and receives ILP packets and
                                      communicates with network peers.

  Open Payments API                   Provides standardized interfaces
                                      for payment setup and execution.

  STREAM                              Handles secure and reliable
                                      packet-based payment communication.

  Payment Pointers                    Identify recipient payment
                                      endpoints.

  Webhooks                            Notify external applications about
                                      payment-related events.
  -----------------------------------------------------------------------

### Payment Pointers and STREAM

A Payment Pointer is a user-facing identifier associated with a payment
account.

For example:

``` text
$wallet.example.com/alice
```

A Payment Pointer can resolve to an HTTPS endpoint that provides payment
setup information.

The Simple Payment Setup Protocol (SPSP) can provide the recipient's ILP
address and shared secret. These details are used to establish a STREAM
connection between the sender and receiver.

STREAM handles secure communication, packet creation, encryption, and
reliable delivery over the Interledger network.

------------------------------------------------------------------------

## System Architecture

The Interledger Payment Gateway is divided into five decoupled
components to ensure security, scalability, maintainability, and high
availability.

1.  **Nginx (Reverse Proxy):** Acts as the entry point, handling SSL
    termination, request routing, and reverse proxy configuration.
2.  **Transformer (Entry Point):** A FastAPI service responsible for
    validating request schemas, handling authentication, managing public
    API security (JWT/API Keys), and routing incoming requests.
3.  **Brain (Middleware):** The core orchestration engine responsible
    for business logic, Rafiki GraphQL operations, payment workflows,
    liquidity management, and transaction coordination.
4.  **Database Service:** The persistence layer and source of truth for
    institution identities, account information, internal balances,
    transaction records, and audit trails.
5.  **Webhook Service:** A reactive event listener that processes Rafiki
    events and coordinates asynchronous payment execution, settlement,
    and transaction status updates.

### High-Level Architecture Flow

``` text
              Financial Institutions
                        |
                 Payment Requests
                        |
                        v
                +---------------+
                |     NGINX     |
                | Reverse Proxy |
                +---------------+
                        |
                        v
                +---------------+
                |  Transformer  |
                |    FastAPI    |
                | API Gateway   |
                +---------------+
                        |
                        v
                +---------------+
                |     Brain     |
                |  Middleware   |
                | Orchestration |
                +---------------+
                   |         |
                   v         v
             +----------+  +----------+
             | Database |  |  Rafiki  |
             | Service  |  |  Backend |
             +----------+  +----------+
                                |
                                v
                       +----------------+
                       | ILP Connector  |
                       +----------------+
                                |
                                v
                       Interledger Network
                                |
                                v
                       Other Connectors
                                |
                                v
                       Receiving Rafiki
                                |
                                v
                       Receiving Institution

                Rafiki Events
                      |
                      v
                +-----------+
                |  Webhook  |
                |  Service  |
                +-----------+
                      |
                      v
                Brain / Database
```

------------------------------------------------------------------------

## Tech Stack

  Component             Technology
  --------------------- -------------------------------
  Backend               Python 3.11, FastAPI
  Interledger Engine    Rafiki (v2.2.0-beta)
  Payment Protocol      Interledger Protocol (ILPv4)
  Payment APIs          Open Payments, GraphQL, REST
  Transport Protocol    STREAM
  Database              PostgreSQL 16
  Event Queue / Cache   Redis
  Authentication        JWT (jose)
  Password Security     Bcrypt (passlib)
  Request Integrity     HMAC-SHA256
  Infrastructure        Docker, Docker Compose, Nginx
  Operating System      RHEL 10 / Linux

------------------------------------------------------------------------

## Project Structure

``` text
payment-gateway/
├── docker-compose.yml          # Root Orchestrator
├── nginx.conf                  # Reverse Proxy Configuration
├── middleware/                 # Core Payment Middleware
│   ├── .env                    # Middleware Secrets
│   ├── Dockerfile              # Multi-stage Build
│   ├── backend/                # Business Logic & Rafiki Services
│   └── transformer/            # API Routes & Schema Validation
├── webhook/                    # Reactive Event Listener
│   ├── .env                    # Webhook Secrets
│   ├── Dockerfile
│   └── app/                    # Event Relay Logic
└── database/                   # Persistent Database Service
```

------------------------------------------------------------------------

## Configuration & Setup

### 1. Prerequisites

-   Docker and Docker Compose installed.
-   Access to a running Rafiki instance.
-   Rafiki Admin API access (default port 3001).
-   Python 3.11 or later.
-   PostgreSQL 16.
-   Redis.

### 2. Environment Variables

Each service requires its own `.env` file.

**Middleware (`middleware/.env`)**

  Variable                 Description
  ------------------------ ----------------------------------------
  `DATABASE_SERVICE_URL`   URL for the database service API.
  `DATABASE_API_KEY`       Secret for internal database access.
  `RAFIKI_ADMIN_URL`       Rafiki Admin GraphQL endpoint.
  `ADMIN_API_SECRET`       Secret for Rafiki request signatures.
  `MIDDLEWARE_ADMIN_KEY`   Key for administrative API operations.

Example:

``` env
DATABASE_SERVICE_URL=http://localhost:8000/v1
DATABASE_API_KEY=your-database-api-key
RAFIKI_ADMIN_URL=https://rafiki-backend.testnet.test/graphql
ADMIN_API_SECRET=your-rafiki-admin-key
MIDDLEWARE_ADMIN_KEY=your-middleware-admin-key
```

Replace the placeholder values with the actual service endpoints and
credentials.

Never commit `.env` files or sensitive credentials to version control.

------------------------------------------------------------------------

## Deployment via Docker

The entire stack is containerized for simplified deployment and service
management.

### Start the Entire System

``` bash
# Build and run all services in detached mode
sudo docker compose up --build -d
```

### Management Commands

``` bash
# Check middleware logs
docker logs -f ipg-middleware-app

# Check running containers
docker compose ps

# Restart the entire stack
docker compose restart

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

**Warning:** The `docker compose down -v` command removes associated
persistent volumes and may permanently delete database data.

------------------------------------------------------------------------

## Payment Processing Workflow (Rafiki Integration)

The gateway uses a **Just-in-Time (JIT) Funding** model to coordinate
liquidity provisioning and payment settlement.

This workflow represents the application-level orchestration performed
by the middleware and Rafiki. It complements the underlying ILP
Prepare/Fulfill/Reject packet lifecycle described earlier.

### The Rafiki Payment Flow

1.  **Initiation:** The middleware creates the required
    `IncomingPayment`, `Quote`, and `OutgoingPayment` resources through
    Rafiki.
2.  **Notification:** Rafiki generates an `outgoing_payment.created`
    event, which is received by the Webhook Service.
3.  **Liquidity Provisioning:** The Webhook Service triggers the Brain
    to coordinate the required asset and payment liquidity provisioning
    through the relevant Rafiki operations.
4.  **Settlement:** The middleware coordinates the payment execution and
    settlement operations.
5.  **Release:** Once the payment conditions are satisfied, the
    middleware invokes `createIncomingPaymentWithdrawal` to release the
    funds into the receiver's spendable balance.
6.  **Finalization:** The PostgreSQL database is updated with the final
    transaction status (`COMPLETED`), and the Shadow Ledger balances are
    adjusted accordingly.

### Payment Lifecycle

``` text
       Payment Initiation
               |
               v
       Create IncomingPayment
               |
               v
          Generate Quote
               |
               v
       Create OutgoingPayment
               |
               v
       Rafiki Webhook Event
               |
               v
       Liquidity Provisioning
               |
               v
        Payment Execution
               |
               v
       ILP Packet Processing
               |
          +----+----+
          |         |
          v         v
       Fulfill    Reject
          |         |
          v         v
      Successful  Failed
       Payment    Payment
          |
          v
    Incoming Payment
       Withdrawal
          |
          v
     Shadow Ledger
       Update
          |
          v
      COMPLETED
```

The gateway maintains internal transaction records and coordinates the
application-level payment lifecycle, while Rafiki and the Interledger
network handle the underlying payment protocol operations.

------------------------------------------------------------------------

## Testing Specific Modules

CLI scripts are provided to test individual modules and payment
workflows without requiring interaction through the UI.

``` bash
# Test Enrollment (Phase 1 & 2)
python -m backend.scripts.test_enrollment

# Test JIT Payment Transfer (Full Loop)
python -m backend.scripts.test_jit_payment

# Find/Create Operator Assets
python -m backend.scripts.test_funding_db
```

------------------------------------------------------------------------

## Security Model

### 1. Authentication and Authorization

-   **Operator Operations:** Secured using `X-Admin-Key`, a high-entropy
    administrative secret.
-   **Institution Operations:** Secured using JWT Bearer Tokens obtained
    through `/auth/login`.
-   **Internal Service Communication:** Protected through API keys and
    service-level authentication.

### 2. Request Integrity

-   **HMAC Signing:** Requests to Rafiki are signed using HMAC-SHA256
    with deterministic JSON canonicalization.
-   **Shadow Ledger:** Every transaction is validated against internal
    accounting records before initiating the relevant payment operations
    to prevent unauthorized transfers and overdrafts.
-   **Credential Management:** Sensitive credentials are stored in
    environment variables and should be managed through a secure
    secrets-management solution in production.

### 3. Transaction Safety

-   Validate payment requests before processing.
-   Maintain transaction status throughout the payment lifecycle.
-   Handle asynchronous events through the webhook service.
-   Implement idempotency to prevent duplicate payment processing.
-   Maintain consistent accounting records for successful and failed
    transactions.
-   Implement appropriate timeout, retry, and recovery mechanisms.

------------------------------------------------------------------------

## Roadmap

-   [ ] **Multi-Institution Support:** Enable onboarding and management
    of multiple participating financial institutions.
-   [ ] **Multi-Account Layer:** Support multiple accounts and wallets
    under each institution.
-   [ ] **Fee Engine:** Implement automatic transaction fee calculation
    and deduction.
-   [ ] **Exchange Rate Engine:** Support configurable exchange rates
    and multi-currency payment processing.
-   [ ] **Payment Provider Integration:** Integrate external payment
    providers and financial systems.
-   [ ] **Transaction Reconciliation:** Implement automated
    reconciliation between internal ledger records and external
    settlement systems.
-   [ ] **Monitoring and Observability:** Introduce centralized logging,
    metrics, tracing, and transaction monitoring.
-   [ ] **Retry and Recovery:** Implement reliable retry mechanisms and
    recovery workflows for failed or pending transactions.
-   [ ] **Enhanced Security:** Introduce advanced access controls, rate
    limiting, and centralized secrets management.
-   [ ] **Production Interledger Connectivity:** Establish production
    peering relationships and configure routing, liquidity, and
    settlement arrangements with network participants.

------------------------------------------------------------------------

## Useful Resources and Documentation

  ----------------------------------------------------------------------------------------------------------------------
  Resource                                                                           Description
  ---------------------------------------------------------------------------------- -----------------------------------
  [Interledger Developer Getting                                                     Introduction to building
  Started](https://interledger.org/developers/get-started/)                          applications using Interledger.

  [Interledger Protocol                                                              Official specification for
  (ILPv4)](https://interledger.org/developers/rfcs/interledger-protocol/)            packet-based value transfers.

  [Interledger                                                                       Explains the different layers of
  Architecture](https://interledger.org/developers/rfcs/interledger-architecture/)   the Interledger ecosystem.

  [Interledger Technology Stack](https://interledger.org/tech/overview/)             Overview of Open Payments, STREAM,
                                                                                     ILP, and settlement layers.

  [Rafiki Documentation](https://rafiki.dev/)                                        Documentation for the Rafiki
                                                                                     Interledger implementation.

  [Open Payments](https://openpayments.dev/)                                         Standardized APIs for initiating
                                                                                     and authorizing payments.

  [Rafiki Testnet](https://github.com/interledger/testnet)                           Local test environment for
                                                                                     experimenting with Interledger.
  ----------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

**Interledger Payment Gateway (IPG) \| 2026**
