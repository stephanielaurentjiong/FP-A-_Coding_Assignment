import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from agent.planner import CFOPlanner

# Page configuration
st.set_page_config(
    page_title="CFO Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize the CFO planner
@st.cache_resource
def load_cfo_planner():
    """Load the CFO planner (cached for performance)"""
    return CFOPlanner()

def create_revenue_chart(data):
    """Create revenue vs budget chart"""
    if 'all_months' in data:
        # Multi-month revenue trend
        df = pd.DataFrame(data['all_months'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['month_str'],
            y=df['amount_usd'],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title="Revenue Trend",
            xaxis_title="Month",
            yaxis_title="Revenue (USD)",
            yaxis_tickformat="$,.0f",
            height=400
        )
        return fig
    elif 'actual_revenue_usd' in data and 'budget_revenue_usd' in data:
        # Single month vs budget comparison
        actual_value = float(data['actual_revenue_usd'].replace('$', '').replace(',', ''))
        budget_value = float(data['budget_revenue_usd'].replace('$', '').replace(',', ''))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['Budget', 'Actual'],
            y=[budget_value, actual_value],
            name='Revenue Comparison',
            marker_color=['#ff7f0e', '#1f77b4'],
            text=[data['budget_revenue_usd'], data['actual_revenue_usd']],
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Revenue vs Budget - {data.get('month', 'N/A')}",
            xaxis_title="Category",
            yaxis_title="Revenue (USD)",
            yaxis_tickformat="$,.0f",
            height=400,
            showlegend=False
        )
        return fig
    elif 'actual_revenue_usd' in data:
        # Single month actual only (no budget comparison)
        actual_value = float(data['actual_revenue_usd'].replace('$', '').replace(',', ''))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[data.get('month', 'Revenue')],
            y=[actual_value],
            name='Revenue',
            marker_color='#1f77b4',
            text=[data['actual_revenue_usd']],
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Revenue - {data.get('month', 'N/A')}",
            xaxis_title="Month",
            yaxis_title="Revenue (USD)",
            yaxis_tickformat="$,.0f",
            height=400,
            showlegend=False
        )
        return fig
    return None

def create_margin_chart(data):
    """Create gross margin trend chart"""
    if 'data' in data and isinstance(data['data'], list):
        df = pd.DataFrame(data['data'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['gross_margin_percent'],
            mode='lines+markers',
            name='Gross Margin %',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title="Gross Margin Trend",
            xaxis_title="Month",
            yaxis_title="Gross Margin (%)",
            yaxis_tickformat=".1f",
            height=400
        )
        return fig
    return None

def create_opex_chart(data):
    """Create OpEx breakdown pie chart"""
    if 'breakdown_by_category' in data:
        categories = [item['category'] for item in data['breakdown_by_category']]
        amounts = [float(item['amount_usd'].replace('$', '').replace(',', '')) for item in data['breakdown_by_category']]
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=amounts,
            hole=0.3,
            textinfo='label+percent',
            textfont_size=12
        )])
        fig.update_layout(
            title="OpEx Breakdown by Category",
            height=400
        )
        return fig
    elif 'all_months_summary' in data:
        categories = [item['category'] for item in data['all_months_summary']['category_breakdown']]
        amounts = [float(item['total_amount_usd'].replace('$', '').replace(',', '')) for item in data['all_months_summary']['category_breakdown']]
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=amounts,
            hole=0.3,
            textinfo='label+percent',
            textfont_size=12
        )])
        fig.update_layout(
            title="OpEx Breakdown - All Time",
            height=400
        )
        return fig
    return None

