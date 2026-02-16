import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Set

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ─── Config ───
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "データ")
CUTOFF_HOUR = int(os.environ.get("CUTOFF_HOUR", "18"))
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "service-account-key.json")
JST = timezone(timedelta(hours=9))


# ─── Google Sheets ───
def get_sheets_service():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def get_sheet():
    return get_sheets_service().spreadsheets()


# ─── WebSocket Manager ───
class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict):
        """Send message to ALL connected clients."""
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.discard(ws)


manager = ConnectionManager()


# ─── App ───
app = FastAPI(title="Daily Item Tracker")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ─── Static files served at root for PWA ───
from fastapi.responses import FileResponse

@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

@app.get("/sw.js")
async def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript")

@app.get("/icon-192.png")
async def icon_192():
    return FileResponse("static/icon-192.png", media_type="image/png")

@app.get("/icon-512.png")
async def icon_512():
    return FileResponse("static/icon-512.png", media_type="image/png")


# ─── Models ───
class AddItemRequest(BaseModel):
    action: str = "add"
    item: str


class CheckRequest(BaseModel):
    action: str
    row: int


# ─── HTML ───
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── WebSocket endpoint ───
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; client sends pings
            data = await ws.receive_text()
            # Echo pong to keep alive
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# ─── API: Load items ───
@app.get("/api/load")
async def load_items(date: str):
    try:
        sheet = get_sheet()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E"
        ).execute()
        rows = result.get("values", [])

        items = []
        for i, row in enumerate(rows):
            if i == 0:
                continue
            while len(row) < 5:
                row.append("")
            row_date = row[0][:10] if row[0] else ""
            if row_date == date:
                checked = row[3] in ("済", "TRUE", "true", True)
                items.append({
                    "row": i + 1,
                    "item": row[1],
                    "inputTime": row[2],
                    "checked": checked,
                    "checkedAt": row[4] if checked else ""
                })

        return {"success": True, "items": items}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── API: Add item ───
@app.post("/api/add")
async def add_item(req: AddItemRequest):
    try:
        now = datetime.now(JST)
        target_date = now
        if now.hour >= CUTOFF_HOUR:
            target_date = now + timedelta(days=1)

        date_str = target_date.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        sheet = get_sheet()
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [[date_str, req.item, time_str, "", ""]]}
        ).execute()

        # Broadcast to all clients: reload list
        await manager.broadcast({
            "type": "item_added",
            "date": date_str,
            "item": req.item
        })

        return {"success": True, "date": date_str, "item": req.item}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── API: Check / Uncheck ───
@app.post("/api/check")
async def check_item(req: CheckRequest):
    try:
        sheet = get_sheet()
        now = datetime.now(JST)
        time_str = now.strftime("%H:%M:%S")

        if req.action == "check":
            # Get item name for broadcast
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!B{req.row}"
            ).execute()
            item_name = ""
            vals = result.get("values", [])
            if vals and vals[0]:
                item_name = vals[0][0]

            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!D{req.row}:E{req.row}",
                valueInputOption="RAW",
                body={"values": [["済", time_str]]}
            ).execute()

            # Broadcast: all clients speak + reload
            await manager.broadcast({
                "type": "item_checked",
                "item": item_name,
                "checkedAt": time_str,
                "row": req.row
            })

            return {"success": True, "checkedAt": time_str}

        elif req.action == "uncheck":
            # Get item name for broadcast
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!B{req.row}"
            ).execute()
            item_name = ""
            vals = result.get("values", [])
            if vals and vals[0]:
                item_name = vals[0][0]

            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!D{req.row}:E{req.row}",
                valueInputOption="RAW",
                body={"values": [["", ""]]}
            ).execute()

            # Broadcast: all clients reload
            await manager.broadcast({
                "type": "item_unchecked",
                "item": item_name,
                "row": req.row
            })

            return {"success": True}

        return {"success": False, "error": "Unknown action"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Health ───
@app.get("/health")
async def health():
    return {"status": "ok", "connections": len(manager.active)}
