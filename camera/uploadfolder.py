import os
from concurrent.futures import ThreadPoolExecutor

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES      = ["https://www.googleapis.com/auth/drive.file"]
CREDS_FILE  = "credentials.json"
TOKEN_FILE  = "token.json"
FOLDER_NAME = "mushroom-data"


class DriveUploader:
    def __init__(self):
        self._service = None
        self._folder_id = None
        self._authenticate()

    def _authenticate(self):
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        self._service = build("drive", "v3", credentials=creds)
        self._folder_id = self._get_or_create_folder(FOLDER_NAME)

        print(f"[Drive] 초기화 완료 (폴더: {FOLDER_NAME})")

    def _get_or_create_folder(self, name):
        res = self._service.files().list(
            q=f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute()

        files = res.get("files", [])
        if files:
            return files[0]["id"]

        meta = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder"
        }

        folder = self._service.files().create(body=meta, fields="id").execute()
        return folder["id"]

    def upload(self, file_path):
        file_name = os.path.basename(file_path)
        try:
            media = MediaFileUpload(file_path, mimetype="image/jpeg")
            meta = {
                "name": file_name,
                "parents": [self._folder_id]}
            self._service.files().create(body=meta, media_body=media, fields="id").execute()
            print(f"[Drive] 업로드 완료: {file_name}")
        except Exception as e:
            print(f"[Drive] 실패: {file_name} - {e}")

    def upload_folder(self, local_folder, extensions=(".jpg", ".jpeg"), max_workers=1):
        files = sorted([
            os.path.join(local_folder, f)
            for f in os.listdir(local_folder)
            if f.lower().endswith(extensions)
        ])

        print(f"[Drive] 총 {len(files)}개 파일 업로드 시작")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.upload, files)
            
if __name__ == "__main__":
    DriveUploader().upload_folder("captures")
