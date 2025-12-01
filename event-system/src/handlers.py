import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# URL of the Order Microservice
ORDER_SERVICE = os.getenv("ORDER_SERVICE", "http://order-service:8000")


async def handle_user_contact_updated(body: bytes):
    """
    Handles the 'user.contact.updated' event from the User Microservice.
    Calls the Order Microservice to update all orders for the user.

    Example event:
    {
       "event_id": "...",
       "type": "user.contact.updated",
       "user_id": "...",
       "email": "...",
       "delivery_address": "...",
       "version": "v1"
    }
    """
    event = json.loads(body.decode())
    print("\n--- Received Event ---")
    print(event)
    print("----------------------\n")

    user_id = event.get("user_id")
    email = event.get("email")
    delivery_address = event.get("delivery_address")

    if not user_id:
        print("No user_id found in event. Skipping update.")
        return

    # Call the Order Microservice to update contact info
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.put(
                f"{ORDER_SERVICE}/orders/contact",
                json={
                    "user_id": user_id,
                    "email": email,
                    "delivery_address": delivery_address
                }
            )
            if resp.status_code == 200:
                print(f"Successfully updated orders for user_id={user_id}")
            else:
                print(f"Failed to update orders for user_id={user_id}: {resp.status_code} {resp.text}")
        except httpx.RequestError as e:
            print(f"Error communicating with Order Microservice: {e}")
