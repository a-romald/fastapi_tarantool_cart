import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from fastapi.security import APIKeyHeader

from config import settings
from shop.routes import router as shop_router


api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=True)

def handle_api_key(api_key: str = Security(api_key_header)):
    if api_key == settings.VALID_API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API Key"
    )


app = FastAPI(
    dependencies=[
        Depends(handle_api_key),
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shop_router, tags=["Cart"], prefix="/cart")

@app.get("/")
async def home():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
