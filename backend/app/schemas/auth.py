from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization_name: str
    industry: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    organization_id: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse