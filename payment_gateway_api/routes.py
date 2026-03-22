from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from payment_gateway_api.models import PostPaymentRequest, PostPaymentResponse, PaymentStatus
from payment_gateway_api.service import PaymentService


router = APIRouter()


def get_payment_service(request: Request) -> PaymentService:
    """ app.state get PaymentService instance(dependency injection)"""
    return request.app.state.payment_service


@router.post("/api/payments", response_model=PostPaymentResponse)
def post_payment(
    payment_request: PostPaymentRequest,
    service: PaymentService = Depends(get_payment_service), # get the payment_service to service befor biz logic
):
    # ---- POST THE REQUEST!!! ----
    result = service.process_payment(payment_request)

    if result.status == PaymentStatus.REJECTED:
        raise HTTPException(
            status_code=422,  # Unprocessable Entity , format is correct, could not be processed
            detail=result.model_dump(mode="json")
        )

    return result


@router.get("/api/payments/{payment_id}", response_model=PostPaymentResponse)
def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
):
    result = service.get_payment(payment_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    return result
