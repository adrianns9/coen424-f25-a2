import os
import random
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# User service URLs
USER_V1 = os.getenv("USER_V1")
USER_V2 = os.getenv("USER_V2")
P = float(os.getenv("P", 0.5))

# Order service URL
ORDER_SERVICE = os.getenv("ORDER_SERVICE")


def pick_user_service():
    """Return URL of v1 or v2 based on probability P."""
    return USER_V1 if random.random() < P else USER_V2


app = FastAPI()


async def forward_request(method: str, url: str, json: dict = None, params: dict = None):
    """Forward an HTTP request to a microservice with error handling."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.request(method, url, json=json, params=params)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(content={"error": "Microservice unavailable"}, status_code=503)
    except httpx.ReadTimeout:
        return JSONResponse(content={"error": "Microservice timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------
# User Microservices
# ----------------------
@app.post("/users")
async def create_user(request: Request):
    service = pick_user_service()
    forward_body = await request.json()
    return await forward_request("POST", f"{service}/users", json=forward_body)


@app.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    service = pick_user_service()
    forward_body = await request.json()
    return await forward_request("PUT", f"{service}/users/{user_id}", json=forward_body)


# ----------------------
# Order Microservices
# ----------------------
@app.post("/orders")
async def create_order(request: Request):
    forward_body = await request.json()
    return await forward_request("POST", f"{ORDER_SERVICE}/orders", json=forward_body)


@app.get("/orders")
async def get_orders(status: str = None):
    params = {"status": status} if status else {}
    return await forward_request("GET", f"{ORDER_SERVICE}/orders", params=params)


@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, request: Request):
    forward_body = await request.json()
    return await forward_request("PUT", f"{ORDER_SERVICE}/orders/{order_id}/status", json=forward_body)


@app.put("/orders/contact")
async def update_order_contact(request: Request):
    forward_body = await request.json()
    return await forward_request("PUT", f"{ORDER_SERVICE}/orders/contact", json=forward_body)
