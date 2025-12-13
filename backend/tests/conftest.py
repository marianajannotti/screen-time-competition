"""Pytest configuration and shared fixtures for all tests.

This file is automatically loaded by pytest and provides
common fixtures and configuration for all test modules.
"""

import pytest
from backend import create_app
from backend.database import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing.
    
    Session-scoped fixture that creates a test application instance
    once per test session.
    """
    app = create_app('testing')
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app.
    
    Function-scoped fixture that provides a fresh test client
    for each test function.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for testing.
    
    Function-scoped fixture that provides a clean database
    session for each test.
    """
    with app.app_context():
        # Clean up any existing data
        _db.session.remove()
        _db.drop_all()
        _db.create_all()
        
        yield _db
        
        # Clean up after test
        _db.session.remove()
        _db.drop_all()
