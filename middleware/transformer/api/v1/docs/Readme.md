## Setup


## API Endpoints

### fsp & Asset
- POST /api/v1/fsp/enroll
- GET  /api/v1/fsp/balance_inquiry/{fsp_id}
- POST /api/v1/asset/create
-POST  /api/v1/fsp/{fsp_id}/credit --> for loading balance in fsp 

### Payments
- POST /api/v1/payment/transfer
- GET  /api/v1/payment/status/{payment_id}

### Wallet
- POST /api/v1/wallet/create
- POST /api/v1/wallet/create