# API Usage

## Base URL
```url
https://basalt.bundl-spaces.com
```
or (if the server is started locally)
```url
http://localhost:8000
```

## Endpoints

### Generate data
```
POST /generate
```
### Request
**Headers**
```bash 
Content-Type: application/json
```

**Body**
```json
{
  "rows": 3,
  "seed": 42,
  "columns": {
    "client_id": {
      "type": "int",
      "min": 1000,
      "max": 9999,
      "unique": true
    }
  }
}
```
**CURL Example**
```bash 
curl -X 'POST' \
  '{BASE URL}/generate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "rows": 3,
  "seed": 42,
  "columns": {
    "client_id": {
      "type": "int",
      "min": 1000,
      "max": 9999,
      "unique": true
    }
  }
}'
```
**Response**
```json 
{
  "data": [
    {
      "client_id": 1474
    },
    {
      "client_id": 8987
    },
    {
      "client_id": 1346
    }
  ]
}
```

**Note**
> For the same request payload and seed, the response will be **byte-for-byte** identical across runs.


### Health Check
```
GET /health
```
### Request
**Headers**
```bash 
Content-Type: application/json
```

**Response**
```json 
{
  "message": "I'm Pikachu!!!"
}
```

### Error Handling (Example)
**Response**
```json 
{
  "error": "Column 'person': 'values' or 'depends_on' must be specified for string type"
}
```