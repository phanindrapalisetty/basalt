import os
from slowapi import Limiter
from slowapi.util import get_remote_address

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
RATE_LIMIT_VALIDATE_PER_MINUTE = os.getenv("RATE_LIMIT_VALIDATE_PER_MINUTE", "200")

limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)
