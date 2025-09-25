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
        
        # Handle potential None/NaN values
        if pd.isna(amount) or amount is None:
            return 0
            
        # Find exchange rate for this month and currency
        rate_data = self.fx[
            (self.fx['month'] == month) & 
            (self.fx['currency'] == currency)
        ]
        
        if rate_data.empty:
            # Try to find the closest month rate as fallback
            closest_rate = self.fx[self.fx['currency'] == currency].tail(1)
            if not closest_rate.empty:
                rate = closest_rate.iloc[0]['rate_to_usd']
                print(f"Warning: Using latest available {currency} rate ({rate}) for {month}")
                return amount * rate
            else:
                print(f"Warning: No exchange rate found for {currency}, returning original amount")
                return amount
        
        rate = rate_data.iloc[0]['rate_to_usd']
        return amount * rate
    
    def _parse_month(self, month_str):
        """Parse month string and return datetime, with error handling"""
        try:
            # Handle different formats: "2025-06", "June 2025", "06/2025"
            if isinstance(month_str, str):
                # Try common formats
                for fmt in ['%Y-%m', '%B %Y', '%m/%Y', '%Y/%m']:
                    try:
                        return pd.to_datetime(month_str, format=fmt)
                    except:
                        continue
                # If no format works, try pandas general parsing
                return pd.to_datetime(month_str)
            return pd.to_datetime(month_str)
        except:
            raise ValueError(f"Could not parse month: {month_str}. Please use format like '2025-06'")
    
    def get_revenue(self, month=None, vs_budget=False):
        """
        Get revenue data for a specific month or all months
        
        Args:
            month: '2025-06' format, or None for all months
            vs_budget: True to compare actual vs budget
        
        Returns:
            Dictionary with revenue data and charts
        """
        try:
            # Filter actuals for revenue only
            revenue_actuals = self.actuals[self.actuals['account_c'] == 'Revenue'].copy()
            
            if revenue_actuals.empty:
                return {"error": "No revenue data found in actuals"}
            
            # Convert all revenue to USD
            revenue_actuals['amount_usd'] = revenue_actuals.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            
            if month:
                # Parse and filter for specific month
                try:
                    target_month = self._parse_month(month)
                except ValueError as e:
                    return {"error": str(e)}
                    
                month_data = revenue_actuals[revenue_actuals['month'] == target_month]
                
                if month_data.empty:
                    return {"error": f"No revenue data found for {month}"}
                
                # Sum up all entities for this month
                total_actual = month_data['amount_usd'].sum()
                
                # Handle zero or negative revenue
                if total_actual <= 0:
                    return {"error": f"Invalid revenue amount (${total_actual:,.0f}) for {month}"}
                
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
                        
                        if total_budget > 0:
                            variance = total_actual - total_budget
                            variance_pct = (variance / total_budget * 100)
                            
                            result.update({
                                "budget_revenue_usd": f"${total_budget:,.0f}",
                                "variance_usd": f"${variance:,.0f}",
                                "variance_percent": f"{variance_pct:.1f}%"
                            })
                        else:
                            result["budget_note"] = "Budget data found but amount is zero"
                    else:
                        result["budget_note"] = "No budget data available for this month"
                
                return result
            
            else:
                # Return all months summary
                monthly_totals = revenue_actuals.groupby('month')['amount_usd'].sum().reset_index()
                monthly_totals['month_str'] = monthly_totals['month'].dt.strftime('%Y-%m')
                
                # Filter out any zero/negative months
                valid_months = monthly_totals[monthly_totals['amount_usd'] > 0]
                
                return {
                    "all_months": valid_months[['month_str', 'amount_usd']].to_dict('records'),
                    "total_revenue_usd": f"${valid_months['amount_usd'].sum():,.0f}",
                    "months_count": len(valid_months)
                }
                
        except Exception as e:
            return {"error": f"Unexpected error in revenue calculation: {str(e)}"}
    
    def get_gross_margin(self, month=None, last_n_months=None):
        """
        Calculate gross margin: (Revenue - COGS) / Revenue * 100
        
        Args:
            month: '2025-06' format for specific month
            last_n_months: Number of recent months to show trend
        
        Returns:
            Dictionary with gross margin data and percentages
        """
        try:
            # Get revenue and COGS data, convert to USD
            revenue_data = self.actuals[self.actuals['account_c'] == 'Revenue'].copy()
            cogs_data = self.actuals[self.actuals['account_c'] == 'COGS'].copy()
            
            if revenue_data.empty:
                return {"error": "No revenue data found for gross margin calculation"}
            
            # Convert to USD
            revenue_data['amount_usd'] = revenue_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            cogs_data['amount_usd'] = cogs_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            
            # Group by month
            monthly_revenue = revenue_data.groupby('month')['amount_usd'].sum()
            monthly_cogs = cogs_data.groupby('month')['amount_usd'].sum()
            
            # Calculate gross margin for each month
            gross_margin_data = []
            for month_date in monthly_revenue.index:
                revenue = monthly_revenue[month_date]
                cogs = monthly_cogs.get(month_date, 0)  # Default to 0 if no COGS data
                gross_profit = revenue - cogs
                
                # Handle edge cases
                if revenue <= 0:
                    gross_margin_pct = 0
                    status = "Invalid: Zero or negative revenue"
                elif cogs < 0:
                    gross_margin_pct = 0
                    status = "Warning: Negative COGS"
                elif cogs > revenue:
                    gross_margin_pct = (gross_profit / revenue * 100)
                    status = "Warning: COGS exceeds revenue"
                else:
                    gross_margin_pct = (gross_profit / revenue * 100)
                    status = "Normal"
                
                margin_entry = {
                    'month': month_date.strftime('%Y-%m'),
                    'revenue_usd': revenue,
                    'cogs_usd': cogs,
                    'gross_profit_usd': gross_profit,
                    'gross_margin_percent': round(gross_margin_pct, 1)
                }
                
                if status != "Normal":
                    margin_entry['status'] = status
                    
                gross_margin_data.append(margin_entry)
            
            # Sort by month
            gross_margin_data = sorted(gross_margin_data, key=lambda x: x['month'])
            
            if month:
                # Parse month and return specific month
                try:
                    parsed_month = self._parse_month(month)
                    target_month = parsed_month.strftime('%Y-%m')
                except ValueError as e:
                    return {"error": str(e)}
                
                month_data = [m for m in gross_margin_data if m['month'] == target_month]
                if not month_data:
                    return {"error": f"No data found for {month}"}
                
                result = month_data[0].copy()
                result.update({
                    "revenue_formatted": f"${result['revenue_usd']:,.0f}",
                    "cogs_formatted": f"${result['cogs_usd']:,.0f}",
                    "gross_profit_formatted": f"${result['gross_profit_usd']:,.0f}"
                })
                return result
            
            elif last_n_months:
                # Return trend for last N months
                if last_n_months <= 0:
                    return {"error": "last_n_months must be positive"}
                    
                recent_data = gross_margin_data[-last_n_months:] if len(gross_margin_data) >= last_n_months else gross_margin_data
                
                if not recent_data:
                    return {"error": "No data available for trend analysis"}
                
                # Calculate averages only from valid margins
                valid_margins = [m['gross_margin_percent'] for m in recent_data if m.get('status') != "Invalid: Zero or negative revenue"]
                
                return {
                    "trend_months": last_n_months,
                    "data": recent_data,
                    "summary": {
                        "avg_margin": round(sum(valid_margins) / len(valid_margins), 1) if valid_margins else 0,
                        "latest_margin": recent_data[-1]['gross_margin_percent'] if recent_data else 0,
                        "valid_months": len(valid_margins)
                    }
                }
            
            else:
                # Return all months
                valid_margins = [m['gross_margin_percent'] for m in gross_margin_data if m.get('status') != "Invalid: Zero or negative revenue"]
                
                return {
                    "all_months": gross_margin_data,
                    "summary": {
                        "avg_margin": round(sum(valid_margins) / len(valid_margins), 1) if valid_margins else 0,
                        "latest_margin": gross_margin_data[-1]['gross_margin_percent'] if gross_margin_data else 0,
                        "total_months": len(gross_margin_data),
                        "valid_months": len(valid_margins)
                    }
                }
                
        except Exception as e:
            return {"error": f"Unexpected error in gross margin calculation: {str(e)}"}

