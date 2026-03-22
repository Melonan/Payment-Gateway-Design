import uuid

from payment_gateway_api.models import (
    BankPaymentRequest,
    BankPaymentResponse,
    PaymentStatus,
    PostPaymentRequest,
    PostPaymentResponse,
)


class TestPaymentStatus:
    def test_authorized_value(self):
        assert PaymentStatus.AUTHORIZED == "Authorized"

    def test_declined_value(self):
        assert PaymentStatus.DECLINED == "Declined"

    def test_rejected_value(self):
        assert PaymentStatus.REJECTED == "Rejected"

    def test_status_is_string(self):
        # PaymentStatus 继承了 str，所以可以直接当字符串用
        assert isinstance(PaymentStatus.AUTHORIZED, str)


class TestPostPaymentRequest:
    def test_create_from_dict(self):
        data = {
            "card_number": "12345678901234",
            "expiry_month": 12,
            "expiry_year": 2030,
            "currency": "USD",
            "amount": 1000,
            "cvv": "123",
        }
        request = PostPaymentRequest(**data)
        assert request.card_number == "12345678901234"
        assert request.expiry_month == 12
        assert request.expiry_year == 2030
        assert request.currency == "USD"
        assert request.amount == 1000
        assert request.cvv == "123"

    def test_serialize_to_dict(self):
        request = PostPaymentRequest(
            card_number="12345678901234",
            expiry_month=6,
            expiry_year=2028,
            currency="CNY",
            amount=500,
            cvv="4567",
        )
        data = request.model_dump()
        assert data["card_number"] == "12345678901234"
        assert data["amount"] == 500


class TestPostPaymentResponse:
    def test_create_response(self):
        payment_id = uuid.uuid4()
        response = PostPaymentResponse(
            id=payment_id,
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="1234",
            expiry_month=12,
            expiry_year=2030,
            currency="USD",
            amount=1000,
        )
        assert response.id == payment_id
        assert response.status == PaymentStatus.AUTHORIZED
        assert response.last_four_card_digits == "1234"

    def test_response_json_contains_status_string(self):
        response = PostPaymentResponse(
            id=uuid.uuid4(),
            status=PaymentStatus.DECLINED,
            last_four_card_digits="5678",
            expiry_month=1,
            expiry_year=2029,
            currency="EUR",
            amount=200,
        )
        json_data = response.model_dump()
        assert json_data["status"] == PaymentStatus.DECLINED


class TestBankPaymentRequest:
    def test_create_bank_request(self):
        request = BankPaymentRequest(
            card_number="2222405343248877",
            expiry_date="04/2025",
            currency="CNY",
            amount=100,
            cvv="123",
        )
        assert request.expiry_date == "04/2025"
        assert request.card_number == "2222405343248877"


class TestBankPaymentResponse:
    def test_authorized_response(self):
        response = BankPaymentResponse(
            authorized=True,
            authorization_code="01107405-6d44-4b50-a14f-7ae0beff13ad",
        )
        assert response.authorized is True
        assert response.authorization_code == "01107405-6d44-4b50-a14f-7ae0beff13ad"

    def test_declined_response(self):
        response = BankPaymentResponse(
            authorized=False,
            authorization_code="",
        )
        assert response.authorized is False
        assert response.authorization_code == ""