def create_ebitda_chart(data):
    """Create EBITDA trend or waterfall chart"""
    if 'data' in data and isinstance(data['data'], list):
        # Trend chart
        df = pd.DataFrame(data['data'])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['ebitda_usd'],
            name='EBITDA',
            marker_color='#ff7f0e'
        ))
        fig.update_layout(
            title="EBITDA Trend",
            xaxis_title="Month",
            yaxis_title="EBITDA (USD)",
            yaxis_tickformat="$,.0f",
            height=400
        )
        return fig
    elif 'calculation_breakdown' in data:
        # Single month waterfall chart
        breakdown = data['calculation_breakdown']
        revenue = float(breakdown['revenue'].replace('$', '').replace(',', ''))
        cogs = -float(breakdown['minus_cogs'].replace('$', '').replace(',', ''))
        opex = -float(breakdown['minus_opex'].replace('$', '').replace(',', ''))
        ebitda = float(breakdown['equals_ebitda'].replace('$', '').replace(',', ''))
        
        fig = go.Figure(go.Waterfall(
            name="EBITDA Calculation",
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Revenue", "COGS", "OpEx", "EBITDA"],
            y=[revenue, cogs, opex, ebitda],
            text=[f"${revenue:,.0f}", f"${abs(cogs):,.0f}", f"${abs(opex):,.0f}", f"${ebitda:,.0f}"],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig.update_layout(
            title=f"EBITDA Breakdown - {data['month']}",
            height=400,
            yaxis_tickformat="$,.0f"
        )
        return fig
    return None

def create_cash_chart(data):
    """Create cash runway visualization"""
    if 'burn_analysis' in data:
        burns = data['burn_analysis']['monthly_burns']
        months = [burn['month'] for burn in burns]
        burn_amounts = [float(burn['burn_usd'].replace('$', '').replace(',', '')) for burn in burns]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=burn_amounts,
            name='Monthly Burn',
            marker_color='#d62728'
        ))
        fig.update_layout(
            title="Monthly Cash Burn Analysis",
            xaxis_title="Month",
            yaxis_title="Cash Burn (USD)",
            yaxis_tickformat="$,.0f",
            height=400
        )
        return fig
    return None

def display_cash_runway_metrics(data):
    """Display cash runway metrics in an organized format"""
    st.markdown("### 💰 Cash Position Overview")

    # Key metrics in a clean row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💵 Current Cash",
            value=data.get('current_cash_usd', 'N/A'),
            help="Current cash position"
        )

    with col2:
        st.metric(
            label="🔥 Monthly Burn Rate",
            value=data.get('avg_monthly_burn_usd', 'N/A'),
            help="Average monthly cash burn"
        )

    with col3:
        runway_months = data.get('runway_months', 'N/A')
        st.metric(
            label="📅 Runway",
            value=runway_months,
            help="Months of cash remaining at current burn rate"
        )

    with col4:
        depletion_date = data.get('estimated_depletion_date', 'N/A')
        st.metric(
            label="⏰ Estimated Depletion",
            value=depletion_date,
            help="Projected date when cash will run out"
        )

    # Status indicator
    status = data.get('status', 'Unknown')
    status_color = {
        'Normal': '🟢',
        'Warning': '🟡',
        'Critical': '🔴'
    }.get(status, '⚪')

    st.markdown(f"**Status:** {status_color} {status}")

    # Recent burn analysis if available
    if 'burn_analysis' in data and 'monthly_burns' in data['burn_analysis']:
        st.markdown("### 📊 Recent Burn Analysis")
        burns = data['burn_analysis']['monthly_burns']

        burn_cols = st.columns(min(len(burns), 6))  # Max 6 columns
        for i, burn in enumerate(burns[:6]):  # Show max 6 months
            with burn_cols[i]:
                st.metric(
                    label=burn['month'],
                    value=burn['burn_usd'],
                    help=f"Cash burn for {burn['month']}"
                )