# Simple test function
def test_revenue_tool():
    """Test the revenue calculator"""
    tools = FinancialTools()
    
    print("="*60)
    print("TESTING NORMAL CASES")
    print("="*60)
    
    # Test June 2025 revenue
    june_result = tools.get_revenue('2025-06', vs_budget=True)
    print("June 2025 Revenue Test:")
    print(june_result)
    
    print("\n" + "="*50)
    print("GROSS MARGIN TESTS")
    print("="*50)
    
    # Test June 2025 gross margin
    june_margin = tools.get_gross_margin('2025-06')
    print("June 2025 Gross Margin:")
    print(f"Revenue: {june_margin.get('revenue_formatted', 'N/A')}")
    print(f"COGS: {june_margin.get('cogs_formatted', 'N/A')}")
    print(f"Gross Profit: {june_margin.get('gross_profit_formatted', 'N/A')}")
    print(f"Gross Margin: {june_margin.get('gross_margin_percent', 'N/A')}%")
    
    print("\nLast 3 months gross margin trend:")
    trend = tools.get_gross_margin(last_n_months=3)
    for month_data in trend['data']:
        print(f"{month_data['month']}: {month_data['gross_margin_percent']}% margin")
    
    print(f"\nAverage margin (last 3 months): {trend['summary']['avg_margin']}%")
    
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)
    
    # Test invalid month formats
    print("\n1. Testing invalid month formats:")
    invalid_formats = ["invalid-month", "13-2025", "2025/13", ""]
    for fmt in invalid_formats:
        result = tools.get_revenue(fmt)
        if "error" in result:
            print(f"   ✅ {fmt}: {result['error'][:50]}...")
    
    # Test non-existent months
    print("\n2. Testing non-existent months:")
    nonexistent = ["2099-12", "1900-01"]
    for month in nonexistent:
        result = tools.get_revenue(month)
        if "error" in result:
            print(f"   ✅ {month}: {result['error']}")
    
    # Test different month formats that should work
    print("\n3. Testing flexible month parsing:")
    flexible_formats = ["2025-06", "June 2025"]  # Only test formats we know exist
    for fmt in flexible_formats:
        try:
            result = tools.get_revenue(fmt)
            if "error" not in result:
                print(f"   ✅ {fmt}: Revenue = {result.get('actual_revenue_usd', 'N/A')}")
        except:
            print(f"   ❌ {fmt}: Failed to parse")
    
    print("\n4. Testing gross margin edge cases:")
    # Test invalid parameters
    result = tools.get_gross_margin(last_n_months=-1)
    if "error" in result:
        print(f"   ✅ Negative months: {result['error']}")
    
    result = tools.get_gross_margin(last_n_months=0)
    if "error" in result:
        print(f"   ✅ Zero months: {result['error']}")
    
    print("\nAll edge case tests completed! ✅")

if __name__ == "__main__":
    test_revenue_tool()