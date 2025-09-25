import re
from datetime import datetime
from tools import FinancialTools

class CFOPlanner:
    """AI planner that understands CFO questions and routes them to the right calculators"""
    
    def __init__(self):
        self.tools = FinancialTools()
        
        # Keywords that help identify question types
        self.revenue_keywords = ['revenue', 'sales', 'income', 'topline', 'budget', 'vs budget', 'actual vs budget']
        self.margin_keywords = ['margin', 'gross margin', 'profit margin', 'profitability']
        self.opex_keywords = ['opex', 'operating expense', 'expenses', 'spending', 'costs', 'breakdown', 'categories']
        self.ebitda_keywords = ['ebitda', 'earnings', 'profit', 'profitability', 'operational profit']
        self.cash_keywords = ['cash', 'runway', 'burn', 'cash flow', 'months left', 'depletion']
        
        # Trend analysis keywords
        self.trend_keywords = ['trend', 'trends', 'last', 'recent', 'months', 'quarterly', 'over time']
    
    def classify_question(self, question):
        """
        Analyze the question and determine intent
        
        Returns:
            dict: {
                'intent': 'revenue|margin|opex|ebitda|cash',
                'month': '2025-06' or None,
                'vs_budget': True/False,
                'trend_analysis': True/False,
                'trend_months': int or None
            }
        """
        question_lower = question.lower()
        
        result = {
            'intent': None,
            'month': None,
            'vs_budget': False,
            'trend_analysis': False,
            'trend_months': None,
            'by_entity': False,
            'confidence': 0.0
        }
        
        # Extract month/date information
        result['month'] = self._extract_month(question)
        
        # Check for budget comparison
        result['vs_budget'] = any(keyword in question_lower for keyword in ['vs budget', 'versus budget', 'compared to budget', 'against budget'])
        
        # Check for trend analysis
        result['trend_analysis'] = any(keyword in question_lower for keyword in self.trend_keywords)
        if result['trend_analysis']:
            result['trend_months'] = self._extract_trend_months(question)
        
        # Check for entity breakdown
        result['by_entity'] = any(keyword in question_lower for keyword in ['by entity', 'by company', 'parentco', 'emea', 'breakdown by'])
        
        # Classify intent based on keywords (with confidence scoring)
        intent_scores = {
            'revenue': self._calculate_score(question_lower, self.revenue_keywords),
            'margin': self._calculate_score(question_lower, self.margin_keywords),
            'opex': self._calculate_score(question_lower, self.opex_keywords),
            'ebitda': self._calculate_score(question_lower, self.ebitda_keywords),
            'cash': self._calculate_score(question_lower, self.cash_keywords)
        }
        
        # Get highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        result['intent'] = best_intent[0]
        result['confidence'] = best_intent[1]
        
        # If confidence is very low, mark as unknown
        if result['confidence'] < 0.1:
            result['intent'] = 'unknown'
        
        return result
    
    def _calculate_score(self, question, keywords):
        """Calculate relevance score based on keyword matches"""
        score = 0
        words = question.split()
        
        for keyword in keywords:
            if keyword in question:
                # Exact phrase match gets higher score
                score += 1.0
        
        for word in words:
            for keyword in keywords:
                if word in keyword.split():
                    # Individual word match gets lower score
                    score += 0.3
        
        return min(score, 3.0)  # Cap at 3.0
    
    def _extract_month(self, question):
        """Extract month from question text"""
        # Look for patterns like "June 2025", "2025-06", "06/2025", "for June", "in June"
        month_patterns = [
            r'(\d{4})-(\d{1,2})',  # 2025-06
            r'(\d{1,2})/(\d{4})',  # 06/2025
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',  # June 2025
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})',  # Jun 2025
            r'(?:for|in)\s+(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))?',  # for June, in June
            r'(?:for|in)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:\s+(\d{4}))?'  # for Jun, in Jun
        ]
        
        question_lower = question.lower()
        
        for pattern in month_patterns:
            match = re.search(pattern, question_lower)
            if match:
                try:
                    groups = match.groups()
                    if '-' in match.group(0) or '/' in match.group(0):
                        if '-' in match.group(0):
                            year, month = groups
                            return f"{year}-{month.zfill(2)}"
                        else:  # /
                            month, year = groups
                            return f"{year}-{month.zfill(2)}"
                    else:  # Month name
                        month_name = groups[0]
                        year = groups[1] if len(groups) > 1 and groups[1] else "2025"  # Default to 2025
                        
                        month_num = {
                            'january': '01', 'jan': '01',
                            'february': '02', 'feb': '02',
                            'march': '03', 'mar': '03',
                            'april': '04', 'apr': '04',
                            'may': '05',
                            'june': '06', 'jun': '06',
                            'july': '07', 'jul': '07',
                            'august': '08', 'aug': '08',
                            'september': '09', 'sep': '09',
                            'october': '10', 'oct': '10',
                            'november': '11', 'nov': '11',
                            'december': '12', 'dec': '12'
                        }.get(month_name.lower())
                        
                        if month_num:
                            return f"{year}-{month_num}"
                except:
                    continue
        
        return None
    
    def _extract_trend_months(self, question):
        """Extract number of months for trend analysis"""
        # Look for patterns like "last 3 months", "past 6 months"
        patterns = [
            r'last\s+(\d+)\s+months?',
            r'past\s+(\d+)\s+months?',
            r'recent\s+(\d+)\s+months?',
            r'(\d+)\s+months?'
        ]
        
        question_lower = question.lower()
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                try:
                    num_months = int(match.group(1))
                    if 1 <= num_months <= 24:  # Reasonable range
                        return num_months
                except:
                    continue
        
        # Default trend period
        return 3
    
    def answer_question(self, question):
        """
        Main method: analyze question and return appropriate response
        """
        try:
            # Classify the question
            classification = self.classify_question(question)
            
            # Route to appropriate calculator
            if classification['intent'] == 'revenue':
                return self._handle_revenue_question(classification, question)
            elif classification['intent'] == 'margin':
                return self._handle_margin_question(classification, question)
            elif classification['intent'] == 'opex':
                return self._handle_opex_question(classification, question)
            elif classification['intent'] == 'ebitda':
                return self._handle_ebitda_question(classification, question)
            elif classification['intent'] == 'cash':
                return self._handle_cash_question(classification, question)
            else:
                return self._handle_unknown_question(question)
        
        except Exception as e:
            return {
                "error": f"Error processing question: {str(e)}",
                "suggestion": "Please try rephrasing your question or ask about revenue, margins, expenses, EBITDA, or cash runway."
            }
    
    def _handle_revenue_question(self, classification, question):
        """Handle revenue-related questions"""
        if classification['month']:
            result = self.tools.get_revenue(classification['month'], vs_budget=classification['vs_budget'])
            if 'error' not in result:
                response = f"**Revenue Analysis for {result['month']}:**\n\n"
                response += f"• Actual Revenue: {result['actual_revenue_usd']}\n"
                
                if classification['vs_budget'] and 'variance_percent' in result:
                    response += f"• Budget Revenue: {result['budget_revenue_usd']}\n"
                    response += f"• Variance: {result['variance_usd']} ({result['variance_percent']})\n"
                    
                    variance_pct = float(result['variance_percent'].rstrip('%'))
                    if variance_pct < -10:
                        response += f"⚠️ **Significantly under budget**"
                    elif variance_pct < -5:
                        response += f"⚡ **Slightly under budget**"
                    elif variance_pct > 5:
                        response += f"🎉 **Exceeding budget!**"
                    else:
                        response += f"✅ **On target**"
                
                return {"response": response, "data": result}
            else:
                return result
        else:
            # Show all months or trends
            result = self.tools.get_revenue()
            if 'error' not in result:
                response = f"**Revenue Summary ({result['months_count']} months):**\n\n"
                response += f"• Total Revenue: {result['total_revenue_usd']}\n\n"
                response += "**Monthly Breakdown:**\n"
                for month_data in result['all_months'][-6:]:  # Show last 6 months
                    response += f"• {month_data['month_str']}: ${month_data['amount_usd']:,.0f}\n"
                
                return {"response": response, "data": result}
            else:
                return result
    
    def _handle_margin_question(self, classification, question):
        """Handle gross margin questions"""
        if classification['trend_analysis']:
            months = classification['trend_months'] or 3
            result = self.tools.get_gross_margin(last_n_months=months)
            if 'error' not in result:
                response = f"**Gross Margin Trend (Last {months} Months):**\n\n"
                for month_data in result['data']:
                    response += f"• {month_data['month']}: {month_data['gross_margin_percent']}%\n"
                response += f"\n**Average Margin:** {result['summary']['avg_margin']}%\n"
                response += f"**Latest Margin:** {result['summary']['latest_margin']}%"
                
                return {"response": response, "data": result}
            else:
                return result
        elif classification['month']:
            result = self.tools.get_gross_margin(classification['month'])
            if 'error' not in result:
                response = f"**Gross Margin for {result['month']}:**\n\n"
                response += f"• Revenue: {result['revenue_formatted']}\n"
                response += f"• COGS: {result['cogs_formatted']}\n"
                response += f"• Gross Profit: {result['gross_profit_formatted']}\n"
                response += f"• **Gross Margin: {result['gross_margin_percent']}%**\n"
                
                if result['gross_margin_percent'] > 70:
                    response += f"\n🎉 **Excellent margin!**"
                elif result['gross_margin_percent'] > 50:
                    response += f"\n✅ **Good margin**"
                elif result['gross_margin_percent'] > 30:
                    response += f"\n⚠️ **Moderate margin**"
                else:
                    response += f"\n🚨 **Low margin - needs attention**"
                
                return {"response": response, "data": result}
            else:
                return result
        else:
            # Default to 3-month trend
            return self._handle_margin_question({**classification, 'trend_analysis': True, 'trend_months': 3}, question)
    
    def _handle_opex_question(self, classification, question):
        """Handle operating expense questions"""
        if classification['month']:
            result = self.tools.get_opex_breakdown(classification['month'], by_entity=classification['by_entity'])
            if 'error' not in result:
                response = f"**OpEx Breakdown for {result['month']}:**\n\n"
                response += f"**Total OpEx: {result['total_opex_usd']}**\n\n"
                
                if classification['by_entity'] and 'breakdown_by_category_and_entity' in result:
                    for category, data in result['breakdown_by_category_and_entity'].items():
                        response += f"**{category}:** {data['total_formatted']}\n"
                        for entity, amount in data['entities'].items():
                            response += f"  • {entity}: {amount}\n"
                else:
                    response += "**By Category:**\n"
                    for category in result['breakdown_by_category']:
                        response += f"• {category['category']}: {category['amount_usd']} ({category['percentage']})\n"
                
                return {"response": response, "data": result}
            else:
                return result
        else:
            # Show all-time summary
            result = self.tools.get_opex_breakdown()
            if 'error' not in result:
                response = f"**OpEx Summary (All Time):**\n\n"
                response += f"**Total OpEx: {result['all_months_summary']['total_opex_usd']}**\n\n"
                response += "**Top Categories:**\n"
                for category in result['all_months_summary']['category_breakdown'][:5]:
                    response += f"• {category['category']}: {category['total_amount_usd']} ({category['percentage']})\n"
                
                return {"response": response, "data": result}
            else:
                return result
    
    def _handle_ebitda_question(self, classification, question):
        """Handle EBITDA questions"""
        if classification['trend_analysis']:
            months = classification['trend_months'] or 3
            result = self.tools.get_ebitda(last_n_months=months)
            if 'error' not in result:
                response = f"**EBITDA Trend (Last {months} Months):**\n\n"
                for month_data in result['data']:
                    status_text = f" ({month_data['status']})" if 'status' in month_data else ""
                    response += f"• {month_data['month']}: ${month_data['ebitda_usd']:,.0f} ({month_data['ebitda_margin_percent']}%){status_text}\n"
                
                response += f"\n**Summary:**\n"
                response += f"• Average EBITDA Margin: {result['summary']['avg_ebitda_margin']}%\n"
                response += f"• Latest EBITDA: {result['summary']['latest_ebitda']}"
                
                return {"response": response, "data": result}
            else:
                return result
        elif classification['month']:
            result = self.tools.get_ebitda(classification['month'])
            if 'error' not in result:
                response = f"**EBITDA Analysis for {result['month']}:**\n\n"
                response += f"• Revenue: {result['revenue_formatted']}\n"
                response += f"• COGS: {result['cogs_formatted']}\n"
                response += f"• OpEx: {result['opex_formatted']}\n"
                response += f"• **EBITDA: {result['ebitda_formatted']} ({result['ebitda_margin_percent']}%)**\n"
                
                if result['ebitda_margin_percent'] > 30:
                    response += f"\n🎉 **Excellent profitability!**"
                elif result['ebitda_margin_percent'] > 15:
                    response += f"\n✅ **Good profitability**"
                elif result['ebitda_margin_percent'] > 5:
                    response += f"\n⚠️ **Moderate profitability**"
                else:
                    response += f"\n🚨 **Low profitability - needs attention**"
                
                return {"response": response, "data": result}
            else:
                return result
        else:
            # Default to 3-month trend
            return self._handle_ebitda_question({**classification, 'trend_analysis': True, 'trend_months': 3}, question)
    
    def _handle_cash_question(self, classification, question):
        """Handle cash runway questions"""
        result = self.tools.get_cash_runway(classification['month'])
        if 'error' not in result:
            response = f"**Cash Runway Analysis:**\n\n"
            response += f"• Current Cash: {result['current_cash_usd']}\n"
            response += f"• Monthly Burn Rate: {result['avg_monthly_burn_usd']}\n"
            response += f"• **Runway: {result['runway_months']}**\n"
            response += f"• Estimated Depletion: {result['estimated_depletion_date']}\n"
            response += f"• Status: {result['status']}\n\n"
            
            response += "**Recent Burn Analysis:**\n"
            for burn in result['burn_analysis']['monthly_burns']:
                response += f"• {burn['month']}: {burn['burn_usd']} burn\n"
            
            response += f"\n**Recommendations:**\n"
            for i, rec in enumerate(result['recommendations'], 1):
                response += f"{i}. {rec}\n"
            
            return {"response": response, "data": result}
        else:
            return result
    
    def _handle_unknown_question(self, question):
        """Handle questions we don't understand"""
        return {
            "response": f"I'm not sure how to answer: '{question}'\n\n**I can help with:**\n• Revenue analysis (actual vs budget)\n• Gross margin trends\n• Operating expense breakdowns\n• EBITDA calculations\n• Cash runway analysis\n\n**Try asking:**\n• 'What was June 2025 revenue vs budget?'\n• 'Show me gross margin trends for last 3 months'\n• 'Break down OpEx by category for June'\n• 'What's our current cash runway?'",
            "suggestions": [
                "What was June 2025 revenue vs budget?",
                "Show me gross margin trends",
                "Break down OpEx by category",
                "What's our EBITDA for June?",
                "What's our current cash runway?"
            ]
        }

# Test function
def test_planner():
    """Test the CFO planner with sample questions"""
    planner = CFOPlanner()
    
    test_questions = [
        "What was June 2025 revenue vs budget?",
        "Show me gross margin trends for the last 3 months",
        "Break down Opex by category for June",
        "What is our cash runway right now?",
        "What's our EBITDA for June 2025?",
        "How are we doing this quarter?",  # Unknown question
    ]
    
    for question in test_questions:
        print(f"Q: {question}")
        print("="*50)
        
        classification = planner.classify_question(question)
        print(f"Classification: {classification}")
        
        answer = planner.answer_question(question)
        if 'response' in answer:
            print(f"\nAnswer:\n{answer['response']}")
        elif 'error' in answer:
            print(f"\nError: {answer['error']}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_planner()