from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset, generate_multi_dataset

app = FastAPI(title="Basalt", version="1.0.0")


@app.get("/health")
async def get_health_status(description="Stay healthy"):
    try:
        return JSONResponse(content={"message": "I'm Pikachu!!!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.post("/generate", description="Get a random test data of your choice")
async def generate(pay_load:dict):
    try:
        validate = SpecValidator.validate(pay_load)
        output = generate_dataset(pay_load)
        return JSONResponse(content={"data": output}, status_code=200)
    except SpecValidatorException as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/generate/multi", description="Generate multiple named datasets from a single global seed")
async def generate_multi(pay_load: dict):
    try:
        SpecValidator.validate_multi(pay_load)
        output = generate_multi_dataset(pay_load)
        return JSONResponse(content={"data": output}, status_code=200)
    except SpecValidatorException as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
