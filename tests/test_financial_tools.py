"""
Test suite for FinancialTools class

Tests core financial calculations and data processing
"""
import pytest
import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.tools import FinancialTools


class TestFinancialTools:
    """Test suite for financial calculations and data quality validation"""

    @pytest.fixture
    def financial_tools(self):
        """Create a FinancialTools instance for testing"""
        return FinancialTools()

    def test_revenue_calculation_june_2025(self, financial_tools):
        """Test revenue calculation for a specific month"""
        result = financial_tools.get_revenue('2025-06')

        # Should return valid result without errors
        assert 'error' not in result
        assert 'actual_revenue_usd' in result
        assert 'month' in result

        # Revenue should be a properly formatted string
        revenue_str = result['actual_revenue_usd']
        assert revenue_str.startswith('$')
        assert ',' in revenue_str  # Should have comma formatting

        # Extract numeric value and verify it's reasonable
        revenue_value = float(revenue_str.replace('$', '').replace(',', ''))
        assert revenue_value > 0
        assert revenue_value > 500000  # Should be substantial for a business

    def test_revenue_vs_budget(self, financial_tools):
        """Test revenue vs budget comparison"""
        result = financial_tools.get_revenue('2025-06', vs_budget=True)

        assert 'error' not in result
        assert 'actual_revenue_usd' in result
        assert 'budget_revenue_usd' in result or 'budget_note' in result

        if 'budget_revenue_usd' in result:
            assert 'variance_usd' in result
            assert 'variance_percent' in result

            # Variance should be properly formatted
            variance_pct = result['variance_percent']
            assert '%' in variance_pct

    def test_gross_margin_calculation(self, financial_tools):
        """Test gross margin calculation and data quality validation"""
        result = financial_tools.get_gross_margin('2025-06')

        # Should return valid result
        assert 'error' not in result
        assert 'gross_margin_percent' in result

        # Margin should be a reasonable percentage
        margin = result['gross_margin_percent']
        assert isinstance(margin, (int, float))
        assert 0 <= margin <= 100

        # Should have formatted values
        assert 'revenue_formatted' in result
        assert 'cogs_formatted' in result
        assert 'gross_profit_formatted' in result

    def test_gross_margin_trend_with_validation(self, financial_tools):
        """Test gross margin trend analysis with data quality validation"""
        result = financial_tools.get_gross_margin(last_n_months=3)

        # Should return valid trend data
        assert 'error' not in result
        assert 'trend_months' in result
        assert 'data' in result
        assert 'summary' in result

        # Should have exactly 3 months of data
        assert result['trend_months'] == 3
        assert len(result['data']) == 3

        # With our test data, should trigger data quality warnings
        assert 'data_quality_warnings' in result
        assert len(result['data_quality_warnings']) > 0

        # Should have statistical analysis
        assert 'statistics' in result
        stats = result['statistics']
        assert 'mean' in stats
        assert 'std_dev' in stats
        assert 'range' in stats

    def test_opex_breakdown(self, financial_tools):
        """Test operating expense breakdown"""
        result = financial_tools.get_opex_breakdown('2025-06')

        assert 'error' not in result
        assert 'breakdown_by_category' in result
        assert 'total_opex_usd' in result

        # Should have OpEx categories
        categories = result['breakdown_by_category']
        assert len(categories) > 0

        for category in categories:
            assert 'category' in category
            assert 'amount_usd' in category
            assert 'percentage' in category

            # Percentage should be properly formatted
            assert '%' in category['percentage']

    def test_ebitda_calculation(self, financial_tools):
        """Test EBITDA calculation"""
        result = financial_tools.get_ebitda('2025-06')

        assert 'error' not in result
        assert 'ebitda_formatted' in result
        assert 'ebitda_margin_percent' in result

        # Should have calculation breakdown
        assert 'calculation_breakdown' in result
        breakdown = result['calculation_breakdown']
        assert 'revenue' in breakdown
        assert 'minus_cogs' in breakdown
        assert 'minus_opex' in breakdown
        assert 'equals_ebitda' in breakdown

    def test_ebitda_trend_validation(self, financial_tools):
        """Test EBITDA trend with data quality validation"""
        result = financial_tools.get_ebitda(last_n_months=6)

        assert 'error' not in result
        assert 'data' in result
        assert len(result['data']) == 6

        # Should trigger validation warnings due to consistent test data
        assert 'data_quality_warnings' in result
        warnings = result['data_quality_warnings']

        # Should flag unusually high EBITDA margins
        high_margin_warning = any('unusually high' in warning for warning in warnings)
        assert high_margin_warning

    def test_cash_runway_calculation(self, financial_tools):
        """Test cash runway calculation (previously failing)"""
        result = financial_tools.get_cash_runway()

        # This should now work without the strftime error
        assert 'error' not in result
        assert 'current_cash_usd' in result
        assert 'runway_months' in result
        assert 'avg_monthly_burn_usd' in result
        assert 'burn_analysis' in result

        # Should have burn analysis
        burn_analysis = result['burn_analysis']
        assert 'monthly_burns' in burn_analysis
        assert 'months_analyzed' in burn_analysis

        # Should have recommendations
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0

    def test_invalid_date_handling(self, financial_tools):
        """Test error handling for invalid dates"""
        result = financial_tools.get_revenue('invalid-date')

        # Should return error for invalid date
        assert 'error' in result

    def test_nonexistent_month_handling(self, financial_tools):
        """Test handling of months with no data"""
        result = financial_tools.get_revenue('2099-12')

        # Should return error for non-existent month
        assert 'error' in result

    def test_data_validation_consistency_detection(self, financial_tools):
        """Test that data validation properly detects artificial consistency"""
        # Test with a longer period to ensure validation triggers
        result = financial_tools.get_gross_margin(last_n_months=12)

        # Should detect artificial consistency in test data
        assert 'data_quality_warnings' in result
        warnings = result['data_quality_warnings']

        # Should flag identical values
        identical_warning = any('identical' in warning.lower() for warning in warnings)
        assert identical_warning

        # Should flag low variation
        low_variation_warning = any('low variation' in warning.lower() for warning in warnings)
        assert low_variation_warning