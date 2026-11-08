import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.ADMIN_API_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# --- SECURITY SCHEMES (Matches main.py components) ---

# 1. Set auto_error=False so it doesn't crash if the header is missing
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter JWT Token",
    auto_error=False,  # <--- ADD THIS
)

# 2. Set auto_error=False for Admin Key as well
admin_key_scheme = APIKeyHeader(
    name="X-Admin-Key", scheme_name="AdminKey", auto_error=False  # <--- ADD THIS
)


def _get_password_hash_input(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    pre_hashed = _get_password_hash_input(password)
    return pwd_context.hash(pre_hashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = _get_password_hash_input(plain_password)
    return pwd_context.verify(pre_hashed, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- THE GUARDS (Dependencies) ---


async def verify_admin_access(x_admin_key: str = Security(admin_key_scheme)):
    """
    Validates the Master Admin Key.
    Use 'Security' instead of 'Depends' to ensure Swagger UI picks it up.
    """
    if not x_admin_key or x_admin_key != settings.MIDDLEWARE_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Invalid Admin Key",
        )
    return True


async def get_current_fsp(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """
    Verifies the JWT and returns the internal fsp ID (sub).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
        )

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        coop_id: str = payload.get("sub")

        if coop_id is None:
            raise credentials_exception

        return str(coop_id)

    except JWTError:
        raise credentials_exception


async def get_actor_id(
    x_admin_key: Optional[str] = Security(admin_key_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """
    Identifies the caller.
    Logic:
    1. First, check if a valid Admin Key is present.
    2. If not, check if a valid Bearer Token is present.
    3. If neither, throw 401.
    """
    # 1. Check Admin Key
    if x_admin_key and x_admin_key == settings.MIDDLEWARE_ADMIN_KEY:
        return "ADMIN"

    # 2. Check fsp JWT
    if credentials and credentials.credentials:
        try:
            payload = jwt.decode(
                credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
            )
            coop_id: str = payload.get("sub")
            if coop_id:
                return str(coop_id)
        except JWTError:
            # If a token was provided but it's invalid, we should inform the user
            raise HTTPException(
                status_code=401, detail="Invalid or expired fsp token"
            )

    # 3. If we reach here, no valid auth was provided at all
    raise HTTPException(
        status_code=401,
        detail="Authentication required: Provide X-Admin-Key or Authorization Bearer Token",
        headers={"WWW-Authenticate": "Bearer"},
    )
