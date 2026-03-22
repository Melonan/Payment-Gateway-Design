from datetime import datetime
from typing import List

from payment_gateway_api.models import PostPaymentRequest

# we only support several currency currently
ALLOWED_CURRENCIES = {"USD", "CNY", "EUR"}


def validate_payment_request(request: PostPaymentRequest) -> List[str]:
    """
    validation the request fields
    return a error list, if it's empty, the validation passed
    """
    errors = []

    # card num check , should be totaly digits
    if not request.card_number.isdigit() or not (14 <= len(request.card_number) <= 19):
        errors.append("card_number must be 14-19 numeric digits")

    # month check
    if not (1 <= request.expiry_month <= 12):
        errors.append("expiry_month must be between 1 and 12")

    # expiration date check, the combination of month and year must be in the future.
    now = datetime.utcnow()
    if request.expiry_year < now.year or (
        request.expiry_year == now.year and request.expiry_month <= now.month
    ):
        errors.append("Card expiry date must be in the future")

    # cunrrency must be allowed
    if request.currency not in ALLOWED_CURRENCIES:
        errors.append(f"currency must be one of {sorted(ALLOWED_CURRENCIES)}")

    # amount, must be an integer
    if request.amount <= 0:
        errors.append("amount must be a positive integer")

    # CVV
    if not request.cvv.isdigit() or not (3 <= len(request.cvv) <= 4):
        errors.append("cvv must be 3-4 numeric digits")

    return errors