def display_revenue_metrics(data):
    """Display revenue metrics in an organized format"""
    st.markdown("### 💰 Revenue Analysis")

    # Check if this is a specific month or all months data
    if 'month' in data:
        # Single month view
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="💵 Actual Revenue",
                value=data.get('actual_revenue_usd', 'N/A'),
                help=f"Revenue for {data.get('month', 'N/A')}"
            )

        with col2:
            if 'budget_revenue_usd' in data:
                st.metric(
                    label="🎯 Budgeted Revenue",
                    value=data.get('budget_revenue_usd', 'N/A'),
                    help="Budgeted revenue for the month"
                )
            else:
                st.metric(
                    label="🎯 Budget Status",
                    value="No budget data",
                    help="Budget comparison not available"
                )

        with col3:
            if 'variance_usd' in data:
                variance_value = data.get('variance_usd', '$0')
                variance_pct = data.get('variance_percent', '0%')
                st.metric(
                    label="📊 Variance",
                    value=variance_value,
                    delta=variance_pct,
                    help="Actual vs Budget variance"
                )
            else:
                st.metric(
                    label="📊 Variance",
                    value="N/A",
                    help="Variance calculation not available"
                )

        with col4:
            st.metric(
                label="📅 Period",
                value=data.get('month', 'N/A'),
                help="Analysis period"
            )

    elif 'all_months' in data:
        # Multi-month summary view
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="💵 Total Revenue",
                value=data.get('total_revenue_usd', 'N/A'),
                help="Total revenue across all months"
            )

        with col2:
            st.metric(
                label="📅 Months Analyzed",
                value=str(data.get('months_count', 'N/A')),
                help="Number of months with revenue data"
            )

        with col3:
            if data.get('all_months'):
                latest_month = data['all_months'][-1]
                st.metric(
                    label="📊 Latest Month",
                    value=f"${latest_month.get('amount_usd', 0):,.0f}",
                    help=f"Revenue for {latest_month.get('month_str', 'N/A')}"
                )

def display_opex_metrics(data):
    """Display OpEx metrics in an organized format"""
    st.markdown("### 💸 Operating Expenses Analysis")

    # Top level metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="💰 Total OpEx",
            value=data.get('total_opex_usd', 'N/A'),
            help="Total operating expenses"
        )

    with col2:
        categories_count = data.get('categories_count', 0)
        st.metric(
            label="📂 Categories",
            value=str(categories_count),
            help="Number of expense categories"
        )

    with col3:
        period = data.get('month', 'All Time')
        st.metric(
            label="📅 Period",
            value=period,
            help="Analysis period"
        )

    # Category breakdown
    if 'breakdown_by_category' in data:
        st.markdown("### 📊 Expense Breakdown by Category")

        # Display top categories in columns
        categories = data['breakdown_by_category'][:6]  # Show top 6
        if categories:
            cols = st.columns(min(len(categories), 3))

            for i, category in enumerate(categories):
                col_idx = i % 3
                with cols[col_idx]:
                    st.metric(
                        label=f"🏷️ {category['category']}",
                        value=category['amount_usd'],
                        delta=category['percentage'],
                        help=f"{category['category']} expenses"
                    )

    elif 'all_months_summary' in data:
        st.markdown("### 📊 All-Time Category Breakdown")

        # Display summary from all months data
        summary = data['all_months_summary']
        categories = summary.get('category_breakdown', [])[:6]

        if categories:
            cols = st.columns(min(len(categories), 3))

            for i, category in enumerate(categories):
                col_idx = i % 3
                with cols[col_idx]:
                    st.metric(
                        label=f"🏷️ {category['category']}",
                        value=category['total_amount_usd'],
                        delta=category['percentage'],
                        help=f"{category['category']} total expenses"
                    )

