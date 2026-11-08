import os, json, requests
from dotenv import load_dotenv

load_dotenv()
FLEET_API = "https://fleet-api.prd.na.vn.cloud.tesla.com"
TOKEN_FILE = "tesla_tokens.json"

def _tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def _refresh():
    reply = requests.post("https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["TESLA_CLIENT_ID"],
        "refresh_token": _tokens()["refresh_token"],
    })
    reply.raise_for_status()
    with open(TOKEN_FILE, "w") as f:
        json.dump(reply.json(), f)

def _get(path):
    for attempt in range(2):
        reply = requests.get(FLEET_API + path, timeout=30,
                             headers={"Authorization": "Bearer " + _tokens()["access_token"]})
        if reply.status_code == 401 and attempt == 0:
            _refresh()
            continue
        return reply

def get_vehicle_data():
    car_id = _get("/api/1/vehicles").json()["response"][0]["id_s"]
    reply = _get(f"/api/1/vehicles/{car_id}/vehicle_data")
    if reply.status_code == 408:
        return {"error": "The car is asleep. Open the Tesla app to wake it, then ask again."}
    if reply.status_code != 200:
        return {"error": f"Tesla returned {reply.status_code}: {reply.text[:200]}"}
    return reply.json()["response"]
