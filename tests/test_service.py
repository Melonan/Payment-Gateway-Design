import uuid
from unittest.mock import MagicMock

from payment_gateway_api.models import (
    BankPaymentResponse,
    PaymentStatus,
    PostPaymentRequest,
)
from payment_gateway_api.repository import PaymentsRepository
from payment_gateway_api.service import PaymentService


def _make_valid_request() -> PostPaymentRequest:
    """create a valid request"""
    return PostPaymentRequest(
        card_number="12345678901234567",
        expiry_month=12,
        expiry_year=2030,
        currency="USD",
        amount=1000,
        cvv="123",
    )


def _create_service(mock_bank=None) -> tuple:
    """Create PaymentService, return (service, repo, mock_bank)"""
    repo = PaymentsRepository()
    if mock_bank is None:
        mock_bank = MagicMock()
    service = PaymentService(repository=repo, bank_client=mock_bank)
    return service, repo, mock_bank


class TestProcessPayment:

    def test_authorized_payment(self):
        """bank side return: authorized=True -> Authorized"""
        service, repo, mock_bank = _create_service()
        # call mock_back 's process_payment , return this Resp obj
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123", # we dont cared the authoriz code from bank side
        )

        request = _make_valid_request()
        result = service.process_payment(request)

        assert result.status == PaymentStatus.AUTHORIZED
        assert result.last_four_card_digits == "4567"
        assert result.amount == 1000
        assert result.currency == "USD"
        # check only called once 
        mock_bank.process_payment.assert_called_once()

    def test_declined_payment(self):
        """authorized=False -> Declined"""
        service, repo, mock_bank = _create_service()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=False,
            authorization_code="",
        )

        request = _make_valid_request()
        result = service.process_payment(request)

        assert result.status == PaymentStatus.DECLINED
        mock_bank.process_payment.assert_called_once()

    def test_rejected_payment_invalid_card(self):
        """invalid Card Num ->  Rejected, and bank side should not be called"""
        service, repo, mock_bank = _create_service()

        request = PostPaymentRequest(
            card_number="abc",
            expiry_month=12,
            expiry_year=2030,
            currency="USD",
            amount=1000,
            cvv="123",
        )
        result = service.process_payment(request)

        assert result.status == PaymentStatus.REJECTED
        mock_bank.process_payment.assert_not_called()

    def test_bank_error_returns_declined(self):
        """bank trow exception ->  Declined"""
        service, repo, mock_bank = _create_service()
        # set the Exception throwed by mock bank's process_payment method
        mock_bank.process_payment.side_effect = Exception("Bank unavailable")

        request = _make_valid_request()
        result = service.process_payment(request)

        assert result.status == PaymentStatus.DECLINED

    def test_payment_is_stored_after_processing(self):
        """payment stored to repository"""
        service, repo, mock_bank = _create_service()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )

        request = _make_valid_request()
        result = service.process_payment(request)

        stored = repo.get(result.id)
        assert stored is not None
        assert stored.id == result.id
        assert stored.status == PaymentStatus.AUTHORIZED

    def test_last_four_digits_extracted_correctly(self):
        """last 4 digits of card num"""
        service, repo, mock_bank = _create_service()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )
        request = _make_valid_request()
        result = service.process_payment(request)

        assert result.last_four_card_digits == "4567"

    def test_expiry_date_format_sent_to_bank(self):
        """ expiry_date : MM/YYYY"""
        service, repo, mock_bank = _create_service()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )

        request = PostPaymentRequest(
            card_number="12345678901234567",
            expiry_month=3,  # should be fill to "03"
            expiry_year=2028,
            currency="USD",
            amount=100,
            cvv="123",
        )
        service.process_payment(request)

        # check the BankReq
        call_args = mock_bank.process_payment.call_args
        bank_request = call_args[0][0]  # 1st arg param
        assert bank_request.expiry_date == "03/2028"


class TestGetPayment:

    def test_get_existing_payment(self):
        """check valid payment"""
        service, repo, mock_bank = _create_service()
        mock_bank.process_payment.return_value = BankPaymentResponse(
            authorized=True,
            authorization_code="abc-123",
        )

        request = _make_valid_request()
        created = service.process_payment(request)

        result = service.get_payment(created.id)
        assert result is not None
        assert result.id == created.id

    def test_get_nonexistent_payment(self):
        """check invalid payment info"""
        service, repo, mock_bank = _create_service()
        result = service.get_payment(uuid.uuid4())
        assert result is None
