#!/usr/bin/env python3
"""Simple test runner to validate our test structure works correctly.

This script runs a subset of tests to ensure the testing framework is working
before running the full test suite.
"""
import sys
import os
import unittest
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def create_simple_test():
    """Create a simple test to validate the framework works.
    
    Returns:
        unittest.TestSuite: Simple test suite
    """
    class SimpleTest(unittest.TestCase):
        def test_imports_work(self):
            """Test that basic imports work."""
            try:
                from backend import create_app
                from backend.database import db
                self.assertTrue(True)
            except ImportError as e:
                self.fail(f"Import failed: {e}")
        
        def test_app_creation(self):
            """Test that app can be created."""
            from backend import create_app
            
            app = create_app("testing")
            self.assertIsNotNone(app)
            self.assertEqual(app.config["TESTING"], True)

    suite = unittest.TestSuite()
    suite.addTest(SimpleTest('test_imports_work'))
    suite.addTest(SimpleTest('test_app_creation'))
    return suite

def run_simple_validation():
    """Run simple validation tests.
    
    Returns:
        bool: True if tests pass, False otherwise
    """
    print("Running simple validation tests...")
    print("=" * 50)
    
    suite = create_simple_test()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\nSimple Validation Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("✅ Basic test framework validation PASSED")
    else:
        print("❌ Basic test framework validation FAILED")
        if result.failures:
            print("Failures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("Errors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return success

if __name__ == "__main__":
    # Set environment for testing
    os.environ['FLASK_ENV'] = 'testing'
    
    success = run_simple_validation()
    sys.exit(0 if success else 1)
