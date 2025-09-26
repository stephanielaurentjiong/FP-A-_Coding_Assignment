"""
Test suite for CFOPlanner class

Tests question classification, intent routing, and response generation
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.planner import CFOPlanner


class TestCFOPlanner:
    """Test suite for CFO question planning and routing"""

    @pytest.fixture
    def planner(self):
        """Create a CFOPlanner instance for testing"""
        return CFOPlanner()

    def test_revenue_question_classification(self, planner):
        """Test classification of revenue-related questions"""
        test_cases = [
            ("What was June 2025 revenue vs budget?", "revenue", "2025-06", True),
            ("Show me revenue for June", "revenue", "2025-06", False),
            ("Revenue in 2025-06", "revenue", "2025-06", False),
        ]

        for question, expected_intent, expected_month, expected_vs_budget in test_cases:
            classification = planner.classify_question(question)

            assert classification['intent'] == expected_intent
            assert classification['month'] == expected_month
            assert classification['vs_budget'] == expected_vs_budget

    def test_margin_trend_classification(self, planner):
        """Test classification of margin trend questions"""
        test_cases = [
            ("Show me gross margin trends for the last 3 months", "margin", True, 3),
            ("Gross margin trend last 6 months", "margin", True, 6),
            ("Show gross margin for last year", "margin", True, 12),
        ]

        for question, expected_intent, expected_trend, expected_months in test_cases:
            classification = planner.classify_question(question)

            assert classification['intent'] == expected_intent
            assert classification['trend_analysis'] == expected_trend
            assert classification['trend_months'] == expected_months

    def test_sample_questions_from_readme(self, planner):
        """Test the specific sample questions mentioned in the README"""
        sample_questions = [
            "What was June 2025 revenue vs budget in USD?",
            "Show Gross Margin % trend for the last 3 months.",
            "Break down Opex by category for June.",
            "What is our cash runway right now?"
        ]

        for question in sample_questions:
            response = planner.answer_question(question)

            # All sample questions should work without errors
            assert 'error' not in response
            assert 'response' in response

            # Response should be substantial (not empty)
            assert len(response['response']) > 50

    def test_revenue_vs_budget_response(self, planner):
        """Test revenue vs budget question handling"""
        question = "What was June 2025 revenue vs budget in USD?"
        response = planner.answer_question(question)

        assert 'error' not in response
        assert 'response' in response
        assert 'data' in response

        # Response should mention key elements
        response_text = response['response']
        assert 'Revenue Analysis' in response_text
        assert 'Actual Revenue' in response_text
        assert '2025-06' in response_text or 'June' in response_text

    def test_gross_margin_trend_response(self, planner):
        """Test gross margin trend question handling"""
        question = "Show Gross Margin % trend for the last 3 months."
        response = planner.answer_question(question)

        assert 'error' not in response
        assert 'response' in response
        assert 'data' in response

        response_text = response['response']
        assert 'Gross Margin Trend' in response_text
        assert 'Average Margin' in response_text

        # Should include data quality warnings due to test data
        assert 'Data Quality Alerts' in response_text

    def test_opex_breakdown_response(self, planner):
        """Test OpEx breakdown question handling"""
        question = "Break down Opex by category for June."
        response = planner.answer_question(question)

        assert 'error' not in response
        assert 'response' in response
        assert 'data' in response

        response_text = response['response']
        assert 'OpEx Breakdown' in response_text
        assert 'Total OpEx' in response_text

    def test_cash_runway_response(self, planner):
        """Test cash runway question handling (previously failing)"""
        question = "What is our cash runway right now?"
        response = planner.answer_question(question)

        # This should now work without the NaT strftime error
        assert 'error' not in response
        assert 'response' in response
        assert 'data' in response

        response_text = response['response']
        assert 'Cash Runway Analysis' in response_text
        assert 'Current Cash' in response_text
        assert 'Monthly Burn Rate' in response_text

    def test_unknown_question_handling(self, planner):
        """Test handling of unrecognized questions"""
        unknown_questions = [
            "What is the meaning of life?",
            "How do I cook pasta?",
            "Can you help me with derivatives trading?",
        ]

        for question in unknown_questions:
            response = planner.answer_question(question)

            # Should provide helpful response for unknown questions
            assert 'response' in response
            response_text = response['response']
            assert "I can help with" in response_text or "Try asking" in response_text

    def test_date_extraction_edge_cases(self, planner):
        """Test edge cases in date extraction"""
        test_cases = [
            ("Revenue for June 2025", "2025-06"),
            ("Show me data for 2025-06", "2025-06"),
            ("What about June?", "2025-06"),  # Should default to current year
            ("Revenue for last month", None),  # No specific date
        ]

        for question, expected_month in test_cases:
            classification = planner.classify_question(question)
            assert classification['month'] == expected_month

    def test_confidence_scoring(self, planner):
        """Test confidence scoring in question classification"""
        # High confidence questions
        high_confidence = [
            "What was revenue for June 2025?",
            "Show me gross margin trends",
            "Cash runway analysis"
        ]

        for question in high_confidence:
            classification = planner.classify_question(question)
            assert classification['confidence'] > 0.5

        # Low confidence questions
        low_confidence = [
            "How are we doing?",
            "What's the status?",
            "Can you help?"
        ]

        for question in low_confidence:
            classification = planner.classify_question(question)
            # These might still get classified but with lower confidence
            # or as unknown intent
            assert classification['intent'] is not None

    def test_data_quality_warnings_in_responses(self, planner):
        """Test that data quality warnings are properly included in responses"""
        # Questions that should trigger data quality warnings
        questions_with_warnings = [
            "Show me gross margin trends for the last 6 months",
            "What's our EBITDA trend for the last year?",
        ]

        for question in questions_with_warnings:
            response = planner.answer_question(question)

            assert 'response' in response
            response_text = response['response']

            # Should include data quality alerts
            assert 'Data Quality Alerts' in response_text
            assert '⚠️' in response_text