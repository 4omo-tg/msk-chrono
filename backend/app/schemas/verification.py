from pydantic import BaseModel

class VerificationResponse(BaseModel):
    verified: bool
    message: str
    token: str | None = None
