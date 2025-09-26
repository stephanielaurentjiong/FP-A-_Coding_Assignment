#!/usr/bin/env python3
"""
Test runner for CFO Copilot

Run this script to execute all tests and verify the system is working correctly.
This can be used for the demo video showing "pytest passing".
"""
import sys
import subprocess
import os

def run_tests():
    """Run pytest and display results"""
    print("🧪 CFO COPILOT - RUNNING TESTS")
    print("="*50)

    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",  # verbose
            "--tb=short",  # shorter traceback
            "--color=yes"  # colored output
        ], capture_output=False, text=True)

        if result.returncode == 0:
            print("\n✅ ALL TESTS PASSED!")
            print("🎯 CFO Copilot is ready for demo")
        else:
            print("\n❌ SOME TESTS FAILED")
            print("Check the output above for details")

        return result.returncode

    except FileNotFoundError:
        print("❌ pytest not found. Please install requirements:")
        print("pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)