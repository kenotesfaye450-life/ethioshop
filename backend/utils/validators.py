"""
Input validation utilities for EthioShop
"""
import re


def validate_ethiopian_phone(phone):
    """
    Validates Ethiopian phone number format.
    Accepts: +251[97]XXXXXXXX, 251[97]XXXXXXXX, or 0[97]XXXXXXXX
    Returns: (is_valid, normalized_phone, error_message)
    """
    if not phone:
        return False, None, "Phone number is required"
    
    # Remove spaces and dashes
    phone = phone.strip().replace(' ', '').replace('-', '')
    
    # Pattern 1: +251[97]XXXXXXXX
    if phone.startswith('+251'):
        if len(phone) == 13 and phone[4] in ['9', '7']:
            return True, phone, None
        return False, None, "Invalid Ethiopian phone format (must be +251[97]XXXXXXXX)"
    
    # Pattern 2: 251[97]XXXXXXXX
    if phone.startswith('251'):
        if len(phone) == 12 and phone[3] in ['9', '7']:
            return True, '+' + phone, None
        return False, None, "Invalid Ethiopian phone format (must be 251[97]XXXXXXXX)"
    
    # Pattern 3: 0[97]XXXXXXXX
    if phone.startswith('0'):
        if len(phone) == 10 and phone[1] in ['9', '7']:
            return True, '+251' + phone[1:], None
        return False, None, "Invalid Ethiopian phone format (must be 0[97]XXXXXXXX)"
    
    return False, None, "Invalid phone number format"


def validate_email(email):
    """
    Basic email validation.
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, None
    return False, "Invalid email format"


def validate_price(price, min_value=0):
    """
    Validates price value.
    Returns: (is_valid, error_message)
    """
    try:
        price_float = float(price)
        if price_float < min_value:
            return False, f"Price must be at least {min_value}"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid price format"


def validate_stock(stock):
    """
    Validates stock quantity.
    Returns: (is_valid, error_message)
    """
    try:
        stock_int = int(stock)
        if stock_int < 0:
            return False, "Stock cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid stock format"