def display_ebitda_metrics(data):
    """Display EBITDA metrics in an organized format"""
    st.markdown("### 🎯 EBITDA Analysis")

    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        revenue = data.get('revenue_formatted', data.get('revenue_usd', 'N/A'))
        if isinstance(revenue, (int, float)):
            revenue = f"${revenue:,.0f}"
        st.metric(
            label="💰 Revenue",
            value=revenue,
            help="Total revenue"
        )

    with col2:
        gross_profit = data.get('gross_profit_formatted', data.get('gross_profit_usd', 'N/A'))
        if isinstance(gross_profit, (int, float)):
            gross_profit = f"${gross_profit:,.0f}"
        gross_margin = data.get('gross_margin_percent', 'N/A')
        st.metric(
            label="📊 Gross Profit",
            value=gross_profit,
            delta=f"{gross_margin}%" if gross_margin != 'N/A' else None,
            help="Revenue minus COGS"
        )

    with col3:
        ebitda = data.get('ebitda_formatted', data.get('ebitda_usd', 'N/A'))
        if isinstance(ebitda, (int, float)):
            ebitda = f"${ebitda:,.0f}"
        ebitda_margin = data.get('ebitda_margin_percent', 'N/A')
        st.metric(
            label="🎯 EBITDA",
            value=ebitda,
            delta=f"{ebitda_margin}%" if ebitda_margin != 'N/A' else None,
            help="Earnings before interest, taxes, depreciation, and amortization"
        )

    with col4:
        period = data.get('month', 'Multiple Months')
        st.metric(
            label="📅 Period",
            value=period,
            help="Analysis period"
        )

    # Status indicator if available
    if 'status' in data and data['status'] != 'Normal':
        status = data['status']
        status_color = {
            'Warning: Negative EBITDA': '🔴',
            'Alert: Low EBITDA margin (<10%)': '🟡',
            'Invalid: Zero or negative revenue': '🔴'
        }.get(status, '⚠️')

        st.markdown(f"**Status:** {status_color} {status}")

    # Calculation breakdown if available
    if 'calculation_breakdown' in data:
        st.markdown("### 🧮 Calculation Breakdown")
        breakdown = data['calculation_breakdown']

        calc_cols = st.columns(4)
        with calc_cols[0]:
            st.metric("Revenue", breakdown.get('revenue', 'N/A'), help="Starting point")
        with calc_cols[1]:
            st.metric("Less: COGS", breakdown.get('minus_cogs', 'N/A'), help="Cost of goods sold")
        with calc_cols[2]:
            st.metric("Less: OpEx", breakdown.get('minus_opex', 'N/A'), help="Operating expenses")
        with calc_cols[3]:
            st.metric("Equals: EBITDA", breakdown.get('equals_ebitda', 'N/A'), help="Final result")

