from payment_gateway_api.models import PostPaymentRequest
from payment_gateway_api.validation import validate_payment_request


def _make_request(**overrides) -> PostPaymentRequest:
    """
    make a valid request
    override some fields , make it illegal
    """
    defaults = {
        "card_number": "12345678901234567",  # 17 digits, which is valid default
        "expiry_month": 12,
        "expiry_year": 2030,
        "currency": "USD",
        "amount": 1000,
        "cvv": "123",
    }
    defaults.update(overrides)
    return PostPaymentRequest(**defaults)


class TestValidatePaymentRequest:

    # Valid workflow
    def test_valid_request_returns_no_errors(self):
        request = _make_request()
        errors = validate_payment_request(request)
        assert errors == []

    # card number validation
    def test_card_number_too_short(self):
        """ less than 14 digits """
        request = _make_request(card_number="1234567890123")  # 13 
        errors = validate_payment_request(request)
        assert any("card_number" in e for e in errors)

    def test_card_number_too_long(self):
        """ more than 19 digits"""
        request = _make_request(card_number="12345678901234567890")  # 20 
        errors = validate_payment_request(request)
        assert any("card_number" in e for e in errors)

    def test_card_number_contains_letters(self):
        """invalid char, should be all digits"""
        request = _make_request(card_number="1234abcd56789012")
        errors = validate_payment_request(request)
        assert any("card_number" in e for e in errors)

    def test_card_number_14_digits_is_valid(self):
        """valid card num, with 14 digits """
        request = _make_request(card_number="12345678901234")
        errors = validate_payment_request(request)
        assert errors == []


    # month check 
    def test_expiry_month_zero(self):
        """month is 0, illegal"""
        request = _make_request(expiry_month=0)
        errors = validate_payment_request(request)
        assert any("expiry_month" in e for e in errors)

    def test_expiry_month_13(self):
        """month is 13, illegal"""
        request = _make_request(expiry_month=13)
        errors = validate_payment_request(request)
        assert any("expiry_month" in e for e in errors)

    def test_expiry_month_1_is_valid(self):
        """Jan, legal"""
        request = _make_request(expiry_month=1)
        errors = validate_payment_request(request)
        assert not any("expiry_month" in e for e in errors)

    # expiration check
    def test_expiry_in_past_year(self):
        """expired date"""
        request = _make_request(expiry_year=2020, expiry_month=6)
        errors = validate_payment_request(request)
        assert any("future" in e for e in errors)

    def test_expiry_current_month(self):
        """expired month"""
        from datetime import datetime
        now = datetime.utcnow()
        request = _make_request(expiry_year=now.year, expiry_month=now.month)
        errors = validate_payment_request(request)
        assert any("future" in e for e in errors)

    def test_expiry_next_month_is_valid(self):
        """valid date"""
        from datetime import datetime
        now = datetime.utcnow()
        # 计算下个月
        if now.month == 12:
            next_month, next_year = 1, now.year + 1
        else:
            next_month, next_year = now.month + 1, now.year
        request = _make_request(expiry_year=next_year, expiry_month=next_month)
        errors = validate_payment_request(request)
        assert not any("future" in e for e in errors)

    # currency check
    def test_invalid_currency(self):
        """invalid currency"""
        request = _make_request(currency="JPY")
        errors = validate_payment_request(request)
        assert any("currency" in e for e in errors)

    def test_currency_usd_is_valid(self):
        request = _make_request(currency="USD")
        errors = validate_payment_request(request)
        assert not any("currency" in e for e in errors)

    def test_currency_cny_is_valid(self):
        request = _make_request(currency="CNY")
        errors = validate_payment_request(request)
        assert not any("currency" in e for e in errors)

    def test_currency_eur_is_valid(self):
        request = _make_request(currency="EUR")
        errors = validate_payment_request(request)
        assert not any("currency" in e for e in errors)

    def test_currency_lowercase_is_invalid(self):
        """lower case check"""
        request = _make_request(currency="usd")
        errors = validate_payment_request(request)
        assert any("currency" in e for e in errors)

    # amount chek
    def test_amount_zero(self):
        """amount == 0 , invalid"""
        request = _make_request(amount=0)
        errors = validate_payment_request(request)
        assert any("amount" in e for e in errors)

    def test_amount_negative(self):
        """amount < 0, invalid"""
        request = _make_request(amount=-100)
        errors = validate_payment_request(request)
        assert any("amount" in e for e in errors)

    def test_amount_123_is_valid(self):
        """vaild"""
        request = _make_request(amount=123)
        errors = validate_payment_request(request)
        assert not any("amount" in e for e in errors)

    # CVV
    def test_cvv_too_short(self):
        """CVV 2 digits , invalid"""
        request = _make_request(cvv="12")
        errors = validate_payment_request(request)
        assert any("cvv" in e for e in errors)

    def test_cvv_too_long(self):
        """CVV 5 digits, invalid"""
        request = _make_request(cvv="12345")
        errors = validate_payment_request(request)
        assert any("cvv" in e for e in errors)

    def test_cvv_contains_letters(self):
        """CVV contains letter, invalid"""
        request = _make_request(cvv="12a")
        errors = validate_payment_request(request)
        assert any("cvv" in e for e in errors)

    def test_cvv_3_digits_is_valid(self):
        """CVV 3 digit, valid"""
        request = _make_request(cvv="123")
        errors = validate_payment_request(request)
        assert errors == []

    def test_cvv_4_digits_is_valid(self):
        """CVV 4 digits, valid"""
        request = _make_request(cvv="1234")
        errors = validate_payment_request(request)
        assert errors == []

    # multiple errors
    def test_multiple_errors(self):
        """multi errors check"""
        request = _make_request(
            card_number="abc",
            expiry_month=13,
            currency="JPY",
            amount=-1,
            cvv="1",
        )
        errors = validate_payment_request(request)
        assert len(errors) >= 4
