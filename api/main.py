from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler  # type: ignore[import-untyped]
from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]
from api.rate_limit import limiter
from api.routers.v1 import router as v1_router

app = FastAPI(title="Basalt", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(v1_router)


@app.get("/health")
async def get_health_status():
    try:
        return JSONResponse(content={"message": "I'm Pikachu!!!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


# Backwards-compat redirects (308 preserves the request method and body)
@app.post("/generate")
async def generate_compat():
    return RedirectResponse(url="/v1/generate", status_code=308)
