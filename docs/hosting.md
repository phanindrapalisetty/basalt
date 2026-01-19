## Self Hosting

Want to run it yourself? You already got my appreciation, here's how. 

The project is expected to run on Python 3.10+ and Docker. 

### Clone the reporsitory

```bash
git clone https://github.com/phanindrapalisetty/basalt.git
cd basalt
```

## Local Deployment
### Set up a virtual environment

```bash
python3 -m venv basalt-venv
source basalt-venv/bin/activate (for Mac/Linux)
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run uvicorn AGSI

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Deployment
### Change the Dockerfile
```Docker
FROM python:3.10-slim

WORKDIR /basalt
ADD . .
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build the Docker Image

```bash
docker build --pull --rm -f 'Dockerfile' -t 'basalt:latest' '.'
```

### Run the Docker Container

```bash
docker run --rm -it -p 8000:8000/tcp basalt:latest
```

The API will be available at http://localhost:8000. You can have the Swagger UI at http://localhost:8000/docs.

This [medium article](https://medium.com/@phanindra-palisetty/deploying-a-public-fastapi-on-aws-lambda-using-ecr-and-api-gateway-aaceeaccd04e) can help in deploying to AWS Lambda via API Gateway with predictable costs and minimal operational overhead. 