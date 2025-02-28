from pydantic import BaseModel

# Schema for creating a new user
class UserCreate(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True  # Replace orm_mode with from_attributes

# Schema for user response (after creation)
class UserResponse(BaseModel):
    email: str

    class Config:
        from_attributes = True  # Replace orm_mode with from_attributes

# New name for the response schema
class UserOut(BaseModel):
    email: str
    hashed_password: str

    class Config:
        from_attributes = True  # Replace orm_mode with from_attribute

# Schema for login data
class LoginRequest(BaseModel):
    email: str
    password: str

# Schema for response after successful login (contains JWT token)
class Token(BaseModel):
    access_token: str
    token_type: str
