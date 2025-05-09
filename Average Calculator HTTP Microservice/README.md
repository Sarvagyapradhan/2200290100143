# Average Calculator API

A FastAPI application that fetches different types of numbers, maintains sliding windows, and calculates averages.

## Features

- Fetches four types of numbers (Prime, Fibonacci, Even, Random)
- Maintains a sliding window of the last 10 unique numbers for each type
- Calculates the average of numbers in each window
- Handles timeouts and errors gracefully

## API Endpoints

- `GET /numbers/{numberid}` - Get numbers and average
  - `numberid` can be:
    - `p` - Prime numbers
    - `f` - Fibonacci numbers
    - `e` - Even numbers
    - `r` - Random numbers
  
- `GET /` - Health check endpoint

## Response Format

```json
{
  "windowPrevState": [2, 4],
  "windowCurrState": [2, 4, 6, 8],
  "numbers": [6, 8],
  "avg": 5.0
}
```

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 9876
```

Or simply run:

```bash
python main.py
```

## API Documentation

When the server is running, you can access:
- Swagger UI: http://localhost:9876/docs
- ReDoc: http://localhost:9876/redoc

## Testing

You can test the API using curl or any API client:

```bash
curl http://localhost:9876/numbers/e
``` 