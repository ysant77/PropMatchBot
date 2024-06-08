from pydantic import BaseModel

class TenantProfile(BaseModel):
    user_id: int
    gender: str
    age: int
    nationality: str
    race: str
    occupation: str
    work_pass: str
    moving_in_date: str
    length_of_stay: str
    budget: str

class SubscriptionRequest(BaseModel):
    user_id: int
    subscription: str

class PaymentRequest(BaseModel):
    user_id: int
    subscription: str
    token: str

class UserProfile(BaseModel):
    user_id: int
    name: str = ""
    subscription: str = "basic"

class PropertySuggestionRequest(BaseModel):
    user_id: int
    subscription: str
