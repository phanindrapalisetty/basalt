FROM public.ecr.aws/lambda/python:3.10

# Copy dependencies first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api ./api
COPY core ./core

# Lambda handler
CMD ["api.lambda_handler.handler"]
