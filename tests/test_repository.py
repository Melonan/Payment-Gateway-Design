import uuid

from payment_gateway_api.models import PaymentStatus, PostPaymentResponse
from payment_gateway_api.repository import PaymentsRepository


class TestPaymentsRepository:
    """Test Payment Repo"""

    def test_add_and_get_payment(self):
        """fetch a resp from repo"""
        repo = PaymentsRepository()
        payment_id = uuid.uuid4()

        payment = PostPaymentResponse(
            id=payment_id,
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="4242",
            expiry_month=12,
            expiry_year=2030,
            currency="USD",
            amount=1000,
        )

        repo.add(payment)
        result = repo.get(payment_id)

        assert result is not None
        assert result.id == payment_id
        assert result.status == PaymentStatus.AUTHORIZED
        assert result.amount == 1000
        assert result.expiry_year == 2023

    def test_get_nonexistent_payment_returns_none(self):
        """get a nonexist resp"""
        repo = PaymentsRepository()
        result = repo.get(uuid.uuid4())
        assert result is None

    def test_add_multiple_payments(self):
        """fetch multiple resp from repo"""
        repo = PaymentsRepository()

        payment1 = PostPaymentResponse(
            id=uuid.uuid4(),
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="1111",
            expiry_month=6,
            expiry_year=2028,
            currency="CNY",
            amount=500,
        )
        payment2 = PostPaymentResponse(
            id=uuid.uuid4(),
            status=PaymentStatus.DECLINED,
            last_four_card_digits="2222",
            expiry_month=3,
            expiry_year=2029,
            currency="EUR",
            amount=2000,
        )

        repo.add(payment1)
        repo.add(payment2)

        assert repo.get(payment1.id).amount == 500
        assert repo.get(payment2.id).amount == 2000
