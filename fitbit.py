import requests
import json
import datetime
from flask import Flask, request

# Fitbit App credentials
CLIENT_ID = "xxxxxxx"
CLIENT_SECRET = "xxxxxxxxxxx"
REDIRECT_URI = "http://localhost:8000"
AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"

# Settings
DAYS_TO_FETCH = 3
SCOPES = "activity heartrate sleep profile"
OUTPUT_FILE = "fitbit_summary.txt"

app = Flask(__name__)
summary_lines = []

def get_authorization_url():
    return (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={SCOPES.replace(' ', '%20')}&expires_in=604800"
    )

@app.route("/")
def auth_redirect():
    code = request.args.get("code")
    if not code:
        return "❌ Authorization code missing."

    # Get access token
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    if response.status_code != 200:
        return f"❌ Failed to retrieve token: {response.text}"

    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    today = datetime.date.today()

    for i in range(DAYS_TO_FETCH):
        date = today - datetime.timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        summary_lines.append(f"Date: {date_str}")

        # Heart Rate
        hr_url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{date_str}/1d/1min.json"
        hr_resp = requests.get(hr_url, headers=headers)
        hr_data = hr_resp.json()
        hr_count = len(hr_data.get("activities-heart-intraday", {}).get("dataset", []))
        summary_lines.append(f"  Heart Rate: {hr_count} entries")

        # Steps
        steps_url = f"https://api.fitbit.com/1/user/-/activities/steps/date/{date_str}/1d/1min.json"
        steps_resp = requests.get(steps_url, headers=headers)
        steps_data = steps_resp.json()
        steps_count = len(steps_data.get("activities-steps-intraday", {}).get("dataset", []))
        summary_lines.append(f"  Steps: {steps_count} entries")

        # Sleep
        sleep_url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{date_str}.json"
        sleep_resp = requests.get(sleep_url, headers=headers)
        sleep_data = sleep_resp.json()
        sleep_count = len(sleep_data.get("sleep", []))
        summary_lines.append(f"  Sleep: {sleep_count} records\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print(f"\n✅ Data export completed. See '{OUTPUT_FILE}' for results.")
    return "✅ Fitbit data successfully retrieved. You can close this window."

if __name__ == "__main__":
    print("🌐 Fitbit OAuth2 authorization required.")
    print(">> Authorization URL:")
    print(get_authorization_url())
    app.run(port=8000)




