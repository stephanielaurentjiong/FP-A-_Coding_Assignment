import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

class FinancialTools:
    """Tools to calculate financial metrics from CSV data"""
    
    def __init__(self):
        """Load all CSV files when the tool starts"""
        self.actuals = pd.read_csv('fixtures/actuals.csv')
        self.budget = pd.read_csv('fixtures/budget.csv')
        self.cash = pd.read_csv('fixtures/cash.csv')
        self.fx = pd.read_csv('fixtures/fx.csv')
        
        # Convert month columns to datetime for easier filtering
        self.actuals['month'] = pd.to_datetime(self.actuals['month'])
        self.budget['month'] = pd.to_datetime(self.budget['month'])
        self.cash['month'] = pd.to_datetime(self.cash['month'])
        self.fx['month'] = pd.to_datetime(self.fx['month'])
    
    def convert_to_usd(self, amount, currency, month):
        """Convert any currency to USD using exchange rates"""
        if currency == 'USD':
            return amount
        
        # Find exchange rate for this month and currency
        rate_data = self.fx[
            (self.fx['month'] == month) & 
            (self.fx['currency'] == currency)
        ]
        
        if rate_data.empty:
            print(f"Warning: No exchange rate found for {currency} in {month}")
            return amount  # Return original if no rate found
        
        rate = rate_data.iloc[0]['rate_to_usd']
        return amount * rate
    
    def get_revenue(self, month=None, vs_budget=False):
        """
        Get revenue data for a specific month or all months
        
        Args:
            month: '2025-06' format, or None for all months
            vs_budget: True to compare actual vs budget
        
        Returns:
            Dictionary with revenue data and charts
        """
        
        # Filter actuals for revenue only
        revenue_actuals = self.actuals[self.actuals['account_c'] == 'Revenue'].copy()
        
        # Convert all revenue to USD
        revenue_actuals['amount_usd'] = revenue_actuals.apply(
            lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
            axis=1
        )
        
        if month:
            # Filter for specific month
            target_month = pd.to_datetime(month)
            month_data = revenue_actuals[revenue_actuals['month'] == target_month]
            
            if month_data.empty:
                return {"error": f"No revenue data found for {month}"}
            
            # Sum up all entities for this month
            total_actual = month_data['amount_usd'].sum()
            
            result = {
                "month": month,
                "actual_revenue_usd": f"${total_actual:,.0f}",
                "details": month_data[['entity', 'amount_usd']].to_dict('records')
            }
            
            # Add budget comparison if requested
            if vs_budget:
                budget_data = self.budget[
                    (self.budget['account_c'] == 'Revenue') & 
                    (self.budget['month'] == target_month)
                ].copy()
                
                if not budget_data.empty:
                    # Convert budget to USD too
                    budget_data['amount_usd'] = budget_data.apply(
                        lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                        axis=1
                    )
                    total_budget = budget_data['amount_usd'].sum()
                    variance = total_actual - total_budget
                    variance_pct = (variance / total_budget * 100) if total_budget > 0 else 0
                    
                    result.update({
                        "budget_revenue_usd": f"${total_budget:,.0f}",
                        "variance_usd": f"${variance:,.0f}",
                        "variance_percent": f"{variance_pct:.1f}%"
                    })
            
            return result
        
        else:
            # Return all months summary
            monthly_totals = revenue_actuals.groupby('month')['amount_usd'].sum().reset_index()
            monthly_totals['month_str'] = monthly_totals['month'].dt.strftime('%Y-%m')
            
            return {
                "all_months": monthly_totals[['month_str', 'amount_usd']].to_dict('records'),
                "total_revenue_usd": f"${monthly_totals['amount_usd'].sum():,.0f}"
            }

# Simple test function
def test_revenue_tool():
    """Test the revenue calculator"""
    tools = FinancialTools()
    
    # Test June 2025 revenue
    june_result = tools.get_revenue('2025-06', vs_budget=True)
    print("June 2025 Revenue Test:")
    print(june_result)
    
    print("\nAll months summary:")
    all_result = tools.get_revenue()
    print(all_result)

if __name__ == "__main__":
    test_revenue_tool()