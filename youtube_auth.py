from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    service = build("youtube", "v3", credentials=creds)
    return service

if __name__ == "__main__":
    print("=== 認証を開始します ===")
    service = get_service()
    print("=== 認証が完了しました ===")
