"""SMS notifications router using Twilio."""
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

router = APIRouter(prefix="/api/notifications", tags=["SMS Notifications"])

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")

twilio_client: Optional[TwilioClient] = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class SMSRequest(BaseModel):
    to: str
    message: str

class SMSResponse(BaseModel):
    sid: str
    status: str
    to: str
    from_: str

@router.post("/sms", response_model=SMSResponse)
async def send_sms(request: SMSRequest):
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio not configured")
    if not TWILIO_PHONE_NUMBER:
        raise HTTPException(status_code=503, detail="Twilio phone number not configured")

    try:
        message = twilio_client.messages.create(
            body=request.message,
            from_=TWILIO_PHONE_NUMBER,
            to=request.to
        )
        return SMSResponse(
            sid=message.sid,
            status=str(message.status),
            to=message.to,
            from_=message.from_
        )
    except TwilioRestException as e:
        raise HTTPException(status_code=500, detail=f"Twilio error: {e.msg}")

@router.get("/sms/status/{sid}")
async def check_sms_status(sid: str):
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio not configured")
    try:
        message = twilio_client.messages(sid).fetch()
        return {
            "sid": message.sid,
            "status": str(message.status),
            "date_created": str(message.date_created),
            "date_sent": str(message.date_sent) if message.date_sent else None
        }
    except TwilioRestException as e:
        raise HTTPException(status_code=404, detail=f"Message not found: {e.msg}")

@router.get("/health")
async def twilio_health():
    if not twilio_client:
        return {"status": "not_configured", "account_sid": TWILIO_ACCOUNT_SID or "not set"}
    return {"status": "configured", "account_sid": TWILIO_ACCOUNT_SID}