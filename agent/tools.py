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
        if currency == 'USD' or pd.isna(currency):
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
                print(f"Warning: No exchange rate found for {currency}, assuming USD")
                return amount  # Assume it's already USD
        
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
    
    def get_opex_breakdown(self, month=None, by_entity=False):
        """
        Break down operating expenses by category
        
        Args:
            month: '2025-06' format for specific month, None for all months
            by_entity: True to show breakdown by entity as well
        
        Returns:
            Dictionary with OpEx breakdown by category
        """
        try:
            # Filter for OpEx accounts (anything starting with "Opex:")
            opex_data = self.actuals[self.actuals['account_c'].str.startswith('Opex:', na=False)].copy()
            
            if opex_data.empty:
                return {"error": "No operating expense data found"}
            
            # Convert to USD
            opex_data['amount_usd'] = opex_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            
            # Extract category from account name (Opex:Marketing -> Marketing)
            opex_data['category'] = opex_data['account_c'].str.replace('Opex:', '', regex=False)
            
            if month:
                # Filter for specific month
                try:
                    target_month = self._parse_month(month)
                except ValueError as e:
                    return {"error": str(e)}
                    
                month_data = opex_data[opex_data['month'] == target_month]
                
                if month_data.empty:
                    return {"error": f"No OpEx data found for {month}"}
                
                if by_entity:
                    # Breakdown by category AND entity
                    breakdown = month_data.groupby(['category', 'entity'])['amount_usd'].sum().reset_index()
                    
                    # Organize by category
                    category_breakdown = {}
                    for _, row in breakdown.iterrows():
                        category = row['category']
                        if category not in category_breakdown:
                            category_breakdown[category] = {
                                'total_usd': 0,
                                'entities': {}
                            }
                        category_breakdown[category]['entities'][row['entity']] = row['amount_usd']
                        category_breakdown[category]['total_usd'] += row['amount_usd']
                    
                    # Add formatted totals
                    for category in category_breakdown:
                        category_breakdown[category]['total_formatted'] = f"${category_breakdown[category]['total_usd']:,.0f}"
                        for entity in category_breakdown[category]['entities']:
                            amount = category_breakdown[category]['entities'][entity]
                            category_breakdown[category]['entities'][entity] = f"${amount:,.0f}"
                    
                    total_opex = sum(cat['total_usd'] for cat in category_breakdown.values())
                    
                    return {
                        "month": month,
                        "breakdown_by_category_and_entity": category_breakdown,
                        "total_opex_usd": f"${total_opex:,.0f}",
                        "categories_count": len(category_breakdown)
                    }
                
                else:
                    # Simple breakdown by category only
                    category_totals = month_data.groupby('category')['amount_usd'].sum().reset_index()
                    category_totals = category_totals.sort_values('amount_usd', ascending=False)
                    
                    total_opex = category_totals['amount_usd'].sum()
                    
                    # Add percentages
                    category_breakdown = []
                    for _, row in category_totals.iterrows():
                        percentage = (row['amount_usd'] / total_opex * 100) if total_opex > 0 else 0
                        category_breakdown.append({
                            'category': row['category'],
                            'amount_usd': f"${row['amount_usd']:,.0f}",
                            'percentage': f"{percentage:.1f}%"
                        })
                    
                    return {
                        "month": month,
                        "breakdown_by_category": category_breakdown,
                        "total_opex_usd": f"${total_opex:,.0f}",
                        "categories_count": len(category_breakdown)
                    }
            
            else:
                # All months summary
                monthly_totals = opex_data.groupby(['month', 'category'])['amount_usd'].sum().reset_index()
                monthly_totals['month_str'] = monthly_totals['month'].dt.strftime('%Y-%m')
                
                # Get category totals across all months
                category_totals = opex_data.groupby('category')['amount_usd'].sum().reset_index()
                category_totals = category_totals.sort_values('amount_usd', ascending=False)
                
                total_opex = category_totals['amount_usd'].sum()
                
                category_summary = []
                for _, row in category_totals.iterrows():
                    percentage = (row['amount_usd'] / total_opex * 100) if total_opex > 0 else 0
                    category_summary.append({
                        'category': row['category'],
                        'total_amount_usd': f"${row['amount_usd']:,.0f}",
                        'percentage': f"{percentage:.1f}%"
                    })
                
                # Monthly trend
                monthly_summary = monthly_totals.groupby('month_str')['amount_usd'].sum().reset_index()
                monthly_summary['amount_formatted'] = monthly_summary['amount_usd'].apply(lambda x: f"${x:,.0f}")
                
                return {
                    "all_months_summary": {
                        "category_breakdown": category_summary,
                        "monthly_totals": monthly_summary[['month_str', 'amount_formatted']].to_dict('records'),
                        "total_opex_usd": f"${total_opex:,.0f}",
                        "months_analyzed": len(monthly_summary)
                    }
                }
                
        except Exception as e:
            return {"error": f"Unexpected error in OpEx breakdown: {str(e)}"}
    
    def get_ebitda(self, month=None, last_n_months=None):
        """
        Calculate EBITDA: Revenue - COGS - OpEx
        
        Args:
            month: '2025-06' format for specific month
            last_n_months: Number of recent months to show trend
        
        Returns:
            Dictionary with EBITDA data and margin percentages
        """
        try:
            # Get all relevant data
            revenue_data = self.actuals[self.actuals['account_c'] == 'Revenue'].copy()
            cogs_data = self.actuals[self.actuals['account_c'] == 'COGS'].copy()
            opex_data = self.actuals[self.actuals['account_c'].str.startswith('Opex:', na=False)].copy()
            
            if revenue_data.empty:
                return {"error": "No revenue data found for EBITDA calculation"}
            
            # Convert all to USD
            revenue_data['amount_usd'] = revenue_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            cogs_data['amount_usd'] = cogs_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            opex_data['amount_usd'] = opex_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            
            # Group by month
            monthly_revenue = revenue_data.groupby('month')['amount_usd'].sum()
            monthly_cogs = cogs_data.groupby('month')['amount_usd'].sum()
            monthly_opex = opex_data.groupby('month')['amount_usd'].sum()
            
            # Calculate EBITDA for each month
            ebitda_data = []
            for month_date in monthly_revenue.index:
                revenue = monthly_revenue[month_date]
                cogs = monthly_cogs.get(month_date, 0)
                opex = monthly_opex.get(month_date, 0)
                
                gross_profit = revenue - cogs
                ebitda = revenue - cogs - opex
                
                # Calculate margins
                gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0
                ebitda_margin_pct = (ebitda / revenue * 100) if revenue > 0 else 0
                
                # Status indicators
                status = "Normal"
                if revenue <= 0:
                    status = "Invalid: Zero or negative revenue"
                elif ebitda < 0:
                    status = "Warning: Negative EBITDA"
                elif ebitda_margin_pct < 10:
                    status = "Alert: Low EBITDA margin (<10%)"
                
                ebitda_entry = {
                    'month': month_date.strftime('%Y-%m'),
                    'revenue_usd': revenue,
                    'cogs_usd': cogs,
                    'opex_usd': opex,
                    'gross_profit_usd': gross_profit,
                    'ebitda_usd': ebitda,
                    'gross_margin_percent': round(gross_margin_pct, 1),
                    'ebitda_margin_percent': round(ebitda_margin_pct, 1)
                }
                
                if status != "Normal":
                    ebitda_entry['status'] = status
                    
                ebitda_data.append(ebitda_entry)
            
            # Sort by month
            ebitda_data = sorted(ebitda_data, key=lambda x: x['month'])
            
            if month:
                # Return specific month
                try:
                    parsed_month = self._parse_month(month)
                    target_month = parsed_month.strftime('%Y-%m')
                except ValueError as e:
                    return {"error": str(e)}
                
                month_data = [m for m in ebitda_data if m['month'] == target_month]
                if not month_data:
                    return {"error": f"No EBITDA data found for {month}"}
                
                result = month_data[0].copy()
                result.update({
                    "revenue_formatted": f"${result['revenue_usd']:,.0f}",
                    "cogs_formatted": f"${result['cogs_usd']:,.0f}",
                    "opex_formatted": f"${result['opex_usd']:,.0f}",
                    "gross_profit_formatted": f"${result['gross_profit_usd']:,.0f}",
                    "ebitda_formatted": f"${result['ebitda_usd']:,.0f}",
                    "calculation_breakdown": {
                        "formula": "EBITDA = Revenue - COGS - OpEx",
                        "revenue": f"${result['revenue_usd']:,.0f}",
                        "minus_cogs": f"${result['cogs_usd']:,.0f}",
                        "minus_opex": f"${result['opex_usd']:,.0f}",
                        "equals_ebitda": f"${result['ebitda_usd']:,.0f}"
                    }
                })
                return result
            
            elif last_n_months:
                # Return trend for last N months
                if last_n_months <= 0:
                    return {"error": "last_n_months must be positive"}
                    
                recent_data = ebitda_data[-last_n_months:] if len(ebitda_data) >= last_n_months else ebitda_data
                
                if not recent_data:
                    return {"error": "No EBITDA data available for trend analysis"}
                
                # Calculate averages (excluding invalid months)
                valid_data = [m for m in recent_data if m.get('status') != "Invalid: Zero or negative revenue"]
                
                avg_ebitda_margin = 0
                avg_gross_margin = 0
                if valid_data:
                    avg_ebitda_margin = sum(m['ebitda_margin_percent'] for m in valid_data) / len(valid_data)
                    avg_gross_margin = sum(m['gross_margin_percent'] for m in valid_data) / len(valid_data)
                
                return {
                    "trend_months": last_n_months,
                    "data": recent_data,
                    "summary": {
                        "avg_ebitda_margin": round(avg_ebitda_margin, 1),
                        "avg_gross_margin": round(avg_gross_margin, 1),
                        "latest_ebitda_margin": recent_data[-1]['ebitda_margin_percent'] if recent_data else 0,
                        "latest_ebitda": f"${recent_data[-1]['ebitda_usd']:,.0f}" if recent_data else "$0",
                        "valid_months": len(valid_data)
                    }
                }
            
            else:
                # Return all months summary
                valid_data = [m for m in ebitda_data if m.get('status') != "Invalid: Zero or negative revenue"]
                
                avg_ebitda_margin = 0
                avg_gross_margin = 0
                total_ebitda = sum(m['ebitda_usd'] for m in valid_data)
                
                if valid_data:
                    avg_ebitda_margin = sum(m['ebitda_margin_percent'] for m in valid_data) / len(valid_data)
                    avg_gross_margin = sum(m['gross_margin_percent'] for m in valid_data) / len(valid_data)
                
                return {
                    "all_months": ebitda_data,
                    "summary": {
                        "avg_ebitda_margin": round(avg_ebitda_margin, 1),
                        "avg_gross_margin": round(avg_gross_margin, 1),
                        "total_ebitda_usd": f"${total_ebitda:,.0f}",
                        "latest_ebitda_margin": ebitda_data[-1]['ebitda_margin_percent'] if ebitda_data else 0,
                        "total_months": len(ebitda_data),
                        "valid_months": len(valid_data),
                        "months_with_negative_ebitda": len([m for m in ebitda_data if m['ebitda_usd'] < 0])
                    }
                }
                
        except Exception as e:
            return {"error": f"Unexpected error in EBITDA calculation: {str(e)}"}


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
    
    print("\n" + "="*50)
    print("OPEX BREAKDOWN TESTS")
    print("="*50)
    
    # Test June 2025 OpEx breakdown
    print("June 2025 OpEx Breakdown by Category:")
    june_opex = tools.get_opex_breakdown('2025-06')
    if 'breakdown_by_category' in june_opex:
        for category in june_opex['breakdown_by_category']:
            print(f"  {category['category']}: {category['amount_usd']} ({category['percentage']})")
        print(f"Total OpEx: {june_opex['total_opex_usd']}")
    else:
        print(f"Error: {june_opex}")
    
    print("\nJune 2025 OpEx Breakdown by Category AND Entity:")
    june_opex_detailed = tools.get_opex_breakdown('2025-06', by_entity=True)
    if 'breakdown_by_category_and_entity' in june_opex_detailed:
        for category, data in june_opex_detailed['breakdown_by_category_and_entity'].items():
            print(f"  {category}: {data['total_formatted']}")
            for entity, amount in data['entities'].items():
                print(f"    - {entity}: {amount}")
    
    print("\nAll months OpEx summary:")
    all_opex = tools.get_opex_breakdown()
    if 'all_months_summary' in all_opex:
        print("Top categories across all months:")
        for category in all_opex['all_months_summary']['category_breakdown'][:3]:  # Show top 3
            print(f"  {category['category']}: {category['total_amount_usd']} ({category['percentage']})")
        print(f"Total OpEx (all time): {all_opex['all_months_summary']['total_opex_usd']}")
    
    print("\n" + "="*50)
    print("EBITDA TESTS")
    print("="*50)
    
    # Test June 2025 EBITDA
    print("June 2025 EBITDA Analysis:")
    june_ebitda = tools.get_ebitda('2025-06')
    if 'ebitda_formatted' in june_ebitda:
        print(f"Revenue: {june_ebitda['revenue_formatted']}")
        print(f"COGS: {june_ebitda['cogs_formatted']}")
        print(f"OpEx: {june_ebitda['opex_formatted']}")
        print(f"Gross Profit: {june_ebitda['gross_profit_formatted']} ({june_ebitda['gross_margin_percent']}%)")
        print(f"EBITDA: {june_ebitda['ebitda_formatted']} ({june_ebitda['ebitda_margin_percent']}%)")
        
        if 'status' in june_ebitda:
            print(f"Status: {june_ebitda['status']}")
            
        print("\nCalculation breakdown:")
        breakdown = june_ebitda['calculation_breakdown']
        print(f"  {breakdown['revenue']} (Revenue)")
        print(f"- {breakdown['minus_cogs']} (COGS)")
        print(f"- {breakdown['minus_opex']} (OpEx)")
        print(f"= {breakdown['equals_ebitda']} (EBITDA)")
    else:
        print(f"Error: {june_ebitda}")
    
    print("\nLast 3 months EBITDA trend:")
    ebitda_trend = tools.get_ebitda(last_n_months=3)
    if 'data' in ebitda_trend:
        for month_data in ebitda_trend['data']:
            status_text = f" ({month_data['status']})" if 'status' in month_data else ""
            print(f"  {month_data['month']}: ${month_data['ebitda_usd']:,.0f} ({month_data['ebitda_margin_percent']}% margin){status_text}")
        
        summary = ebitda_trend['summary']
        print(f"\nSummary (last 3 months):")
        print(f"  Average EBITDA margin: {summary['avg_ebitda_margin']}%")
        print(f"  Latest EBITDA: {summary['latest_ebitda']}")
    
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
    
    print("\n5. Testing OpEx edge cases:")
    # Test non-existent month for OpEx
    result = tools.get_opex_breakdown("2099-12")
    if "error" in result:
        print(f"   ✅ Non-existent month OpEx: {result['error']}")
    
    print("\n6. Testing EBITDA edge cases:")  
    # Test non-existent month for EBITDA
    result = tools.get_ebitda("2099-12")
    if "error" in result:
        print(f"   ✅ Non-existent month EBITDA: {result['error']}")
        
    # Test invalid last_n_months for EBITDA
    result = tools.get_ebitda(last_n_months=-5)
    if "error" in result:
        print(f"   ✅ Negative months EBITDA: {result['error']}")
    
    print("\nAll edge case tests completed! ✅")

if __name__ == "__main__":
    test_revenue_tool()