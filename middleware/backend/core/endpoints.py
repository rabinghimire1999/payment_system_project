from backend.core.config import settings

# TEAM C (Database Service) Endpoints
DB_BASE_URL = settings.DATABASE_SERVICE_URL

CREATE_COOP_URL = f"{DB_BASE_URL}/internal/fsps"
# GET_ASSET_URL = f"{DB_BASE_URL}/internal/assets"
UPDATE_COOP_URL = lambda coop_id: f"{DB_BASE_URL}/internal/fsps/{coop_id}"

# RAFIKI Endpoints
RAFIKI_GRAPHQL_URL = settings.RAFIKI_ADMIN_URL

