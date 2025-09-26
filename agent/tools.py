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

    def _validate_margin_consistency(self, margins, metric_name="Gross Margin", threshold=2.0):
        """
        Flag if margins are suspiciously consistent across time periods

        Args:
            margins: List of margin percentages
            metric_name: Name of metric for warning message
            threshold: Standard deviation threshold below which to flag (default 2.0%)

        Returns:
            dict with warning if margins are too consistent
        """
        if len(margins) < 3:
            return {}

        # Calculate statistics
        import statistics
        std_dev = statistics.stdev(margins)
        mean_margin = statistics.mean(margins)
        min_margin = min(margins)
        max_margin = max(margins)
        range_margin = max_margin - min_margin

        warnings = []

        # Flag suspiciously low standard deviation
        if std_dev < threshold:
            warnings.append(f"{metric_name} shows unusually low variation (std dev: {std_dev:.2f}%)")

        # Flag if all margins are identical
        if range_margin == 0:
            warnings.append(f"All {metric_name} values are identical ({mean_margin:.1f}%)")

        # Flag if margins are unrealistically high
        if metric_name == "Gross Margin" and mean_margin > 80:
            warnings.append(f"{metric_name} average ({mean_margin:.1f}%) is unusually high for most businesses")
        elif metric_name == "EBITDA Margin" and mean_margin > 40:
            warnings.append(f"{metric_name} average ({mean_margin:.1f}%) is unusually high for most businesses")

        # Flag if too consistent within a tight range
        if range_margin < 1.0 and std_dev < 0.5:
            warnings.append(f"{metric_name} varies by less than 1% across all periods (range: {range_margin:.2f}%)")

        if warnings:
            return {
                "data_quality_warnings": warnings,
                "statistics": {
                    "mean": round(mean_margin, 2),
                    "std_dev": round(std_dev, 2),
                    "min": min_margin,
                    "max": max_margin,
                    "range": round(range_margin, 2)
                }
            }

        return {}

    def _validate_business_metrics(self, data_type, values):
        """
        Validate business metrics for realistic ranges and patterns

        Args:
            data_type: 'revenue', 'margin', 'ebitda', etc.
            values: List of values to validate

        Returns:
            dict with warnings if metrics seem unrealistic
        """
        if not values or len(values) < 2:
            return {}

        warnings = []

        if data_type == 'revenue':
            # Check for unrealistic revenue patterns
            growth_rates = []
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    growth = ((values[i] - values[i-1]) / values[i-1]) * 100
                    growth_rates.append(growth)

            if growth_rates:
                avg_growth = sum(growth_rates) / len(growth_rates)
                if abs(avg_growth) > 20:  # More than 20% average month-over-month growth
                    warnings.append(f"Revenue shows unusually high average monthly growth rate: {avg_growth:.1f}%")

        elif data_type == 'cash_burn':
            # Check for unrealistic burn patterns
            if all(abs(v - values[0]) < 1000 for v in values):  # All burns within $1k of each other
                warnings.append("Cash burn rates are unusually consistent across months")

        if warnings:
            return {"business_logic_warnings": warnings}

        return {}

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
            revenue_actuals = self.actuals[self.actuals['account_category'] == 'Revenue'].copy()
            
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
                        (self.budget['account_category'] == 'Revenue') & 
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
            revenue_data = self.actuals[self.actuals['account_category'] == 'Revenue'].copy()
            cogs_data = self.actuals[self.actuals['account_category'] == 'COGS'].copy()
            
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

                # Add data validation warnings
                result = {
                    "trend_months": last_n_months,
                    "data": recent_data,
                    "summary": {
                        "avg_margin": round(sum(valid_margins) / len(valid_margins), 1) if valid_margins else 0,
                        "latest_margin": recent_data[-1]['gross_margin_percent'] if recent_data else 0,
                        "valid_months": len(valid_margins)
                    }
                }

                # Add data quality validation
                validation_result = self._validate_margin_consistency(valid_margins, "Gross Margin")
                if validation_result:
                    result.update(validation_result)

                return result
            
            else:
                # Return all months
                valid_margins = [m['gross_margin_percent'] for m in gross_margin_data if m.get('status') != "Invalid: Zero or negative revenue"]

                result = {
                    "all_months": gross_margin_data,
                    "summary": {
                        "avg_margin": round(sum(valid_margins) / len(valid_margins), 1) if valid_margins else 0,
                        "latest_margin": gross_margin_data[-1]['gross_margin_percent'] if gross_margin_data else 0,
                        "total_months": len(gross_margin_data),
                        "valid_months": len(valid_margins)
                    }
                }

                # Add data quality validation for all months
                validation_result = self._validate_margin_consistency(valid_margins, "Gross Margin")
                if validation_result:
                    result.update(validation_result)

                return result
                
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
            opex_data = self.actuals[self.actuals['account_category'].str.startswith('Opex:', na=False)].copy()
            
            if opex_data.empty:
                return {"error": "No operating expense data found"}
            
            # Convert to USD
            opex_data['amount_usd'] = opex_data.apply(
                lambda row: self.convert_to_usd(row['amount'], row['currency'], row['month']), 
                axis=1
            )
            
            # Extract category from account name (Opex:Marketing -> Marketing)
            opex_data['category'] = opex_data['account_category'].str.replace('Opex:', '', regex=False)
            
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
            revenue_data = self.actuals[self.actuals['account_category'] == 'Revenue'].copy()
            cogs_data = self.actuals[self.actuals['account_category'] == 'COGS'].copy()
            opex_data = self.actuals[self.actuals['account_category'].str.startswith('Opex:', na=False)].copy()
            
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

                result = {
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

                # Add EBITDA margin validation
                valid_ebitda_margins = [m['ebitda_margin_percent'] for m in valid_data]
                validation_result = self._validate_margin_consistency(valid_ebitda_margins, "EBITDA Margin")
                if validation_result:
                    result.update(validation_result)

                return result
            
            else:
                # Return all months summary
                valid_data = [m for m in ebitda_data if m.get('status') != "Invalid: Zero or negative revenue"]
                
                avg_ebitda_margin = 0
                avg_gross_margin = 0
                total_ebitda = sum(m['ebitda_usd'] for m in valid_data)
                
                if valid_data:
                    avg_ebitda_margin = sum(m['ebitda_margin_percent'] for m in valid_data) / len(valid_data)
                    avg_gross_margin = sum(m['gross_margin_percent'] for m in valid_data) / len(valid_data)

                result = {
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

                # Add EBITDA margin validation for all months
                valid_ebitda_margins = [m['ebitda_margin_percent'] for m in valid_data]
                validation_result = self._validate_margin_consistency(valid_ebitda_margins, "EBITDA Margin")
                if validation_result:
                    result.update(validation_result)

                return result
                
        except Exception as e:
            return {"error": f"Unexpected error in EBITDA calculation: {str(e)}"}
    
    def get_cash_runway(self, as_of_month=None):
        """
        Calculate cash runway: months until cash runs out based on recent burn rate
        Formula: Current Cash ÷ Average Monthly Burn Rate (last 3 months)
        
        Args:
            as_of_month: '2025-06' format for specific month analysis, None for latest
        
        Returns:
            Dictionary with cash runway analysis
        """
        try:
            if self.cash.empty:
                return {"error": "No cash data found for runway calculation"}

            # Clean cash data - remove empty rows and NaT values
            cash_clean = self.cash.dropna(subset=['month', 'cash_usd']).copy()
            cash_clean = cash_clean[cash_clean['month'].notna() & cash_clean['cash_usd'].notna()]

            if cash_clean.empty:
                return {"error": "No valid cash data found after cleaning"}

            # Sort cash data by month to ensure correct ordering
            cash_sorted = cash_clean.sort_values('month')
            
            if as_of_month:
                # Calculate runway as of specific month
                try:
                    target_month = self._parse_month(as_of_month)
                except ValueError as e:
                    return {"error": str(e)}
                
                # Find cash balance for target month
                current_cash_data = cash_sorted[cash_sorted['month'] == target_month]
                if current_cash_data.empty:
                    return {"error": f"No cash data found for {as_of_month}"}
                
                current_cash = current_cash_data.iloc[0]['cash_usd']
                
                # Get 3 months of cash data ending with target month
                target_index = cash_sorted[cash_sorted['month'] == target_month].index[0]
                available_data = cash_sorted.loc[:target_index]
                
            else:
                # Use latest available data
                current_cash = cash_sorted.iloc[-1]['cash_usd']
                target_month = cash_sorted.iloc[-1]['month']

                # Safely format the date
                try:
                    as_of_month = target_month.strftime('%Y-%m')
                except (AttributeError, ValueError):
                    return {"error": f"Invalid date format in cash data: {target_month}"}

                available_data = cash_sorted
            
            if len(available_data) < 2:
                return {"error": "Need at least 2 months of cash data to calculate burn rate"}
            
            # Calculate monthly burn rate (cash decrease) for last 3 months
            recent_data = available_data.tail(min(4, len(available_data)))  # Get up to 4 months for 3 burn calculations
            
            if len(recent_data) < 2:
                return {"error": "Insufficient cash history for burn rate calculation"}
            
            # Calculate month-to-month burn (positive = cash decrease)
            monthly_burns = []
            burn_details = []
            
            for i in range(1, len(recent_data)):
                prev_cash = recent_data.iloc[i-1]['cash_usd']
                curr_cash = recent_data.iloc[i]['cash_usd']
                burn = prev_cash - curr_cash  # Positive = money going out
                month_str = recent_data.iloc[i]['month'].strftime('%Y-%m')
                
                monthly_burns.append(burn)
                burn_details.append({
                    'month': month_str,
                    'starting_cash': prev_cash,
                    'ending_cash': curr_cash,
                    'burn': burn
                })
            
            if not monthly_burns:
                return {"error": "Could not calculate any monthly burn rates"}
            
            # Calculate average burn rate
            avg_burn = sum(monthly_burns) / len(monthly_burns)
            
            # Calculate runway
            if avg_burn <= 0:
                runway_months = float('inf')  # Infinite runway if gaining cash or no burn
                runway_status = "Infinite - company is cash flow positive or stable"
            else:
                runway_months = current_cash / avg_burn
                runway_status = "Normal"
                
                # Add status alerts
                if runway_months < 6:
                    runway_status = "Critical: Less than 6 months runway"
                elif runway_months < 12:
                    runway_status = "Warning: Less than 12 months runway"
                elif runway_months < 18:
                    runway_status = "Caution: Less than 18 months runway"
            
            # Format runway display
            if runway_months == float('inf'):
                runway_display = "Infinite (Cash Flow Positive)"
                months_remaining = "N/A - Growing Cash"
            else:
                runway_display = f"{runway_months:.1f} months"
                months_remaining = f"{int(runway_months)} months, {int((runway_months % 1) * 30)} days"
            
            # Calculate estimated cash depletion date
            if runway_months != float('inf'):
                try:
                    from datetime import timedelta
                    depletion_date = target_month + timedelta(days=runway_months * 30)
                    depletion_date_str = depletion_date.strftime('%Y-%m-%d')
                except (TypeError, ValueError, AttributeError):
                    depletion_date_str = f"Approximately {runway_months:.1f} months from latest data"
            else:
                depletion_date_str = "Never (if current trend continues)"
            
            return {
                "as_of_month": as_of_month,
                "current_cash_usd": f"${current_cash:,.0f}",
                "avg_monthly_burn_usd": f"${avg_burn:,.0f}",
                "runway_months": runway_display,
                "runway_detailed": months_remaining,
                "estimated_depletion_date": depletion_date_str,
                "status": runway_status,
                "burn_analysis": {
                    "months_analyzed": len(monthly_burns),
                    "monthly_burns": [
                        {
                            "month": detail['month'],
                            "burn_usd": f"${detail['burn']:,.0f}",
                            "cash_start": f"${detail['starting_cash']:,.0f}",
                            "cash_end": f"${detail['ending_cash']:,.0f}"
                        }
                        for detail in burn_details
                    ],
                    "burn_trend": "Increasing" if len(monthly_burns) > 1 and monthly_burns[-1] > monthly_burns[0] else "Stable/Decreasing"
                },
                "recommendations": self._get_runway_recommendations(runway_months, avg_burn)
            }
            
        except Exception as e:
            return {"error": f"Unexpected error in cash runway calculation: {str(e)}"}
    
    def _get_runway_recommendations(self, runway_months, avg_burn):
        """Generate CFO recommendations based on runway analysis"""
        recommendations = []
        
        if runway_months == float('inf'):
            recommendations.append("Excellent: Company is cash flow positive")
            recommendations.append("Consider investing excess cash or expanding operations")
        elif runway_months < 6:
            recommendations.append("URGENT: Immediate action required")
            recommendations.append("Consider emergency fundraising or cost reduction")
            recommendations.append("Review all non-essential expenses")
        elif runway_months < 12:
            recommendations.append("Start fundraising process immediately")
            recommendations.append("Review OpEx for potential cost savings")
            recommendations.append("Accelerate revenue initiatives")
        elif runway_months < 18:
            recommendations.append("Begin planning next funding round")
            recommendations.append("Monitor burn rate closely")
            recommendations.append("Optimize operational efficiency")
        else:
            recommendations.append("Healthy runway - continue monitoring")
            recommendations.append("Plan for future growth initiatives")
        
        return recommendations

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
    
    print("\n" + "="*50)
    print("CASH RUNWAY TESTS")
    print("="*50)
    
    # Test latest cash runway
    print("Current Cash Runway Analysis:")
    runway = tools.get_cash_runway()
    if 'runway_months' in runway:
        print(f"Current Cash: {runway['current_cash_usd']}")
        print(f"Average Monthly Burn: {runway['avg_monthly_burn_usd']}")
        print(f"Runway: {runway['runway_months']} ({runway['runway_detailed']})")
        print(f"Status: {runway['status']}")
        print(f"Estimated Depletion: {runway['estimated_depletion_date']}")
        
        print(f"\nBurn Rate Analysis (last {runway['burn_analysis']['months_analyzed']} months):")
        for burn in runway['burn_analysis']['monthly_burns']:
            print(f"  {burn['month']}: {burn['burn_usd']} burn ({burn['cash_start']} → {burn['cash_end']})")
        print(f"Trend: {runway['burn_analysis']['burn_trend']}")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(runway['recommendations'], 1):
            print(f"  {i}. {rec}")
    else:
        print(f"Error: {runway}")
    
    # Test specific month runway
    print(f"\nRunway as of June 2025:")
    june_runway = tools.get_cash_runway('2025-06')
    if 'runway_months' in june_runway:
        print(f"Cash as of June 2025: {june_runway['current_cash_usd']}")
        print(f"Runway: {june_runway['runway_months']}")
        print(f"Status: {june_runway['status']}")
    
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
    
    print("\n7. Testing Cash Runway edge cases:")
    # Test non-existent month for runway
    result = tools.get_cash_runway("2099-12")
    if "error" in result:
        print(f"   ✅ Non-existent month runway: {result['error']}")
    
    # Test invalid date format for runway  
    result = tools.get_cash_runway("invalid-date")
    if "error" in result:
        print(f"   ✅ Invalid date runway: {result['error'][:50]}...")
    
    print("\nAll edge case tests completed! ✅")

if __name__ == "__main__":
    test_revenue_tool()