"""Google Drive ingestion source (OAuth user flow)."""

from __future__ import annotations

import io


def list_new_drive_pdfs(
    *,
    folder_id: str,
    token_json_path: str,
    client_secret_path: str,
    seen: dict[str, str],
) -> list[tuple[str, bytes, str]]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        return []

    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(token_json_path, scopes)
    except Exception:
        creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_json_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    files = (
        service.files()
        .list(q=query, fields="files(id,name,modifiedTime,md5Checksum)")
        .execute()
        .get("files", [])
    )

    out: list[tuple[str, bytes, str]] = []
    for file_meta in files:
        file_id = file_meta["id"]
        digest = file_meta.get("md5Checksum") or file_meta.get("modifiedTime", "")
        seen_key = f"gdrive:{file_id}"
        if seen.get(seen_key) == digest:
            continue
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        out.append((file_meta["name"], fh.getvalue(), digest))
    return out
