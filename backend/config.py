# Plain-English description: Loads and manages environment configuration, secrets, and cryptographic keys.

import os
from pathlib import Path

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database URL from environment with fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres_password@localhost:5432/vibecheck_db"
)

# Redis / Celery broker URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# Load RSA keys from environment variables or local key files
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")

private_key_file = os.getenv("JWT_PRIVATE_KEY_PATH", str(BASE_DIR / "jwt_rs256.key"))
public_key_file = os.getenv("JWT_PUBLIC_KEY_PATH", str(BASE_DIR / "jwt_rs256.key.pub"))

if not JWT_PRIVATE_KEY and os.path.exists(private_key_file):
    with open(private_key_file, "r", encoding="utf-8") as f:
        JWT_PRIVATE_KEY = f.read()

if not JWT_PUBLIC_KEY and os.path.exists(public_key_file):
    with open(public_key_file, "r", encoding="utf-8") as f:
        JWT_PUBLIC_KEY = f.read()

# Storage directory for uploaded videos (MOCK for Azure Blob)
STORAGE_DIR = BASE_DIR / "backend" / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Upload limits (50 MB in bytes)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

