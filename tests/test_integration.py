"""
E2E test
docker-compose up -d 
run the bank simulator, else this part will be skipped
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from payment_gateway_api.app import app
from payment_gateway_api.bank_client import BankClient
from payment_gateway_api.repository import PaymentsRepository
from payment_gateway_api.service import PaymentService


def _simulator_is_running() -> bool:
    try:
        httpx.get("http://localhost:8080", timeout=2)
        return True
    except Exception:
        return False

def _create_integration_client() -> TestClient:
    """create bank client connect to real bank side"""
    repo = PaymentsRepository()
    bank_client = BankClient(base_url="http://localhost:8080")  
    service = PaymentService(repository=repo, bank_client=bank_client)
    app.state.payment_service = service
    return TestClient(app)

# pytest.mark --- add different marks on the test
requires_simulator = pytest.mark.skipif(
    not _simulator_is_running(),
    reason="Bank simulator is not running (start with: docker-compose up -d)",
)


@requires_simulator
class TestEndToEnd:
    
    # ---- LAST DIGIT TEST ---
    # last digit : odd
    def test_authorized_payment_odd_card(self):
        """last digit odd -> bank accept-> Authorized"""
        client = _create_integration_client()

        response = client.post("/api/payments", json={
            "card_number": "12345678901234567",  # 7 odd
            "expiry_month": 12,
            "expiry_year": 2030,
            "currency": "USD",
            "amount": 1000,
            "cvv": "123",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Authorized"
        assert data["last_four_card_digits"] == "4567"
        assert data["amount"] == 1000

    # last digit : even
    def test_declined_payment_even_card(self):
        """last digit even-> bank decline -> Declined"""
        client = _create_integration_client()

        response = client.post("/api/payments", json={
            "card_number": "12345678901234568",  
            "expiry_month": 6,
            "expiry_year": 2029,
            "currency": "CNY",
            "amount": 500,
            "cvv": "456",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Declined"

    # last digit : 0
    def test_bank_unavailable_card_ending_zero(self):
        """last digit 0 -> bank return 503 -> Declined"""
        client = _create_integration_client()

        response = client.post("/api/payments", json={
            "card_number": "12345678901234560", 
            "expiry_month": 3,
            "expiry_year": 2028,
            "currency": "EUR",
            "amount": 2000,
            "cvv": "789",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Declined"

    # ---- FULL FLOW ----

    def test_full_flow_post_then_get(self):
        client = _create_integration_client()

        # POST 
        post_response = client.post("/api/payments", json={
            "card_number": "12345678901234561",  
            "expiry_month": 9,
            "expiry_year": 2031,
            "currency": "USD",
            "amount": 7500,
            "cvv": "321",
        })

        assert post_response.status_code == 200
        payment_id = post_response.json()["id"]

        # GET the payment info
        get_response = client.get(f"/api/payments/{payment_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == payment_id
        assert data["status"] == "Authorized"
        assert data["last_four_card_digits"] == "4561"
        assert data["expiry_month"] == 9
        assert data["expiry_year"] == 2031
        assert data["currency"] == "USD"
        assert data["amount"] == 7500

    # invalid request -- validation fail
    def test_rejected_payment_not_sent_to_bank(self):
        """Rejected case, return 422 directly"""
        client = _create_integration_client()

        response = client.post("/api/payments", json={
            "card_number": "abc",  # invalid
            "expiry_month": 12,
            "expiry_year": 2030,
            "currency": "USD",
            "amount": 1000,
            "cvv": "123",
        })

        assert response.status_code == 422
        assert response.json()["detail"]["status"] == "Rejected"
