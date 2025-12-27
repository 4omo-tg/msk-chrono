import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login to get token
try:
    auth_resp = requests.post(
        f"{BASE_URL}/login/access-token",
        data={"username": "tester999", "password": "tester999pass"}
    )
    if auth_resp.status_code != 200:
        # Try registering if login fails
        print("Login failed, trying registration...")
        reg_resp = requests.post(
            f"{BASE_URL}/users/open",
            json={"email": "tester_btn@example.com", "password": "password123", "full_name": "Button Tester", "username": "buttontester"}
        )
        if reg_resp.status_code == 200:
            print("Registered 'buttontester'. Logging in...")
            auth_resp = requests.post(
                f"{BASE_URL}/login/access-token",
                data={"username": "buttontester", "password": "password123"}
            )
    
    if auth_resp.status_code != 200:
        print(f"Authentication failed: {auth_resp.text}")
        exit(1)

    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Authenticated successfully.")

    # 2. Get Routes to find an ID
    routes_resp = requests.get(f"{BASE_URL}/routes/", headers=headers)
    routes = routes_resp.json()
    if not routes:
        print("No routes found to start.")
        exit(1)
    
    route_id = routes[0]["id"]
    print(f"Found route ID: {route_id}")

    # 3. Try to start route
    print(f"Attempting to start route {route_id}...")
    start_resp = requests.post(
        f"{BASE_URL}/progress/",
        headers=headers,
        json={"route_id": route_id, "status": "started"}
    )

    print(f"Start Route Response Status: {start_resp.status_code}")
    print(f"Start Route Response Body: {start_resp.text}")

except Exception as e:
    print(f"Error: {e}")
