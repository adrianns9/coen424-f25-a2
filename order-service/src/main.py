from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from schemas import OrderCreate, OrderUpdateStatus, OrdersUpdateContact
from order_db import orders_collection
import uuid

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"hello": True}


@app.post("/orders")
async def create_order(payload: OrderCreate):
    order_id = str(uuid.uuid4())
    order_doc = {
        "_id": order_id,
        "user_id": payload.user_id,
        "email": payload.email,
        "delivery_address": payload.delivery_address,
        "items": [item.model_dump() for item in payload.items],
        "status": "processing"
    }

    await orders_collection.insert_one(order_doc)
    return order_doc


@app.get("/orders")
async def get_orders(status: str = Query(None, description="Filter orders by status")):
    query = {"status": status} if status else {}
    orders = await orders_collection.find(query).to_list(100)
    return orders


@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, payload: OrderUpdateStatus):
    existing = await orders_collection.find_one({"_id": order_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    await orders_collection.update_one({"_id": order_id}, {"$set": {"status": payload.status}})
    updated = await orders_collection.find_one({"_id": order_id})
    return updated


@app.put("/orders/contact")
async def update_orders_contact(payload: OrdersUpdateContact):
    # Build update dictionary
    update_data = {}
    if payload.email:
        update_data["email"] = payload.email
    if payload.delivery_address:
        update_data["delivery_address"] = payload.delivery_address

    if not update_data:
        raise HTTPException(status_code=400, detail="No contact info provided")

    # Update all orders for this user_id
    result = await orders_collection.update_many(
        {"user_id": payload.user_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No orders found for this user")

    # Return the updated orders
    updated_orders = await orders_collection.find({"user_id": payload.user_id}).to_list(length=100)
    return {"updated_count": result.modified_count, "orders": updated_orders}
