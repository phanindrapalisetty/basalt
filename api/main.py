from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, Response
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from core.formatters import get_formatter, SUPPORTED_FORMATS

app = FastAPI(title="Basalt", version="1.0.0")


@app.get("/health")
async def get_health_status():
    try:
        return JSONResponse(content={"message": "I'm Pikachu!!!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


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
