# schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class LatDirection(str, Enum):
    N = "N"
    S = "S"

class LongDirection(str, Enum):
    E = "E"
    W = "W"

class MessageSender(str, Enum):
    USER = "user"
    AI = "ai"

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = Field(None, max_length=100)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    farm_size: Optional[str] = Field(None, max_length=50)
    crop_type: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    lat_direction: Optional[LatDirection] = None
    long_direction: Optional[LongDirection] = None
    address: Optional[str] = Field(None, max_length=500)

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    farm_size: Optional[str]
    crop_type: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    lat_direction: Optional[str]
    long_direction: Optional[str]
    address: Optional[str]
    created_at: str
    updated_at: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

# Message Schemas
class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    sender: MessageSender

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    text: str
    sender: str
    created_at: str
    metadata: Optional[dict] = None

# Chat Session Schemas
class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field("New Chat", max_length=200)

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)

class ChatSessionResponse(BaseModel):
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    messages: List[MessageResponse] = []

# Chat Request
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    weather_temp: Optional[float] = None
    weather_condition: Optional[str] = Field(None, max_length=100)
    weather_humidity: Optional[int] = Field(None, ge=0, le=100)
    context_data: Optional[dict] = None

class ChatResponse(BaseModel):
    session_id: str
    user_message: MessageResponse
    ai_message: MessageResponse

# Pagination
class PaginationParams(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    last_evaluated_key: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    last_evaluated_key: Optional[str] = None
    count: int

# Error Response
class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None