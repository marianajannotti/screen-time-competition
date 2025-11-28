"""
Input Validation Service for Screen Time Competition App

This module provides comprehensive input validation and sanitization for all
API endpoints. It ensures data integrity, security, and consistent error
handling across the entire application.

Key Features:
- Centralized validation logic for reusability
- Regex-based pattern matching for formats
- Comprehensive error messages for debugging  
- Security-focused input sanitization
- Consistent error response formatting
- Type checking and range validation

Security Benefits:
- Prevents injection attacks through input sanitization
- Validates data types to prevent type confusion attacks
- Enforces length limits to prevent buffer overflow
- Uses whitelist approach for allowed characters
- Provides detailed error messages for debugging

Validation Categories:
- Authentication Data: Username, email, password validation
- Screen Time Data: Minutes, dates, app names validation  
- Goal Data: Target values, goal types validation
- Social Data: Friend requests, usernames validation

Usage Pattern:
    from backend.validation import ValidationService
    
    # Validate required fields
    is_valid, error = ValidationService.validate_required_fields(data, ['username', 'email'])
    if not is_valid:
        return error
    
    # Validate specific formats  
    is_valid, msg = ValidationService.validate_email(email)
    if not is_valid:
        return ValidationService.error_response(msg, 400)
"""

import re
from datetime import datetime, date
from flask import jsonify


