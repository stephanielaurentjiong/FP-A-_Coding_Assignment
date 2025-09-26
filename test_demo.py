#!/usr/bin/env python3
"""
Demo test script for CFO Copilot

This script demonstrates key functionality working correctly.
Perfect for showing in demo videos.
"""
import sys
import os
import traceback

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_core_functionality():
    """Test core CFO Copilot functionality"""
    print("🧪 CFO COPILOT - FUNCTIONALITY DEMO")
    print("="*60)

    tests_passed = 0
    total_tests = 0

    # Test 1: Basic imports work
    total_tests += 1
    print(f"\nTest {total_tests}: Testing imports...")
    try:
        from agent.tools import FinancialTools
        from agent.planner import CFOPlanner
        print("✅ PASS: All modules import successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Import error - {e}")

    # Test 2: Financial tools initialization
    total_tests += 1
    print(f"\nTest {total_tests}: Testing FinancialTools initialization...")
    try:
        tools = FinancialTools()
        print("✅ PASS: FinancialTools loads CSV data successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: FinancialTools init error - {e}")

    # Test 3: Revenue calculation
    total_tests += 1
    print(f"\nTest {total_tests}: Testing revenue calculation...")
    try:
        tools = FinancialTools()
        result = tools.get_revenue('2025-06')
        assert 'error' not in result
        assert 'actual_revenue_usd' in result
        revenue_str = result['actual_revenue_usd']
        assert revenue_str.startswith('$')
        print(f"✅ PASS: Revenue calculation works - {revenue_str}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Revenue calculation error - {e}")

    # Test 4: Gross margin with data quality validation
    total_tests += 1
    print(f"\nTest {total_tests}: Testing gross margin trends with data quality validation...")
    try:
        tools = FinancialTools()
        result = tools.get_gross_margin(last_n_months=3)
        assert 'error' not in result
        assert 'data_quality_warnings' in result
        assert len(result['data_quality_warnings']) > 0
        print(f"✅ PASS: Data quality validation working - {len(result['data_quality_warnings'])} warnings detected")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Gross margin validation error - {e}")

    # Test 5: Cash runway (previously failing)
    total_tests += 1
    print(f"\nTest {total_tests}: Testing cash runway calculation (was failing before)...")
    try:
        tools = FinancialTools()
        result = tools.get_cash_runway()
        assert 'error' not in result
        assert 'runway_months' in result
        runway = result['runway_months']
        print(f"✅ PASS: Cash runway calculation fixed - {runway}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Cash runway error - {e}")

    # Test 6: CFO Planner integration
    total_tests += 1
    print(f"\nTest {total_tests}: Testing CFO Planner integration...")
    try:
        planner = CFOPlanner()
        response = planner.answer_question("What was June 2025 revenue vs budget?")
        assert 'error' not in response
        assert 'response' in response
        assert len(response['response']) > 50
        print("✅ PASS: CFO Planner processes questions correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: CFO Planner error - {e}")

    # Test 7: Data quality alerts in responses
    total_tests += 1
    print(f"\nTest {total_tests}: Testing data quality alerts in responses...")
    try:
        planner = CFOPlanner()
        response = planner.answer_question("Show me gross margin trends for the last 3 months")
        assert 'response' in response
        response_text = response['response']
        assert 'Data Quality Alerts' in response_text
        print("✅ PASS: Data quality alerts appear in user responses")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Data quality alerts error - {e}")

    # Test 8: Sample questions from README
    total_tests += 1
    print(f"\nTest {total_tests}: Testing README sample questions...")
    try:
        planner = CFOPlanner()
        sample_questions = [
            "What was June 2025 revenue vs budget in USD?",
            "Show Gross Margin % trend for the last 3 months.",
            "Break down Opex by category for June.",
            "What is our cash runway right now?"
        ]

        working_questions = 0
        for question in sample_questions:
            try:
                response = planner.answer_question(question)
                if 'error' not in response and 'response' in response:
                    working_questions += 1
            except:
                pass

        assert working_questions == len(sample_questions)
        print(f"✅ PASS: All {len(sample_questions)} README sample questions work correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Sample questions error - {e}")

    # Final results
    print("\n" + "="*60)
    print("🎯 TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")

    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! ✅")
        print("🚀 CFO Copilot is ready for demo")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests failed")
        print("Check the errors above")
        return False

def main():
    """Run the demo tests"""
    try:
        success = test_core_functionality()
        if success:
            print("\n💡 DEMO TIP: Run 'streamlit run app.py' to start the web interface")
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)