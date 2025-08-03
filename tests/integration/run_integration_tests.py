#!/usr/bin/env python3
"""
Test runner for integration tests.

This script runs the integration tests with appropriate configuration
and provides a simple way to execute the complete workflow tests.
"""

import sys
import subprocess
from pathlib import Path

def run_integration_tests():
    """Run integration tests with proper configuration."""
    test_dir = Path(__file__).parent
    
    # Run pytest with integration test configuration
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir / "test_complete_workflow.py"),
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    print("Running integration tests for complete workflow...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, cwd=test_dir.parent.parent)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
    else:
        print("\n" + "=" * 60)
        print("❌ Some integration tests failed!")
        
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_integration_tests())