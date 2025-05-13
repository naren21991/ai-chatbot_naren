from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI()

# Google Sheets setup
SHEET_ID = "1eSdQxobbysym_hS_LumB9RgGwzJeFp1l6ok0eC3U6PQ"
SHEET_NAME = "Sheet1"
SERVICE_ACCOUNT_FILE = "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)


HEADERS = sheet.row_values(1)

# print("Headers from Google Sheet:", HEADERS)

# Ensure the headers match expectation
REQUIRED_HEADERS = [
    "modality", "call_time", "phone_number", "outcome",
    "room", "booking_date", "booking_time", "guests", "summary"
]
if HEADERS != REQUIRED_HEADERS:
    raise Exception("Google Sheet headers do not match expected format.")

# Define payload structure
class BookingData(BaseModel):
    modality: Optional[str] = ""
    call_time: Optional[str] = ""
    phone_number: str  # Keep this required
    outcome: Optional[str] = ""
    room: Optional[str] = ""
    booking_date: Optional[str] = ""
    booking_time: Optional[str] = ""
    guests: Optional[str] = ""
    summary: Optional[str] = ""


class WebhookPayload(BaseModel):
    action: str  # add, update, remove
    booking: Optional[BookingData] = None
    phone_number: Optional[str] = None

def find_row_by_phone(phone_number: str):
    phone_col = sheet.col_values(3)  # "Phone Number" is the 3rd column
    try:
        return phone_col.index(phone_number) + 1
    except ValueError:
        return None

@app.post("/webhook")
def webhook(payload: WebhookPayload):
    action = payload.action.lower()

    if action == "add":
        if not payload.booking:
            raise HTTPException(status_code=400, detail="Missing booking data.")
        if find_row_by_phone(payload.booking.phone_number):
            raise HTTPException(status_code=400, detail="Phone number already exists.")
        row = [
            payload.booking.modality,
            payload.booking.call_time,
            payload.booking.phone_number,
            payload.booking.outcome,
            payload.booking.room,
            payload.booking.booking_date,
            payload.booking.booking_time,
            payload.booking.guests,
            payload.booking.summary
        ]
        sheet.append_row(row)
        return {"message": "Booking added."}

    elif action == "update":
        if not payload.booking:
            raise HTTPException(status_code=400, detail="Missing booking data.")
        row_index = find_row_by_phone(payload.booking.phone_number)
        if not row_index:
            raise HTTPException(status_code=404, detail="Booking not found.")
        row = [
            payload.booking.modality,
            payload.booking.call_time,
            payload.booking.phone_number,
            payload.booking.outcome,
            payload.booking.room,
            payload.booking.booking_date,
            payload.booking.booking_time,
            payload.booking.guests,
            payload.booking.summary
        ]
        sheet.update(f"A{row_index}:I{row_index}", [row])
        return {"message": "Booking updated."}

    elif action == "remove":
        if not payload.phone_number:
            raise HTTPException(status_code=400, detail="Missing phone number.")
        row_index = find_row_by_phone(payload.phone_number)
        if not row_index:
            raise HTTPException(status_code=404, detail="Booking not found.")
        sheet.delete_rows(row_index)
        return {"message": "Booking removed."}

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use add, update, or remove.")


@app.get("/all")
def get_all():
    rows = sheet.get_all_values()[1:]  # Skip header
    bookings = []
    for row in rows:
        if len(row) >= 9:
            bookings.append(dict(zip(REQUIRED_HEADERS, row)))
    return bookings
