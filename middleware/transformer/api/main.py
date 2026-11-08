from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from transformer.api.v1.routes import (
    fsp,
    payment,
    wallet,
    auth,
    internal,
    member,
)

# --- NEW: Import for OpenAPI Customization ---
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="ipg Middleware Gateway",
    version="1.0.0",
    description="Secure Interledger Gateway for financial service providers (FSPs) to facilitate cross-fsp transactions and wallet management.",
    openapi_tags=[
        {"name": "Authentication", "description": "Login and session management"},
        {"name": "fsp Profile", "description": "KYC and Identity registration"},
        {
            "name": "Wallet Services",
            "description": "Activation and Liquidity management",
        },
        {
            "name": "Transaction Engine",
            "description": "Cross-fsp money movement",
        },
        {
            "name": "Member Management",
            "description": "Individual member onboarding and wallets",
        },
    ],
)

# CORS Configuration - IMPORTANT: In production, replace "*" with your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES REGISTRATION ---

# Internal routes (Hidden from Swagger)
app.include_router(internal.router, prefix="/api/v1", include_in_schema=False)

# Public routes with Tags
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(fsp.router, prefix="/api/v1", tags=["fsp Profile"])
app.include_router(wallet.router, prefix="/api/v1", tags=["Wallet Services"])
app.include_router(payment.router, prefix="/api/v1", tags=["Transaction Engine"])
app.include_router(member.router, prefix="/api/v1", tags=["Member Management"])


# --- NEW: CUSTOM OPENAPI SECURITY CONFIG ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 1. Define the JWT Bearer Security Scheme
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter the JWT token received from /auth/login",
    }

    # 2. Define the Admin API Key Security Scheme
    openapi_schema["components"]["securitySchemes"]["AdminKey"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Admin-Key",
        "description": "Master Middleware Admin Key for Operator tasks",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
