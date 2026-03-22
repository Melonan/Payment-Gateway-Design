from typing import Dict

from fastapi import FastAPI

from payment_gateway_api.bank_client import BankClient
from payment_gateway_api.repository import PaymentsRepository
from payment_gateway_api.routes import router
from payment_gateway_api.service import PaymentService

app = FastAPI()

# create service
repository = PaymentsRepository()
bank_client = BankClient(base_url="http://localhost:8080")
payment_service = PaymentService(repository=repository, bank_client=bank_client)

#  save 'service' to app.state
#  Provided for routing to obtain via dependency injection.
app.state.payment_service = payment_service

# register router
app.include_router(router)


@app.get("/")
async def ping() -> Dict[str, str]:
    return {"app": "payment-gateway-api"}
