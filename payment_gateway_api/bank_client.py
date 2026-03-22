import httpx

from payment_gateway_api.models import BankPaymentRequest, BankPaymentResponse


class BankClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self._base_url = base_url

    def process_payment(self, request: BankPaymentRequest) -> BankPaymentResponse:
        with httpx.Client(proxies={}) as client:  # bypass system proxy 
            response = client.post(
                f"{self._base_url}/payments",
                json=request.dict(), # pydantic's dump , transfer the request to dict
            )
        response.raise_for_status()
        return BankPaymentResponse(**response.json())