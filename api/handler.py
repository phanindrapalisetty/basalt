from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json

app = FastAPI()


@app.get("/health")
async def get_health_status(description="Stay healthy"):
    try:
        return {"statuscode": 200, "message": "I'm healthy!"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.post("/generate", description="Get a random test data of your choice")
async def generate():
    try:
        return {"statuscode": 200, "message": "I'm Pikachu!!!"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
