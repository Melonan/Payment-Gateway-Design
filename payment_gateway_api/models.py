# Data Models for Payment Process Request/Response
from enum import Enum
from uuid import UUID
# inheritate from baseModel, so the requst and resp could create obj from dic
from pydantic import BaseModel 

class PaymentStatus(str, Enum):
    AUTHORIZED = "Authorized"
    DECLINED = "Declined"
    REJECTED = "Rejected"

# The Request Merchant send to US
class PostPaymentRequest(BaseModel):
    """The Request Merchant send to us """
    # here we use str for card number and cvv , not integer
    card_number: str
    expiry_month: int
    expiry_year: int
    currency: str
    amount: int
    cvv: str

# Response return to Merchant
class PostPaymentResponse(BaseModel):
    """The payment result we return to the merchant (also used for GET queries). """
    id: UUID
    status: PaymentStatus
    last_four_card_digits: str
    expiry_month: int
    expiry_year: int
    currency: str
    amount: int

class BankPaymentRequest(BaseModel):
    """request we send to the bank side"""
    card_number: str
    expiry_date: str  #  "MM/YYYY"
    currency: str
    amount: int
    cvv: str

class BankPaymentResponse(BaseModel):
    """response from bank side"""
    authorized: bool
    authorization_code: str
