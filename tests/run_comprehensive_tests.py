#!/usr/bin/env python3
"""
Comprehensive test runner for slide-to-image-converter module.

This script runs all tests with proper categorization and reporting,
including unit tests, integration tests, performance tests, and edge cases.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    print(f"Duration: {duration:.2f}s")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for slide-to-image-converter")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--edge-cases", action="store_true", help="Run edge case tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific category is selected
    if not any([args.unit, args.integration, args.performance, args.edge_cases]):
        args.all = True
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])
    
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src/slide_to_image_converter",
            "--cov-report=term-missing"
        ])
        
        if args.html_report:
            pytest_cmd.extend(["--cov-report=html:htmlcov"])
    
    # Test results tracking
    results = {}
    overall_success = True
    
    print("Slide-to-Image-Converter Comprehensive Test Suite")
    print("=" * 60)
    
    # Run unit tests
    if args.unit or args.all:
        cmd = pytest_cmd + [
            "tests/unit/",
            "-m", "not integration and not performance"
        ]
        success = run_command(cmd, "Unit Tests")
        results["Unit Tests"] = success
        overall_success = overall_success and success
    
    # Run integration tests
    if args.integration or args.all:
        cmd = pytest_cmd + [
            "tests/integration/",
            "-m", "integration"
        ]
        success = run_command(cmd, "Integration Tests")
        results["Integration Tests"] = success
        overall_success = overall_success and success
    
    # Run performance tests
    if args.performance or args.all:
        cmd = pytest_cmd + [
            "tests/unit/test_performance_and_memory.py",
            "-m", "performance",
            "-s"  # Show print output for performance stats
        ]
        success = run_command(cmd, "Performance Tests")
        results["Performance Tests"] = success
        overall_success = overall_success and success
    
    # Run edge case tests
    if args.edge_cases or args.all:
        cmd = pytest_cmd + [
            "tests/unit/test_comprehensive_edge_cases.py"
        ]
        success = run_command(cmd, "Edge Case Tests")
        results["Edge Case Tests"] = success
        overall_success = overall_success and success
    
    # Run specific component tests
    if args.all:
        component_tests = [
            ("Markdown Converter Tests", "tests/unit/test_markdown_converter.py"),
            ("HTML Renderer Tests", "tests/unit/test_html_renderer.py"),
            ("Slide Processor Tests", "tests/unit/test_slide_processor.py"),
        ]
        
        for test_name, test_path in component_tests:
            cmd = pytest_cmd + [test_path]
            success = run_command(cmd, test_name)
            results[test_name] = success
            overall_success = overall_success and success
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_category, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_category:<30} {status}")
    
    print("-" * 60)
    overall_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
    print(f"Overall Result: {overall_status}")
    
    if args.coverage and args.html_report:
        print(f"\nCoverage report generated: htmlcov/index.html")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()