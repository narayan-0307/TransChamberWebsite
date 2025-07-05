from flask import make_response, request
from datetime import datetime, timedelta
import json

def set_cookie(response, key, value, max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None):
    """
    Set a cookie in the response object
    
    Args:
        response: Flask response object
        key: Cookie name
        value: Cookie value
        max_age: Cookie max age in seconds
        expires: Cookie expiration datetime
        path: Cookie path
        domain: Cookie domain
        secure: Whether cookie should only be sent over HTTPS
        httponly: Whether cookie should be HTTP only
        samesite: SameSite cookie attribute ('Strict', 'Lax', or 'None')
    """
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        expires=expires,
        path=path,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite
    )
    return response

def get_cookie(key, default=None):
    """
    Get a cookie value
    
    Args:
        key: Cookie name
        default: Default value if cookie doesn't exist
    
    Returns:
        Cookie value or default if not found
    """
    value = request.cookies.get(key, default)
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

def get_all_cookies():
    """
    Get all cookie preferences
    Returns a dictionary with all cookie values
    """
    return {
        'necessary': get_cookie('necessary_cookies') == 'true',
        'analytics': get_cookie('analytics_cookies') == 'true',
        'marketing': get_cookie('marketing_cookies') == 'true'
    }

def delete_cookie(response, key, path='/', domain=None):
    """
    Delete a cookie
    
    Args:
        response: Flask response object
        key: Cookie name
        path: Cookie path
        domain: Cookie domain
    """
    response.delete_cookie(key, path=path, domain=domain)
    return response

def create_cookie_response(key, value, max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None):
    """
    Create a response with a cookie
    
    Args:
        key: Cookie name
        value: Cookie value
        max_age: Cookie max age in seconds
        expires: Cookie expiration datetime
        path: Cookie path
        domain: Cookie domain
        secure: Whether cookie should only be sent over HTTPS
        httponly: Whether cookie should be HTTP only
        samesite: SameSite cookie attribute ('Strict', 'Lax', or 'None')
    
    Returns:
        Flask response object with cookie set
    """
    response = make_response()
    return set_cookie(
        response=response,
        key=key,
        value=value,
        max_age=max_age,
        expires=expires,
        path=path,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite
    )

def check_cookie_consent():
    """
    Check if user has given cookie consent
    Returns a dictionary with consent status for each cookie type
    """
    return {
        'necessary': True,  # Always True as it's required
        'analytics': get_cookie('analytics_cookies') == 'true',
        'marketing': get_cookie('marketing_cookies') == 'true'
    }

def set_cookie_consent(response, analytics=False, marketing=False):
    """
    Set cookie consent preferences
    """
    # Set expiration to 1 hour from now
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # Always set necessary cookies
    response = set_cookie(
        response,
        'necessary_cookies',
        'true',
        expires=expires,
        httponly=True
    )
    
    # Set analytics cookies if consented
    if analytics:
        response = set_cookie(
            response,
            'analytics_cookies',
            'true',
            expires=expires,
            httponly=True
        )
    
    # Set marketing cookies if consented
    if marketing:
        response = set_cookie(
            response,
            'marketing_cookies',
            'true',
            expires=expires,
            httponly=True
        )
    
    return response 