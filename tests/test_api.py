import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from payment_gateway_api.app import app
from payment_gateway_api.models import BankPaymentResponse, PaymentStatus
from payment_gateway_api.repository import PaymentsRepository
from payment_gateway_api.service import PaymentService


def _create_test_client(mock_bank=None) -> TestClient:
    """
    create a Test  Client to mock HTTP req
    """
    repo = PaymentsRepository()
    if mock_bank is None:
        mock_bank = MagicMock()
    service = PaymentService(repository=repo, bank_client=mock_bank)
    app.state.payment_service = service # replace the  'service' in app
    return TestClient(app)


def _valid_payment_body() -> dict:
    """payment req body mock"""
    return {
        "card_number": "12345678901234567",
        "expiry_month": 12,
        "expiry_year": 2030,
        "currency": "USD",
        "amount": 1000,
        "cvv": "123",
    }


class TestPostPayment:
    """ POST /api/payments"""
    #  three STATUS : Authorized;Declined;Rejected

    # Authorized
    def test_authorized_payment_returns_200(self):
        """Bank Authorized -> HTTP 200 + Authorized """
        mock_bank = MagicMock()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )
        client = _create_test_client(mock_bank)

        response = client.post("/api/payments", json=_valid_payment_body())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Authorized"
        assert data["last_four_card_digits"] == "4567"
        assert data["expiry_month"] == 12
        assert data["expiry_year"] == 2030
        assert data["currency"] == "USD"
        assert data["amount"] == 1000
        assert "id" in data

    # Declined
    def test_declined_payment_returns_200(self):
        """Bank decline -> HTTP 200 + Declined """
        mock_bank = MagicMock()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=False,
            authorization_code="",
        )
        client = _create_test_client(mock_bank)

        response = client.post("/api/payments", json=_valid_payment_body())

        assert response.status_code == 200
        assert response.json()["status"] == "Declined"

    def test_bank_error_returns_200_declined(self):
        """bank throw exception -> HTTP 200 + Declined"""
        mock_bank = MagicMock()
        mock_bank.process_payment.side_effect = Exception("Bank down")
        client = _create_test_client(mock_bank)

        response = client.post("/api/payments", json=_valid_payment_body())

        assert response.status_code == 200
        assert response.json()["status"] == "Declined"

    # Rejected --- Request interceped by service 
    def test_rejected_invalid_card_returns_422(self):
        """ illegal card num -> HTTP 422 + Rejected """
        client = _create_test_client()
        body = _valid_payment_body()
        body["card_number"] = "abc"

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"

    def test_rejected_expired_card_returns_422(self):
        """ expiration card -> HTTP 422 + Rejected """
        client = _create_test_client()
        body = _valid_payment_body()
        body["expiry_year"] = 2020
        body["expiry_month"] = 1

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"

    def test_rejected_invalid_currency_returns_422(self):
        """wrong currency -> HTTP 422 + Rejected"""
        client = _create_test_client()
        body = _valid_payment_body()
        body["currency"] = "JPY"

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"

    def test_rejected_invalid_cvv_returns_422(self):
        """CVV wrong -> HTTP 422 + Rejected"""
        client = _create_test_client()
        body = _valid_payment_body()
        body["cvv"] = "1"

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"

    def test_rejected_zero_amount_returns_422(self):
        """amount wrong -> HTTP 422 + Rejected"""
        client = _create_test_client()
        body = _valid_payment_body()
        body["amount"] = 0

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"

    def test_missing_field_returns_422(self):
        """POST with missing required field -> HTTP 422 (FastAPI auto-validation)"""
        client = _create_test_client()
        body = {"card_number": "12345678901234567"}  # missing other fields

        response = client.post("/api/payments", json=body)

        assert response.status_code == 422


class TestGetPayment:
    """ GET /api/payments/{id}"""

    def test_get_existing_payment(self):
        """POST create the payment -> GET the payment"""
        mock_bank = MagicMock()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )
        client = _create_test_client(mock_bank)

        # Create Payment
        post_response = client.post("/api/payments", json=_valid_payment_body())
        payment_id = post_response.json()["id"]

        # Check Payment
        get_response = client.get(f"/api/payments/{payment_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == payment_id
        assert data["status"] == "Authorized"
        assert data["last_four_card_digits"] == "4567"

    def test_get_nonexistent_payment_returns_404(self):
        """check non exist ID -> HTTP 404"""
        client = _create_test_client()
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/payments/{fake_id}")

        assert response.status_code == 404


    def test_get_invalid_id_format_returns_422(self):
        """check invalid ID -> HTTP 422"""
        client = _create_test_client()

        response = client.get("/api/payments/not-a-uuid")

        assert response.status_code == 422
