import logging
import time
import random
from typing import Dict, List, Optional, Union
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Average Calculator API")


MAX_WINDOW_SIZE = 10  
REQUEST_TIMEOUT = 0.5  

class NumberType(str, Enum):
    PRIME = "p"      
    FIBONACCI = "f"  
    EVEN = "e"       
    RANDOM = "r"     

class NumberResponse(BaseModel):
    windowPrevState: List[int] = Field(description="Previous state of the sliding window")
    windowCurrState: List[int] = Field(description="Current state of the sliding window")
    numbers: List[int] = Field(description="New numbers added to the window")
    avg: float = Field(description="Average of the current window")

# TODO: 
URL_MAPPING = {
    NumberType.PRIME: "http://20.244.56.144/evaluation-service/primes",
    NumberType.FIBONACCI: "http://20.244.56.144/evaluation-service/fibo",
    NumberType.EVEN: "http://20.244.56.144/evaluation-service/even",
    NumberType.RANDOM: "http://20.244.56.144/evaluation-service/rand",  
}

AUTH_HEADER = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQ2Nzk2OTUzLCJpYXQiOjE3NDY3OTY2NTMsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6IjEzNzM4MmI5LWMyOTQtNDU5Yy1hMzRkLWM5YzIyODQyODEwOSIsInN1YiI6InNhcnZhZ3lhLjIyMjZjc2UxMDE1QGtpZXQuZWR1In0sImVtYWlsIjoic2FydmFneWEuMjIyNmNzZTEwMTVAa2lldC5lZHUiLCJuYW1lIjoic2FydmFneWEgcHJhZGhhbiIsInJvbGxObyI6IjIyMDAyOTAxMDAxNDMiLCJhY2Nlc3NDb2RlIjoiU3hWZWphIiwiY2xpZW50SUQiOiIxMzczODJiOS1jMjk0LTQ1OWMtYTM0ZC1jOWMyMjg0MjgxMDkiLCJjbGllbnRTZWNyZXQiOiJwRGVKaHlyTk1jeFFLUWFHIn0.xWAWym5B37TiVcdOkOXVcafR-XyEksbE9KnZdCv1RZY"}

USE_MOCK_DATA = True  

number_windows = {
    NumberType.PRIME: [],
    NumberType.FIBONACCI: [],
    NumberType.EVEN: [],
    NumberType.RANDOM: [],
}


def get_test_data(number_type: NumberType) -> List[int]:
    """Generate test data so we don't have to hit the real API during development"""
    if number_type == NumberType.PRIME:
        return random.sample([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47], k=random.randint(1, 5))
    elif number_type == NumberType.FIBONACCI:
        return random.sample([1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144], k=random.randint(1, 5))
    elif number_type == NumberType.EVEN:
        return random.sample([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24], k=random.randint(1, 5))
    else:  
        return random.sample(range(1, 100), k=random.randint(1, 5))


async def get_numbers_from_api(number_type: NumberType) -> Optional[List[int]]:

    if USE_MOCK_DATA:
        logger.info(f"Using test data for {number_type}")
        return get_test_data(number_type)
    
    url = URL_MAPPING[number_type]
    
    try:
        logger.info(f"Calling API: {url}")
        
        async with httpx.AsyncClient() as client:
            start = time.time()
            
            try:
                response = await client.get(
                    url, 
                    timeout=REQUEST_TIMEOUT, 
                    headers=AUTH_HEADER
                )
                elapsed = time.time() - start
                
                logger.info(f"Got response: HTTP {response.status_code} in {elapsed:.2f}s")
                
                if elapsed > REQUEST_TIMEOUT:
                    logger.warning(f"Request took too long: {elapsed:.2f}s")
                    return None
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return None
                    
    
                data = response.json()
                logger.info(f"Got data: {data}")
                return data.get("numbers", [])
                
            except httpx.TimeoutException:
                logger.error(f"Timeout after {time.time() - start:.2f}s")
                return None
            except httpx.RequestError as e:
                logger.error(f"Request failed: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
                
    except Exception as e:
        logger.error(f"Something went wrong: {e}")
        return None


def update_window(type_key: NumberType, new_vals: List[int]) -> tuple:
    current = number_windows[type_key].copy()
    previous = current.copy()
    
    new_additions = []
    for num in new_vals:
        if num not in current:
            new_additions.append(num)
    
    current.extend(new_additions)
    
    if len(current) > MAX_WINDOW_SIZE:
        current = current[-MAX_WINDOW_SIZE:]
    
    number_windows[type_key] = current

    
    return previous, current, new_additions


def calc_avg(numbers: List[int]) -> float:
    """Simple helper to calculate average"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


@app.get("/numbers/{numberid}", response_model=NumberResponse)
async def get_numbers(numberid: NumberType):
    """
    Main endpoint to get numbers, update sliding window, and calculate average.
    """
    logger.info(f"Got request for {numberid}")
    
    try:
        new_numbers = await get_numbers_from_api(numberid)
        
        if new_numbers is None or len(new_numbers) == 0:
            logger.warning(f"No data for {numberid}, using current window")
            window = number_windows[numberid]
            return NumberResponse(
                windowPrevState=window,
                windowCurrState=window,
                numbers=[],
                avg=calc_avg(window)
            )
        
        logger.info(f"Got new numbers for {numberid}: {new_numbers}")
        
        prev, curr, added = update_window(numberid, new_numbers)
        
        average = calc_avg(curr)
        
        logger.info(f"Window update: prev={prev}, curr={curr}, added={added}, avg={average}")
        
        return NumberResponse(
            windowPrevState=prev,
            windowCurrState=curr,
            numbers=added,
            avg=average
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        window = number_windows[numberid]
        return NumberResponse(
            windowPrevState=window,
            windowCurrState=window,
            numbers=[],
            avg=calc_avg(window)
        )
@app.get("/")
async def home():
    """Basic health check"""
    return {"message": "Average Calculator API is running", "status": "OK"}
if __name__ == "__main__":
    import uvicorn
    print("Starting server on port 9876...")
    uvicorn.run(app, host="0.0.0.0", port=9876) 