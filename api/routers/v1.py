from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from api.rate_limit import limiter, RATE_LIMIT_PER_MINUTE, RATE_LIMIT_VALIDATE_PER_MINUTE

router = APIRouter(prefix="/v1")


@router.post("/generate", description="Get a random test data of your choice")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def generate(request: Request, pay_load: dict):
    try:
        SpecValidator.validate(pay_load)
        output = generate_dataset(pay_load)
        return JSONResponse(content={"data": output}, status_code=200)
    except SpecValidatorException as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
