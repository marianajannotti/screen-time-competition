#!/usr/bin/env python3
"""Test runner script for the backend test suite.

This script provides a convenient way to run all backend tests with various options
for filtering, coverage reporting, and output formatting.
"""
import unittest
import sys
import os
import argparse
from pathlib import Path

# Add project root to Python path for backend module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment for testing
os.environ['FLASK_ENV'] = 'testing'

def run_unit_tests():
    """Run all unit tests.
    
    Returns:
        unittest.TestResult: Test results
    """
    print("Running Unit Tests...")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover and add unit tests
    unit_tests_dir = Path(__file__).parent / "unit"
    unit_suite = loader.discover(str(unit_tests_dir), pattern="test_*.py")
    suite.addTests(unit_suite)
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    return runner.run(suite)


def run_integration_tests():
    """Run all integration tests.
    
    Returns:
        unittest.TestResult: Test results
    """
    print("Running Integration Tests...")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover and add integration tests
    integration_tests_dir = Path(__file__).parent / "integration"
    integration_suite = loader.discover(str(integration_tests_dir), pattern="test_*.py")
    suite.addTests(integration_suite)
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    return runner.run(suite)


def run_all_tests():
    """Run all unit and integration tests.
    
    Returns:
        tuple: (unit_results, integration_results)
    """
    print("Running All Backend Tests...")
    print("=" * 50)
    
    unit_results = run_unit_tests()
    print("\n" + "=" * 50)
    integration_results = run_integration_tests()
    
    return unit_results, integration_results


def run_specific_test(test_pattern):
    """Run tests matching a specific pattern.
    
    Args:
        test_pattern (str): Pattern to match test files or test methods
        
    Returns:
        unittest.TestResult: Test results
    """
    print(f"Running tests matching pattern: {test_pattern}")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover tests in both unit and integration directories
    tests_dir = Path(__file__).parent
    discovered_suite = loader.discover(str(tests_dir), pattern=test_pattern)
    suite.addTests(discovered_suite)
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    return runner.run(suite)


def print_test_summary(unit_results=None, integration_results=None, single_result=None):
    """Print a summary of test results.
    
    Args:
        unit_results (unittest.TestResult): Unit test results
        integration_results (unittest.TestResult): Integration test results  
        single_result (unittest.TestResult): Single test run results
    """
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    if single_result:
        results = [("All Tests", single_result)]
    else:
        results = []
        if unit_results:
            results.append(("Unit Tests", unit_results))
        if integration_results:
            results.append(("Integration Tests", integration_results))
    
    for test_type, result in results:
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
        
        total_tests += tests_run
        total_failures += failures
        total_errors += errors
        total_skipped += skipped
        
        print(f"\n{test_type}:")
        print(f"  Tests run: {tests_run}")
        print(f"  Failures: {failures}")
        print(f"  Errors: {errors}")
        print(f"  Skipped: {skipped}")
        
        if failures > 0:
            print(f"  Failed tests:")
            for test, traceback in result.failures:
                print(f"    - {test}")
        
        if errors > 0:
            print(f"  Error tests:")
            for test, traceback in result.errors:
                print(f"    - {test}")
    
    print(f"\nOVERALL SUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Total failures: {total_failures}")
    print(f"  Total errors: {total_errors}")
    print(f"  Total skipped: {total_skipped}")
    
    success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"  Success rate: {success_rate:.1f}%")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total_failures + total_errors} TESTS FAILED")
        return False


def main():
    """Main entry point for the test runner.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Run backend tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--pattern", 
        help="Run tests matching this pattern (e.g., test_auth_*.py)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Increase verbosity"
    )
    
    args = parser.parse_args()
    
    try:
        if args.pattern:
            result = run_specific_test(args.pattern)
            success = print_test_summary(single_result=result)
        elif args.type == "unit":
            result = run_unit_tests()
            success = print_test_summary(single_result=result)
        elif args.type == "integration":
            result = run_integration_tests()
            success = print_test_summary(single_result=result)
        else:  # all
            unit_results, integration_results = run_all_tests()
            success = print_test_summary(unit_results, integration_results)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
