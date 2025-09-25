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
    initial_sidebar_state="expanded"
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

def main():
    # Header
    st.title("📊 CFO Copilot")
    st.markdown("*AI-powered financial analysis assistant*")
    st.divider()
    
    # Initialize planner
    planner = load_cfo_planner()
    
    # Sidebar with sample questions
    st.sidebar.header("Sample Questions")
    sample_questions = [
        "What was June 2025 revenue vs budget?",
        "Show me gross margin trends for the last 3 months",
        "Break down Opex by category for June",
        "What's our EBITDA for June 2025?",
        "What is our cash runway right now?"
    ]
    
    for question in sample_questions:
        if st.sidebar.button(question, key=f"sample_{hash(question)}"):
            st.session_state.user_question = question
    
    st.sidebar.divider()
    st.sidebar.markdown("**Available Analysis:**")
    st.sidebar.markdown("""
    • Revenue vs Budget
    • Gross Margin Trends  
    • OpEx Breakdowns
    • EBITDA Analysis
    • Cash Runway
    """)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Ask Your Financial Question")
        
        # Initialize session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Get user input
        user_question = st.text_input(
            "Enter your question:",
            value=st.session_state.get('user_question', ''),
            placeholder="e.g., What was June 2025 revenue vs budget?",
            key="question_input"
        )
        
        # Clear the session state after displaying
        if 'user_question' in st.session_state:
            del st.session_state.user_question
        
        if st.button("Ask", type="primary") or user_question:
            if user_question:
                with st.spinner("Analyzing your question..."):
                    try:
                        # Get response from CFO planner
                        response = planner.answer_question(user_question)
                        
                        # Store in chat history
                        st.session_state.chat_history.append({
                            'question': user_question,
                            'response': response
                        })
                        
                        # Display response
                        st.success("Analysis Complete!")
                        
                        if 'error' in response:
                            st.error(f"Error: {response['error']}")
                            if 'suggestion' in response:
                                st.info(response['suggestion'])
                        else:
                            # Display text response
                            if 'response' in response:
                                st.markdown(response['response'])
                            
                            # Display chart if available
                            if 'data' in response:
                                data = response['data']
                                chart = None
                                
                                # Determine chart type based on data structure
                                if any(key in data for key in ['all_months', 'actual_revenue_usd']):
                                    chart = create_revenue_chart(data)
                                elif 'gross_margin_percent' in str(data):
                                    chart = create_margin_chart(data)
                                elif any(key in data for key in ['breakdown_by_category', 'all_months_summary']):
                                    chart = create_opex_chart(data)
                                elif any(key in data for key in ['ebitda_usd', 'calculation_breakdown']):
                                    chart = create_ebitda_chart(data)
                                elif 'burn_analysis' in data:
                                    chart = create_cash_chart(data)
                                
                                if chart:
                                    st.plotly_chart(chart, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter a question")
    
    with col2:
        st.header("Financial Summary")
        
        # Quick metrics dashboard
        try:
            # Get latest metrics for summary
            june_revenue = planner.tools.get_revenue('2025-06')
            june_margin = planner.tools.get_gross_margin('2025-06')
            june_ebitda = planner.tools.get_ebitda('2025-06')
            cash_runway = planner.tools.get_cash_runway()
            
            if 'error' not in june_revenue:
                st.metric(
                    label="June 2025 Revenue",
                    value=june_revenue['actual_revenue_usd'],
                    delta=june_revenue.get('variance_usd', 'N/A')
                )
            
            if 'error' not in june_margin:
                st.metric(
                    label="Gross Margin",
                    value=f"{june_margin['gross_margin_percent']}%"
                )
            
            if 'error' not in june_ebitda:
                st.metric(
                    label="EBITDA Margin",
                    value=f"{june_ebitda['ebitda_margin_percent']}%"
                )
            
            if 'error' not in cash_runway:
                st.metric(
                    label="Cash Runway",
                    value=cash_runway['runway_months']
                )
                
        except Exception as e:
            st.error("Unable to load summary metrics")
    
    # Chat history
    if st.session_state.chat_history:
        st.divider()
        st.header("Recent Analysis")
        
        # Show last few conversations
        for i, chat in enumerate(reversed(st.session_state.chat_history[-3:]), 1):
            with st.expander(f"Q: {chat['question'][:50]}...", expanded=(i==1)):
                st.markdown(f"**Question:** {chat['question']}")
                if 'response' in chat['response']:
                    st.markdown(chat['response']['response'])
                elif 'error' in chat['response']:
                    st.error(chat['response']['error'])

if __name__ == "__main__":
    main()