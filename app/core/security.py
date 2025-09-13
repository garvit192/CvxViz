from fastapi import Header, HTTPException, status, Depends
from app.core.config import settings

def verify_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if not x_api_key or x_api_key != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return True

RequireAPIKey = Depends(verify_api_key)
