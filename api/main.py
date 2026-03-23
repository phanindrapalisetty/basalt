<<<<<<< HEAD
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler  # type: ignore[import-untyped]
from slowapi.errors import RateLimitExceeded  # type: ignore[import-untyped]
from api.rate_limit import limiter
from api.routers.v1 import router as v1_router
=======
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, Response
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from core.formatters import get_formatter, SUPPORTED_FORMATS
>>>>>>> 4182667 (feat: output formats — JSON, NDJSON, CSV, Parquet, Avro via ?format= param)

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


<<<<<<< HEAD
# Backwards-compat redirects (308 preserves the request method and body)
@app.post("/generate")
async def generate_compat():
    return RedirectResponse(url="/v1/generate", status_code=308)
=======
@app.post("/generate", description="Get a random test data of your choice")
async def generate(
    pay_load: dict,
    format: str = Query(default="json", description=f"Output format. One of: {SUPPORTED_FORMATS}"),
):
    try:
        SpecValidator.validate(pay_load)
        output = generate_dataset(pay_load)
        formatter = get_formatter(format)
        data = formatter.format(output)
        if format == "json":
            return JSONResponse(content={"data": output}, status_code=200)
        return Response(
            content=data,
            media_type=formatter.content_type,
            headers={"Content-Disposition": f"attachment; filename=basalt.{formatter.extension}"},
        )
    except SpecValidatorException as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
>>>>>>> 4182667 (feat: output formats — JSON, NDJSON, CSV, Parquet, Avro via ?format= param)
