# bot/utils/validators.py
"""Phone number validation utilities for the bot."""
import re


def normalize_ethiopian_phone(phone: str) -> str:
    """
    Normalize Ethiopian phone number to 09xxxxxxxx or 07xxxxxxxx format.
    
    Accepts:
    - 09xxxxxxxx or 07xxxxxxxx (10 digits)
    - +251xxxxxxxxx (country code)
    - 251xxxxxxxxx (country code without +)
    
    Returns:
    - Normalized 10-digit phone starting with 09 or 07
    
    Raises:
    - ValueError if phone is invalid
    """
    if not phone:
        raise ValueError("Phone number is required")
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle country code formats
    if digits.startswith('251'):
        digits = '0' + digits[3:]
    
    # Validate final format: 09xxxxxxxx or 07xxxxxxxx
    if not re.match(r'^(09|07)[0-9]{8}$', digits):
        raise ValueError("Invalid Ethiopian phone number (must be 09xxxxxxxx or 07xxxxxxxx)")
    
    return digits
