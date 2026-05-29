"""
Input validation utilities for EthioShop
"""
import re


def normalize_ethiopian_phone(phone: str) -> str:
    """
    Normalize to 10 digits starting with 09 or 07.
    Accepts: 09xxxxxxxx, 07xxxxxxxx, +2519/7..., 2519/7...
    """
    if not phone:
        raise ValueError('Invalid Ethiopian phone number')
    digits = re.sub(r'\D', '', str(phone).strip())
    if digits.startswith('251'):
        digits = '0' + digits[3:]
    if not re.match(r'^(09|07)[0-9]{8}$', digits):
        raise ValueError('Invalid Ethiopian phone number')
    return digits


def validate_ethiopian_phone(phone):
    """
    Validates Ethiopian phone number format.
    Returns: (is_valid, normalized_phone, error_message)
    """
    if not phone:
        return False, None, 'Phone number is required'
    try:
        normalized = normalize_ethiopian_phone(phone)
        return True, normalized, None
    except ValueError:
        return False, None, 'Invalid Ethiopian phone number (use 09xxxxxxxx or 07xxxxxxxx)'


def validate_email(email):
    """
    Basic email validation.
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, 'Email is required'

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, None
    return False, 'Invalid email format'


def validate_price(price, min_value=0):
    """
    Validates price value.
    Returns: (is_valid, error_message)
    """
    try:
        price_float = float(price)
        if price_float < min_value:
            return False, f'Price must be at least {min_value}'
        return True, None
    except (ValueError, TypeError):
        return False, 'Invalid price format'


def validate_stock(stock):
    """
    Validates stock quantity.
    Returns: (is_valid, error_message)
    """
    try:
        stock_int = int(stock)
        if stock_int < 0:
            return False, 'Stock cannot be negative'
        return True, None
    except (ValueError, TypeError):
        return False, 'Invalid stock format'
