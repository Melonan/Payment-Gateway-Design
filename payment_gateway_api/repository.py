from typing import Dict, Optional
from uuid import UUID

from payment_gateway_api.models import PostPaymentResponse


class PaymentsRepository:
    """Paymenet Info Storage in MEM, 
    when the payment result return from bank side, it would be stored"""

    def __init__(self):
        self._payments: Dict[UUID, PostPaymentResponse] = {}

    def add(self, payment: PostPaymentResponse) -> None:
        self._payments[payment.id] = payment

    def get(self, payment_id: UUID) -> Optional[PostPaymentResponse]:
        return self._payments.get(payment_id)
