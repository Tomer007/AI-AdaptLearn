from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserSettings(BaseModel):
    """User learning settings model."""
    
    pack_name: str = Field(..., description="Name of the learning pack")
    tester_name: str = Field(..., description="Name of the tester/user")
    assessment_date: str = Field(..., description="Date of the assessment (YYYY-MM-DD format)")
    duration: Optional[int] = Field(60, ge=1, description="Duration of assessment in minutes")
    notes: Optional[str] = Field(None, description="Additional notes or preferences")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

