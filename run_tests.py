#!/usr/bin/env python3
"""
Test runner script for all microservices.
Runs unit tests for each service and reports results.
"""
import subprocess
import sys
import os
from pathlib import Path

# Service directories
SERVICES = [
    "user-service",
    "product-service",
    "payment-service",
    "order-service",
    "notification-service",
    "api-gateway"
]

def run_tests(service_dir):
    """Run tests for a specific service."""
    print(f"\n{'='*60}")
    print(f"Running tests for {service_dir}")
    print(f"{'='*60}\n")
    
    service_path = Path(service_dir)
    if not service_path.exists():
        print(f"ERROR: Service directory {service_dir} not found!")
        return False
    
    test_file = service_path / "test_main.py"
    if not test_file.exists():
        print(f"WARNING: No test file found for {service_dir}")
        return True
    
    # Change to service directory and run pytest
    original_dir = os.getcwd()
    try:
        os.chdir(service_path)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_main.py", "-v", "--tb=short"],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR running tests for {service_dir}: {e}")
        return False
    finally:
        os.chdir(original_dir)


def main():
    """Main test runner."""
    print("="*60)
    print("Microservices Unit Test Runner")
    print("="*60)
    
    results = {}
    for service in SERVICES:
        results[service] = run_tests(service)
    
    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}\n")
    
    for service, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{service:30s} {status}")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()


