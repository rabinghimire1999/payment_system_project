## Webhook
- Webhook is responsible to catch the event from rafiki.

## Setup
- Clone the webhook from repo

## Install dependencies
``` bash
    pip install -r requirements.txt
```

## Startup
``` bash
    docker compose up --build
```

## To stop service 
``` bash
    docker compose down
```

## To run test
``` bash
    python3 test_webhook.py
```

## APIs
- POST /webhook/rafiki

## Important concept to now before running webhook
- Create env file
- Configure your webhook url in rafiki/testnet to get events in webhook
- Eg: RAFIKI_BACKEND_WEBHOOK_URL=http://192.168.77.138:8000/webhook/rafiki
- Note: Use your ip
- Use SIGNATURE_SECRET given by rafiki/testnet in ur webhook

## How does our webhook verify the signature 
- Rafiki generate the signature using a secret key and hmac
- Webhook also uses same secret key and hmac algorithm to verify the signature sent by rafiki 

## How does webhook store the event/data given by rafiki
- Events data are stored in database and event id is stored in redis