def display_gross_margin_metrics(data):
    """Display gross margin metrics in an organized format"""
    st.markdown("### 📊 Gross Margin Analysis")

    # Check if this is a single month or trend data
    if 'month' in data:
        # Single month view
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            revenue = data.get('revenue_formatted', data.get('revenue_usd', 'N/A'))
            if isinstance(revenue, (int, float)):
                revenue = f"${revenue:,.0f}"
            st.metric(
                label="💰 Revenue",
                value=revenue,
                help="Total revenue"
            )

        with col2:
            cogs = data.get('cogs_formatted', data.get('cogs_usd', 'N/A'))
            if isinstance(cogs, (int, float)):
                cogs = f"${cogs:,.0f}"
            st.metric(
                label="📦 COGS",
                value=cogs,
                help="Cost of goods sold"
            )

        with col3:
            gross_profit = data.get('gross_profit_formatted', data.get('gross_profit_usd', 'N/A'))
            if isinstance(gross_profit, (int, float)):
                gross_profit = f"${gross_profit:,.0f}"
            st.metric(
                label="💵 Gross Profit",
                value=gross_profit,
                help="Revenue minus COGS"
            )

        with col4:
            margin = data.get('gross_margin_percent', 'N/A')
            st.metric(
                label="📈 Gross Margin",
                value=f"{margin}%" if margin != 'N/A' else 'N/A',
                help="Gross profit as percentage of revenue"
            )

        # Status indicator if available
        if 'status' in data and data['status'] != 'Normal':
            status = data['status']
            status_color = {
                'Warning: Negative COGS': '🟡',
                'Warning: COGS exceeds revenue': '🔴',
                'Invalid: Zero or negative revenue': '🔴'
            }.get(status, '⚠️')

            st.markdown(f"**Status:** {status_color} {status}")

    elif 'data' in data:
        # Trend data view
        st.markdown("### 📊 Margin Trend Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            summary = data.get('summary', {})
            avg_margin = summary.get('avg_margin', 'N/A')
            st.metric(
                label="📈 Average Margin",
                value=f"{avg_margin}%" if avg_margin != 'N/A' else 'N/A',
                help="Average gross margin across all periods"
            )

        with col2:
            latest_margin = summary.get('latest_margin', 'N/A')
            st.metric(
                label="📅 Latest Margin",
                value=f"{latest_margin}%" if latest_margin != 'N/A' else 'N/A',
                help="Most recent month's gross margin"
            )

        with col3:
            valid_months = summary.get('valid_months', 'N/A')
            st.metric(
                label="📊 Valid Months",
                value=str(valid_months),
                help="Number of months with valid data"
            )

def main():
    # Header with better styling
    st.markdown("# 📊 CFO Copilot")
    st.markdown("### AI-powered financial analysis for executives")

    # Initialize planner
    planner = load_cfo_planner()

    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["🔍 Ask Question", "📈 Quick Analysis", "📋 History"])

    with tab1:
        # Main question interface
        st.markdown("#### Ask me about your financials")

        # Quick action buttons
        st.markdown("**Quick Actions:**")
        quick_actions = st.columns(5)

        with quick_actions[0]:
            if st.button("💰 Revenue", help="Revenue vs Budget analysis"):
                st.session_state.user_question = "What was June 2025 revenue vs budget?"

        with quick_actions[1]:
            if st.button("📊 Margins", help="Gross margin trends"):
                st.session_state.user_question = "Show me gross margin trends for the last 3 months"

        with quick_actions[2]:
            if st.button("💸 OpEx", help="Operating expense breakdown"):
                st.session_state.user_question = "Break down Opex by category for June"

        with quick_actions[3]:
            if st.button("🎯 EBITDA", help="EBITDA analysis"):
                st.session_state.user_question = "What's our EBITDA for June 2025?"

        with quick_actions[4]:
            if st.button("🏦 Cash", help="Cash runway analysis"):
                st.session_state.user_question = "What is our cash runway right now?"

        st.markdown("---")

        # Text input for custom questions
        user_question = st.text_input(
            "Or ask a custom question:",
            value=st.session_state.get('user_question', ''),
            placeholder="e.g., Show me EBITDA trends for the last year",
            key="question_input"
        )
        
        # Clear the session state after displaying
        if 'user_question' in st.session_state:
            del st.session_state.user_question

        # Process question
        if st.button("📊 Analyze", type="primary", use_container_width=True) or user_question:
            if user_question:
                process_question(planner, user_question)
            else:
                st.warning("Please enter a question or use one of the quick actions above")

    with tab2:
        # Quick financial dashboard
        st.markdown("#### Financial Dashboard - Latest Metrics")

        try:
            # Display key metrics in a clean grid
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)

            with metrics_col1:
                with st.container():
                    st.markdown("**💰 Revenue**")
                    june_revenue = planner.tools.get_revenue('2025-06')
                    if 'error' not in june_revenue:
                        st.metric("June 2025", june_revenue['actual_revenue_usd'])
                        if st.button("📈 View Trends", key="revenue_trend"):
                            process_question(planner, "Show me revenue trends for the last 6 months")

            with metrics_col2:
                with st.container():
                    st.markdown("**📊 Gross Margin**")
                    june_margin = planner.tools.get_gross_margin('2025-06')
                    if 'error' not in june_margin:
                        st.metric("June 2025", f"{june_margin['gross_margin_percent']}%")
                        if st.button("📈 View Trends", key="margin_trend"):
                            process_question(planner, "Show me gross margin trends for the last 6 months")

            with metrics_col3:
                with st.container():
                    st.markdown("**🎯 EBITDA**")
                    june_ebitda = planner.tools.get_ebitda('2025-06')
                    if 'error' not in june_ebitda:
                        st.metric("June 2025", f"{june_ebitda['ebitda_margin_percent']}%")
                        if st.button("📈 View Trends", key="ebitda_trend"):
                            process_question(planner, "Show me EBITDA trends for the last 6 months")

            with metrics_col4:
                with st.container():
                    st.markdown("**🏦 Cash Runway**")
                    cash_runway = planner.tools.get_cash_runway()
                    if 'error' not in cash_runway:
                        st.metric("Current", cash_runway['runway_months'])
                        if st.button("📊 View Analysis", key="cash_analysis"):
                            process_question(planner, "What is our cash runway right now?")

        except Exception as e:
            st.error("Unable to load dashboard metrics")

    with tab3:
        # Chat history with better formatting
        st.markdown("#### Recent Analysis History")

        if st.session_state.chat_history:
            # Add clear history button
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()

            # Display recent conversations with better styling
            for i, chat in enumerate(reversed(st.session_state.chat_history[-10:]), 1):
                with st.expander(f"💬 {chat['question'][:60]}...", expanded=(i==1)):
                    st.markdown(f"**Question:** {chat['question']}")
                    st.markdown("**Response:**")
                    if 'response' in chat['response']:
                        st.markdown(chat['response']['response'])
                    elif 'error' in chat['response']:
                        st.error(chat['response']['error'])

                    # Replay button
                    if st.button(f"🔄 Ask Again", key=f"replay_{i}"):
                        process_question(planner, chat['question'])
        else:
            st.info("No analysis history yet. Ask a question to get started!")

