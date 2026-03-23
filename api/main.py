from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.spec_validator import SpecValidator, SpecValidatorException
from core.dataset_generator import generate_dataset
from core.inferrer import infer_spec

app = FastAPI(title="Basalt", version="1.0.0")


@app.get("/health")
async def get_health_status():
    try:
        return JSONResponse(content={"message": "I'm Pikachu!!!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.post("/generate", description="Get a random test data of your choice")
async def generate(pay_load: dict):
    try:
        SpecValidator.validate(pay_load)
        output = generate_dataset(pay_load)
        return JSONResponse(content={"data": output}, status_code=200)
    except SpecValidatorException as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


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
