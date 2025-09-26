Instructions:

FP&A Coding Assignment
CFOs rely on monthly financial summaries to understand how the business is performing, spot risks and explain results to the board. Traditionally, preparing these reports takes hours of manual work: pulling numbers from finance systems, reconciling actuals with budget, calculating margins, and creating charts for presentations.

In this assignment, you’ll build a mini CFO Copilot, an AI-powered assistant that can answer simple finance questions directly from structured CSV data. The CFO should be able to ask things like “What was June 2025 revenue vs budget?” or “Show me gross margin trends”, and the agent should respond with numbers and charts.

The goal is not to build a full finance platform, but to demonstrate how you can design an end-to-end agent:

Interpret a question
Run the right data functions
Return concise, board-ready answers
Build a Streamlit web app where a CFO can ask questions about monthly financials (stored in CSV files) and get back answers with charts.

This project is intentionally scoped to fit in 2–3 hours. It will test your ability to combine data analysis, agent design, and UX into a small but complete product.

What to Build
Chat box: CFO types a question.
Agent: classify intent → run data functions → return text + chart.
Charts: matplotlib/plotly, inline in Streamlit.
Optional (extra credit): “Export PDF” with just 1-2  key pages (Revenue vs Budget, Opex breakdown, Cash trend).
Data & Metrics

CSV Files Provided: https://docs.google.com/spreadsheets/d/e/2PACX-1vRPAvun4Gcow4ZNgHAAdE5b36kJgnqeVNNCQLfbzc_T6-IGLxJJsxmms9TJPDn61Q/pub?output=xlsx 

actuals.csv - monthly actuals by entity/account
budget.csv - monthly budget by entity/account
fx.csv - currency exchange rates
cash.csv - monthly cash balances
Required Metrics
Revenue (USD): actual vs budget.
Gross Margin %: (Revenue – COGS) / Revenue.
Opex total (USD): grouped by Opex:* categories.
EBITDA (proxy): Revenue – COGS – Opex.
Cash runway: cash ÷ avg monthly net burn (last 3 months).
Sample Questions to Support
“What was June 2025 revenue vs budget in USD?”
“Show Gross Margin % trend for the last 3 months.”
“Break down Opex by category for June.”
“What is our cash runway right now?”
Deliverables
GitHub repo (public) with:

README.md          # run instructions
app.py             # Streamlit app

agent/             # planner + tools

fixtures/          # sample CSVs

tests/             # 1-2 tests

requirements.txt

Short screen recording demo video (30-60 seconds):
Ask 1-2 questions, show charts.
Show pytest passing.
Optional:
Streamlit Cloud or Hugging Face Space link.