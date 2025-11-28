"""
Rate Limiting and Security Middleware
Provides request rate limiting and enhanced error handling
"""

from functools import wraps
import time
from collections import defaultdict, deque
from flask import jsonify, request, g
from flask_login import current_user


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self):
        # Store request times per IP/user
        self.requests = defaultdict(deque)
        self.cleanup_interval = 300  # Clean old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def is_rate_limited(self, key, max_requests=100, window_seconds=3600):
        """
        Check if a key (IP or user) is rate limited.
        
        Args:
            key (str): Unique identifier (IP address or user ID)
            max_requests (int): Max requests allowed in window
            window_seconds (int): Time window in seconds
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now - window_seconds)
            self.last_cleanup = now
        
        # Get request queue for this key
        request_queue = self.requests[key]
        
        # Remove requests outside the window
        while request_queue and request_queue[0] < now - window_seconds:
            request_queue.popleft()
        
        # Check if at limit
        if len(request_queue) >= max_requests:
            return True
        
        # Add current request
        request_queue.append(now)
        return False
    
    def _cleanup_old_entries(self, cutoff_time):
        """Remove old entries from all queues."""
        keys_to_delete = []
        
        for key, queue in self.requests.items():
            # Remove old entries
            while queue and queue[0] < cutoff_time:
                queue.popleft()
            
            # Mark empty queues for deletion
            if not queue:
                keys_to_delete.append(key)
        
        # Clean up empty queues
        for key in keys_to_delete:
            del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests=100, window_seconds=3600, per_user=False):
    """
    Rate limiting decorator for Flask routes.
    
    Args:
        max_requests (int): Maximum requests allowed in window
        window_seconds (int): Time window in seconds
        per_user (bool): If True, limit per user; if False, limit per IP
    
    Returns:
        function: Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine the key for rate limiting
            if per_user and hasattr(g, 'current_user') and current_user.is_authenticated:
                key = f"user_{current_user.id}"
            else:
                key = f"ip_{request.remote_addr}"
            
            # Check rate limit
            if rate_limiter.is_rate_limited(key, max_requests, window_seconds):
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {max_requests} per {window_seconds} seconds"
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def standardize_error_response(error_message, status_code=500, details=None):
    """
    Create a standardized error response.
    
    Args:
        error_message (str): Main error message
        status_code (int): HTTP status code
        details (dict): Additional error details
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        "success": False,
        "error": error_message,
        "timestamp": time.time()
    }
    
    if details:
        response["details"] = details
    
    return jsonify(response), status_code


def standardize_success_response(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message (str): Success message
        status_code (int): HTTP status code
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": time.time()
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code
