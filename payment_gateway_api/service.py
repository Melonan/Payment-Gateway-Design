import uuid
from typing import Optional

from payment_gateway_api.bank_client import BankClient
from payment_gateway_api.models import (
    BankPaymentRequest,
    PaymentStatus,
    PostPaymentRequest,
    PostPaymentResponse,
)
from payment_gateway_api.repository import PaymentsRepository
from payment_gateway_api.validation import validate_payment_request


class PaymentService:
    """biz logic: validate Merchant req -> call bank -> storage -> return"""

    def __init__(self, repository: PaymentsRepository, bank_client: BankClient):
        self._repository = repository
        self._bank_client = bank_client

    def process_payment(self, request: PostPaymentRequest) -> PostPaymentResponse:
        # 1:validate the Merchant Req
        errors = validate_payment_request(request)
        if errors:
            payment = PostPaymentResponse(
                id=uuid.uuid4(),
                status=PaymentStatus.REJECTED,
                last_four_card_digits=request.card_number[-4:] if len(request.card_number) >= 4 else request.card_number,
                expiry_month=request.expiry_month,
                expiry_year=request.expiry_year,
                currency=request.currency,
                amount=request.amount,
            )
            self._repository.add(payment)
            return payment

        # when pass the validation... 

        # 2:build the bank side req
        bank_request = BankPaymentRequest(
            card_number=request.card_number,
            expiry_date=f"{request.expiry_month:02d}/{request.expiry_year}", # match the MM/YYYY
            currency=request.currency,
            amount=request.amount,
            cvv=request.cvv,
        )

        # 3:call bank side
        try:
            bank_response = self._bank_client.process_payment(bank_request)
        except Exception:
            print("BANK SIDE ERROR")
            payment = PostPaymentResponse(
                id=uuid.uuid4(),
                status=PaymentStatus.DECLINED,
                last_four_card_digits=request.card_number[-4:],
                expiry_month=request.expiry_month,
                expiry_year=request.expiry_year,
                currency=request.currency,
                amount=request.amount,
            )
            self._repository.add(payment)
            return payment

        # 4:process bank resp
        status = PaymentStatus.AUTHORIZED if bank_response.authorized else PaymentStatus.DECLINED

        payment = PostPaymentResponse(
            id=uuid.uuid4(),
            status=status,
            last_four_card_digits=request.card_number[-4:],
            expiry_month=request.expiry_month,
            expiry_year=request.expiry_year,
            currency=request.currency,
            amount=request.amount,
        )

        # 5: add the payment to repo
        self._repository.add(payment)
        return payment

    def get_payment(self, payment_id: uuid.UUID) -> Optional[PostPaymentResponse]:
        return self._repository.get(payment_id)
