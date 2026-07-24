from slowapi import _rate_limit_exceeded_handler  # type: ignore[import-untyped]
from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]
from api.rate_limit import limiter
from api.routers.v1 import router as v1_router

from fastapi import FastAPI, Query # type: ignore[import-untyped]
from fastapi.responses import JSONResponse, Response, RedirectResponse # type: ignore[import-untyped]
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from core.formatters import get_formatter, SUPPORTED_FORMATS
from core.inferrer import infer_spec


app = FastAPI(title="Basalt", version="1.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(v1_router)


@app.get("/health")
async def get_health_status():
    try:
        return JSONResponse(content={"message": "I'm Pikachu!!!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.post("/validate", description="Validate a spec without generating data")
async def validate(pay_load: dict):
    try:
        SpecValidator.validate(pay_load)
        return JSONResponse(content={"valid": True}, status_code=200)
    except SpecValidatorException as e:
        return JSONResponse(content={"valid": False, "error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"valid": False, "error": str(e)}, status_code=500)


@app.post("/infer", description="Infer a Basalt spec from a sample JSON array")
async def infer(pay_load: dict):
    try:
        rows = pay_load.get("rows")
        seed = pay_load.get("seed", 42)
        if not isinstance(rows, list):
            return JSONResponse(content={"error": "'rows' must be a JSON array"}, status_code=422)
        spec = infer_spec(rows, seed=seed)
        return JSONResponse(content={"spec": spec}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)