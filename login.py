import os, json, secrets, webbrowser, requests
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.environ["TESLA_CLIENT_ID"]
CLIENT_SECRET = os.environ["TESLA_CLIENT_SECRET"]
FLEET_API = "https://fleet-api.prd.na.vn.cloud.tesla.com"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "openid offline_access user_data vehicle_device_data vehicle_location"

state = secrets.token_urlsafe(16)
login_url = "https://auth.tesla.com/oauth2/v3/authorize?" + urlencode({
    "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
    "scope": SCOPES, "state": state,
})
print("Opening Tesla login. If no browser opens, copy this link into your browser:")
print(login_url)
webbrowser.open(login_url)

class Catcher(BaseHTTPRequestHandler):
    code = None
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if query.get("state", [""])[0] == state:
            Catcher.code = query.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Done! You can close this tab and go back to Terminal.")
    def log_message(self, *args):
        pass

server = HTTPServer(("localhost", 8080), Catcher)
while Catcher.code is None:
    server.handle_request()

reply = requests.post("https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token", data={
    "grant_type": "authorization_code", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "code": Catcher.code, "audience": FLEET_API, "redirect_uri": REDIRECT_URI,
})
print("Token:", reply.status_code)
if reply.status_code != 200:
    print(reply.text[:500])
    raise SystemExit
with open("tesla_tokens.json", "w") as f:
    json.dump(reply.json(), f)

cars = requests.get(FLEET_API + "/api/1/vehicles",
                    headers={"Authorization": "Bearer " + reply.json()["access_token"]})
print("Vehicles:", cars.status_code)
for car in cars.json().get("response", []):
    print(" -", car.get("display_name"), "| state:", car.get("state"))
