import streamlit as st
import anthropic
from databricks import sql
import pandas as pd

# ── Configuration ─────────────────────────────────────────────

DATABRICKS_HOST   = st.secrets["DATABRICKS_HOST"]
DATABRICKS_TOKEN  = st.secrets["DATABRICKS_TOKEN"]
HTTP_PATH         = st.secrets["HTTP_PATH"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]


# ── Gold table schema for Claude to understand ────────────────
SCHEMA_CONTEXT = """
You are an expert SQL analyst for a Healthcare RCM Analytics Platform.
You have access to these Gold tables in Databricks (database: rcm_gold):

1. gold_daily_snapshot
   - trans_date, facility_name, region, payer_name
   - total_claims, paid_claims, denied_claims, pending_claims
   - gross_charges, cash_collected
   - avg_collection_rate_pct, denial_rate_pct
   - dod_cash_variance (day over day variance)

2. gold_ar_aging
   - payer_name, facility_name, region, ar_aging_bucket
   - claim_count, total_billed, outstanding_ar
   - avg_days_outstanding, risk_flag

3. gold_denial_analytics
   - trans_date, payer_name, facility_name, region
   - denial_reason, total_claims, denied_claims
   - denial_rate_pct, denied_amount

4. gold_revenue_summary
   - trans_date, payer_name, facility_name, region, claim_type
   - claim_volume, gross_charges, net_revenue, cash_collected
   - net_collection_rate_pct, denied_count, denial_rate_pct
   - running_total_payer

5. gold_provider_scorecard
   - provider_name, specialty, contract_type
   - facility_name, region
   - claim_count, total_billed, total_paid
   - collection_rate_pct, denial_rate_pct
   - denial_risk_flag (High Risk / Monitor / Normal)
   - productivity_tier (Top Quartile / Above Average / Below Average / Bottom Quartile)

Rules:
- Always use fully qualified table names: rcm_gold.table_name
- Return only valid Databricks SQL
- Do not use LIMIT unless asked
- For date filters use: WHERE trans_date = '2026-04-21'
- Available dates are: 2026-04-21, 2026-04-22, 2026-04-23
- Return ONLY the SQL query, no explanation, no markdown, no backticks
"""

# ── Connect to Databricks ─────────────────────────────────────
def run_query(sql_query):
    try:
        print("Connecting to Databricks...")
        connection = sql.connect(
            server_hostname = DATABRICKS_HOST,
            http_path       = HTTP_PATH,
            access_token    = DATABRICKS_TOKEN
        )
        print("Connected! Running query...")
        cursor = connection.cursor()
        cursor.execute(sql_query)
        print("Query done! Fetching results...")
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        connection.close()
        print("Done!")
        return pd.DataFrame(result, columns=columns), None
    except Exception as e:
        print(f"ERROR: {e}")
        return None, str(e)
# ── Ask Claude to convert question to SQL ─────────────────────
def generate_sql(user_question):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"{SCHEMA_CONTEXT}\n\nConvert this question to SQL:\n{user_question}"
            }
        ]
    )
    return message.content[0].text.strip()

# ── Ask Claude to explain the results ─────────────────────────
def explain_results(user_question, sql_query, df):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    data_summary = df.to_string(index=False) if len(df) <= 20 else df.head(10).to_string(index=False)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""You are a healthcare revenue cycle analyst.
The user asked: {user_question}

The query returned this data:
{data_summary}

Provide a concise 2-3 sentence business insight from this data.
Focus on what the numbers mean for the business."""
            }
        ]
    )
    return message.content[0].text.strip()

# ── Streamlit UI ───────────────────────────────────────────────
st.set_page_config(
    page_title="RCM AI Analytics Assistant",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Healthcare RCM Analytics — AI Assistant")
st.markdown("Ask questions about your revenue cycle data in plain English.")
st.divider()

# Sidebar with example questions
with st.sidebar:
    st.header("💡 Example Questions")
    examples = [
        "What is the denial rate for each payer?",
        "Which facility has the highest cash collected?",
        "Show me the top 5 denial reasons",
        "What is the total outstanding AR by aging bucket?",
        "Which providers are High Risk?",
        "Compare cash collected across all 3 dates",
        "Which payer has the worst collection rate?",
        "Show me providers in Top Quartile productivity"
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.question = ex

    st.divider()
    st.markdown("**Data available:**")
    st.markdown("📅 Apr 21, 22, 23 — 2026")
    st.markdown("🏥 50 Facilities")
    st.markdown("💊 9 Payers")
    st.markdown("👨‍⚕️ 5,000 Providers")

# Main chat input
question = st.text_input(
    "Ask a question about your RCM data:",
    value=st.session_state.get("question", ""),
    placeholder="e.g. What is the denial rate for Aetna?"
)

if st.button("🔍 Analyze", type="primary") and question:

    with st.spinner("Generating SQL query..."):
        sql_query = generate_sql(question)

    st.subheader("📝 Generated SQL")
    st.code(sql_query, language="sql")

    with st.spinner("Running query on Databricks..."):
        df, error = run_query(sql_query)

    if error:
        st.error(f"Query error: {error}")
    else:
        st.subheader("📊 Results")
        st.dataframe(df, use_container_width=True)

        st.markdown(f"*{len(df)} rows returned*")

        with st.spinner("Generating business insight..."):
            insight = explain_results(question, sql_query, df)

        st.subheader("💡 Business Insight")
        st.info(insight)

# Chat history
if "history" not in st.session_state:
    st.session_state.history = []

