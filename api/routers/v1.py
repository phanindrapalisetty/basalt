from fastapi import APIRouter, Query, Request # type: ignore[import-untyped]
from fastapi.responses import JSONResponse, Response # type: ignore[import-untyped]
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from core.formatters import get_formatter, SUPPORTED_FORMATS
from api.rate_limit import limiter, RATE_LIMIT_PER_MINUTE, RATE_LIMIT_VALIDATE_PER_MINUTE

router = APIRouter(prefix="/v1")


@router.post("/generate", description="Get a random test data of your choice")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def generate(
    request: Request,
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
