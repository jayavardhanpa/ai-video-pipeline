from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret_ai60.json",
    SCOPES
)

creds = flow.run_local_server(port=0)

with open("token_ai60.json", "w") as token:
    token.write(creds.to_json())

print("✅ token_ai60.json generated successfully")