class ValidationService:
    """
    Centralized Input Validation Service
    
    Static utility class providing comprehensive validation methods for all
    API inputs. Designed for security, consistency, and ease of use across
    all route handlers.
    
    Design Principles:
    - Fail-safe defaults (reject invalid input)
    - Detailed error messages for debugging
    - Consistent response formatting
    - Security-first approach to input handling
    - Regex patterns for format validation
    """
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """
        Validate that all required fields are present and not empty.
        
        Args:
            data (dict): Input data to validate
            required_fields (list): List of required field names
            
        Returns:
            tuple: (is_valid, error_response)
        """
        if not data:
            return False, ValidationService.error_response("No data provided", 400)
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                return False, ValidationService.error_response(f"Field '{field}' is required", 400)
        
        return True, None
    
    @staticmethod
    def validate_email(email):
        """
        Validate email format.
        
        Args:
            email (str): Email to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        email = email.strip().lower()
        
        if len(email) > 100:
            return False, "Email must be less than 100 characters"
        
        if not ValidationService.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_username(username):
        """
        Validate username format and length.
        
        Args:
            username (str): Username to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not username or not isinstance(username, str):
            return False, "Username is required"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 30:
            return False, "Username must be less than 30 characters"
        
        if not ValidationService.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        
        return True, None
    
    @staticmethod
    def validate_password(password):
        """
        Validate password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password or not isinstance(password, str):
            return False, "Password is required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter:
            return False, "Password must contain at least one letter"
        
        if not has_number:
            return False, "Password must contain at least one number"
        
        return True, None
    
    @staticmethod
    def validate_screen_time_minutes(minutes):
        """
        Validate screen time minutes value.
        
        Args:
            minutes: Screen time value to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if minutes is None:
            return False, "Screen time minutes is required"
        
        if not isinstance(minutes, int):
            return False, "Screen time must be a whole number"
        
        if minutes < 0:
            return False, "Screen time cannot be negative"
        
        if minutes > 1440:  # 24 hours
            return False, "Screen time cannot exceed 24 hours (1440 minutes)"
        
        return True, None
    
    @staticmethod
    def validate_date_string(date_str, field_name="date"):
        """
        Validate date string format and value.
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format
            field_name (str): Name of field for error messages
            
        Returns:
            tuple: (is_valid, parsed_date, error_message)
        """
        if not date_str:
            return False, None, f"{field_name} is required"
        
        if not isinstance(date_str, str):
            return False, None, f"{field_name} must be a string"
        
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, None, f"{field_name} must be in YYYY-MM-DD format"
        
        # Don't allow future dates
        if parsed_date > date.today():
            return False, None, f"{field_name} cannot be in the future"
        
        # Don't allow dates older than 2 years
        if parsed_date < date.today().replace(year=date.today().year - 2):
            return False, None, f"{field_name} cannot be older than 2 years"
        
        return True, parsed_date, None
    
    @staticmethod
    def validate_goal_type(goal_type):
        """
        Validate goal type value.
        
        Args:
            goal_type (str): Goal type to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not goal_type:
            return False, "Goal type is required"
        
        if goal_type not in ["daily", "weekly"]:
            return False, "Goal type must be 'daily' or 'weekly'"
        
        return True, None
    
    @staticmethod
    def validate_goal_target(target_minutes, goal_type):
        """
        Validate goal target minutes.
        
        Args:
            target_minutes: Target value to validate
            goal_type (str): Type of goal for context
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if target_minutes is None:
            return False, "Target minutes is required"
        
        if not isinstance(target_minutes, int):
            return False, "Target minutes must be a whole number"
        
        if target_minutes <= 0:
            return False, "Target minutes must be greater than 0"
        
        # Reasonable limits based on goal type
        if goal_type == "daily":
            if target_minutes > 1440:  # 24 hours
                return False, "Daily target cannot exceed 24 hours (1440 minutes)"
        elif goal_type == "weekly":
            if target_minutes > 10080:  # 7 days * 24 hours * 60 minutes
                return False, "Weekly target cannot exceed 168 hours (10080 minutes)"
        
        return True, None
    
    @staticmethod
    def validate_top_apps(top_apps):
        """
        Validate top apps data structure.
        
        Args:
            top_apps: Top apps data to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if top_apps is None:
            return True, None  # Optional field
        
        if not isinstance(top_apps, list):
            return False, "Top apps must be a list"
        
        if len(top_apps) > 20:
            return False, "Cannot have more than 20 top apps"
        
        total_minutes = 0
        for app in top_apps:
            if not isinstance(app, dict):
                return False, "Each app entry must be an object"
            
            if "name" not in app or "minutes" not in app:
                return False, "Each app must have 'name' and 'minutes' fields"
            
            if not isinstance(app["name"], str) or not app["name"].strip():
                return False, "App name must be a non-empty string"
            
            if len(app["name"]) > 50:
                return False, "App name must be less than 50 characters"
            
            if not isinstance(app["minutes"], int) or app["minutes"] < 0:
                return False, "App minutes must be a non-negative integer"
            
            total_minutes += app["minutes"]
        
        return True, None
    
    @staticmethod
    def validate_pagination_params(page, per_page, max_per_page=100):
        """
        Validate pagination parameters.
        
        Args:
            page: Page number
            per_page: Items per page
            max_per_page (int): Maximum allowed per page
            
        Returns:
            tuple: (is_valid, validated_page, validated_per_page, error_message)
        """
        # Validate page
        if page is not None:
            if not isinstance(page, int) or page < 1:
                return False, None, None, "Page must be a positive integer"
        else:
            page = 1
        
        # Validate per_page
        if per_page is not None:
            if not isinstance(per_page, int) or per_page < 1:
                return False, None, None, "Per page must be a positive integer"
            if per_page > max_per_page:
                return False, None, None, f"Per page cannot exceed {max_per_page}"
        else:
            per_page = 20  # Default
        
        return True, page, per_page, None
    
    @staticmethod
    def error_response(message, status_code=400, details=None):
        """
        Create standardized error response.
        
        Args:
            message (str): Error message
            status_code (int): HTTP status code
            details (dict, optional): Additional error details
            
        Returns:
            tuple: (flask_response, status_code)
        """
        response_data = {
            "error": message,
            "status_code": status_code
        }
        
        if details:
            response_data["details"] = details
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def success_response(data=None, message=None, status_code=200):
        """
        Create standardized success response.
        
        Args:
            data: Response data
            message (str, optional): Success message
            status_code (int): HTTP status code
            
        Returns:
            tuple: (flask_response, status_code)
        """
        response_data = {}
        
        if data is not None:
            response_data["data"] = data
        
        if message:
            response_data["message"] = message
        
        return jsonify(response_data), status_code