def process_question(planner, user_question):
    """Process a user question and display results"""
    with st.spinner("🔍 Analyzing your question..."):
        try:
            # Get response from CFO planner
            response = planner.answer_question(user_question)

            # Store in chat history
            st.session_state.chat_history.append({
                'question': user_question,
                'response': response
            })

            # Store current analysis
            st.session_state.current_analysis = response

            # Display response in a structured way
            display_analysis_results(response)

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def display_analysis_results(response):
    """Display analysis results in a structured, readable format"""
    if 'error' in response:
        st.error(f"❌ {response['error']}")
        if 'suggestion' in response:
            st.info(f"💡 {response['suggestion']}")
        return

    # Success indicator
    st.success("✅ Analysis completed!")

    # Main response content (only show if no structured data display will be shown)
    if 'response' in response:
        # Check if we'll show structured data instead
        will_show_structured_display = False
        if 'data' in response:
            data = response['data']
            will_show_structured_display = any([
                any(key in data for key in ['all_months', 'actual_revenue_usd']),  # Revenue
                'gross_margin_percent' in str(data),  # Margin
                any(key in data for key in ['breakdown_by_category', 'all_months_summary']),  # OpEx
                any(key in data for key in ['ebitda_usd', 'calculation_breakdown']),  # EBITDA
                any(key in data for key in ['burn_analysis', 'current_cash_usd', 'runway_months', 'avg_monthly_burn_usd'])  # Cash
            ])

        # Only show text response if no structured display will be shown
        if not will_show_structured_display:
            st.markdown("### 📊 Analysis Results")
            st.markdown(response['response'])

    # Data quality warnings (if any)
    if 'data' in response and 'data_quality_warnings' in response['data']:
        with st.expander("⚠️ Data Quality Alerts", expanded=False):
            st.info("""
            **About Data Quality Alerts:** These warnings flag when data appears unusually consistent,
            which may indicate test/demo data rather than real business metrics.
            """)

            for warning in response['data']['data_quality_warnings']:
                st.warning(f"⚠️ {warning}")

            if 'statistics' in response['data']:
                stats = response['data']['statistics']
                st.markdown("**Statistical Summary:**")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Mean", f"{stats['mean']}%")
                with col_b:
                    st.metric("Std Dev", f"{stats['std_dev']}%")
                with col_c:
                    st.metric("Range", f"{stats['range']}%")

    # Structured displays and charts (if available)
    if 'data' in response:
        data = response['data']
        chart = None

        # Determine data type and display appropriate structured view
        if any(key in data for key in ['all_months', 'actual_revenue_usd']):
            # Revenue data
            display_revenue_metrics(data)
            chart = create_revenue_chart(data)
        elif 'gross_margin_percent' in str(data):
            # Gross margin data
            display_gross_margin_metrics(data)
            chart = create_margin_chart(data)
        elif any(key in data for key in ['breakdown_by_category', 'all_months_summary']):
            # OpEx data
            display_opex_metrics(data)
            chart = create_opex_chart(data)
        elif any(key in data for key in ['ebitda_usd', 'calculation_breakdown']):
            # EBITDA data
            display_ebitda_metrics(data)
            chart = create_ebitda_chart(data)
        elif 'burn_analysis' in data:
            # Cash runway data with burn analysis
            display_cash_runway_metrics(data)
            chart = create_cash_chart(data)
        elif any(key in data for key in ['current_cash_usd', 'runway_months', 'avg_monthly_burn_usd']):
            # Cash runway data without burn analysis
            display_cash_runway_metrics(data)

        if chart:
            st.markdown("### 📈 Visualization")
            st.plotly_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()