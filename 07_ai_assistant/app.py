import streamlit as st
import anthropic
from databricks import sql
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare RCM Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .dashboard-title {
        background: linear-gradient(90deg, #1D3461, #1F6AA5);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .section-header {
        background-color: #1D3461;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        margin: 10px 0;
        font-weight: bold;
    }
    .ai-section {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
        color: #1D3461;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px;
        color: #666;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Configuration ─────────────────────────────────────────────
DATABRICKS_HOST   = st.secrets["DATABRICKS_HOST"]
DATABRICKS_TOKEN  = st.secrets["DATABRICKS_TOKEN"]
HTTP_PATH         = st.secrets["HTTP_PATH"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# ── Schema Context for Claude ─────────────────────────────────
SCHEMA_CONTEXT = """
You are an expert SQL analyst for a Healthcare RCM Analytics Platform.
You have access to these Gold tables in Databricks (database: rcm_gold):

1. gold_daily_snapshot
   - trans_date, facility_name, region, payer_name
   - total_claims, paid_claims, denied_claims, pending_claims
   - gross_charges, cash_collected
   - avg_collection_rate_pct, denial_rate_pct
   - dod_cash_variance

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
   - denial_risk_flag, productivity_tier

Rules:
- Always use fully qualified table names: rcm_gold.table_name
- Return ONLY valid Databricks SQL — no explanation, no backticks
- Available dates: 2026-04-21, 2026-04-22, 2026-04-23
"""

# ── Databricks Connection ─────────────────────────────────────
@st.cache_data(ttl=300)
def run_query(sql_query):
    try:
        connection = sql.connect(
            server_hostname = DATABRICKS_HOST,
            http_path       = HTTP_PATH,
            access_token    = DATABRICKS_TOKEN
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        connection.close()
        return pd.DataFrame(result, columns=columns), None
    except Exception as e:
        return None, str(e)

# ── Claude Functions ──────────────────────────────────────────
def generate_sql(question):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"{SCHEMA_CONTEXT}\n\nConvert to SQL:\n{question}"
        }]
    )
    return msg.content[0].text.strip()

def decide_visual(question, df):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""Question: {question}
Columns: {list(df.columns)}
Rows: {len(df)}
Reply ONE word: KPI, BAR, LINE, PIE, or TABLE"""
        }]
    )
    return msg.content[0].text.strip().upper()

def get_insight(question, df):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    data = df.to_string(index=False) if len(df) <= 15 else df.head(10).to_string(index=False)
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Healthcare RCM analyst.
Question: {question}
Data: {data}
Give 2 sentence business insight. Be specific about numbers."""
        }]
    )
    return msg.content[0].text.strip()

# ── Load Dashboard Data ───────────────────────────────────────
def load_kpis(payer_filter, facility_filter, date_filter, claim_type_filter):
    where_clauses = []
    if payer_filter != "All":
        where_clauses.append(f"payer_name = '{payer_filter}'")
    if facility_filter != "All":
        where_clauses.append(f"facility_name = '{facility_filter}'")
    if date_filter != "All":
        where_clauses.append(f"trans_date = '{date_filter}'")
    if claim_type_filter != "All":
        where_clauses.append(f"claim_type = '{claim_type_filter}'")

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT
        SUM(claim_volume)                                      AS total_claims,
        ROUND(SUM(cash_collected), 2)                         AS net_collections,
        ROUND(SUM(cash_collected)/NULLIF(SUM(gross_charges),0)*100, 2) AS collection_rate,
        ROUND(SUM(denied_count)*100.0/NULLIF(SUM(claim_volume),0), 2)  AS denial_rate,
        ROUND(SUM(gross_charges), 2)                          AS gross_charges
    FROM rcm_gold.gold_revenue_summary
    {where}
    """
    df, err = run_query(query)
    return df, err

def load_collections_by_payer(payer_filter, facility_filter, date_filter):
    where_clauses = []
    if payer_filter != "All":
        where_clauses.append(f"payer_name = '{payer_filter}'")
    if facility_filter != "All":
        where_clauses.append(f"facility_name = '{facility_filter}'")
    if date_filter != "All":
        where_clauses.append(f"trans_date = '{date_filter}'")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT payer_name,
           ROUND(SUM(cash_collected), 2) AS cash_collected
    FROM rcm_gold.gold_revenue_summary
    {where}
    GROUP BY payer_name
    ORDER BY cash_collected DESC
    """
    return run_query(query)

def load_denial_by_payer(payer_filter, facility_filter, date_filter):
    where_clauses = []
    if payer_filter != "All":
        where_clauses.append(f"payer_name = '{payer_filter}'")
    if facility_filter != "All":
        where_clauses.append(f"facility_name = '{facility_filter}'")
    if date_filter != "All":
        where_clauses.append(f"trans_date = '{date_filter}'")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT payer_name,
           ROUND(SUM(denied_count)*100.0/NULLIF(SUM(claim_volume),0), 2) AS denial_rate_pct
    FROM rcm_gold.gold_revenue_summary
    {where}
    GROUP BY payer_name
    ORDER BY denial_rate_pct DESC
    """
    return run_query(query)

def load_claims_by_type(payer_filter, facility_filter, date_filter):
    where_clauses = []
    if payer_filter != "All":
        where_clauses.append(f"payer_name = '{payer_filter}'")
    if facility_filter != "All":
        where_clauses.append(f"facility_name = '{facility_filter}'")
    if date_filter != "All":
        where_clauses.append(f"trans_date = '{date_filter}'")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT claim_type,
           SUM(claim_volume) AS claim_count
    FROM rcm_gold.gold_revenue_summary
    {where}
    GROUP BY claim_type
    """
    return run_query(query)

def load_performance_table(payer_filter, facility_filter, date_filter):
    where_clauses = []
    if payer_filter != "All":
        where_clauses.append(f"payer_name = '{payer_filter}'")
    if facility_filter != "All":
        where_clauses.append(f"facility_name = '{facility_filter}'")
    if date_filter != "All":
        where_clauses.append(f"trans_date = '{date_filter}'")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT
        facility_name                                          AS Facility,
        payer_name                                             AS Payer,
        SUM(claim_volume)                                      AS Claims,
        ROUND(SUM(gross_charges), 2)                          AS Gross_Charges,
        ROUND(SUM(cash_collected), 2)                         AS Cash_Collected,
        ROUND(SUM(cash_collected)/NULLIF(SUM(gross_charges),0)*100, 2) AS Collection_Rate_Pct,
        ROUND(SUM(denied_count)*100.0/NULLIF(SUM(claim_volume),0), 2)  AS Denial_Rate_Pct
    FROM rcm_gold.gold_revenue_summary
    {where}
    GROUP BY facility_name, payer_name
    ORDER BY Cash_Collected DESC
    LIMIT 20
    """
    return run_query(query)

# ── SIDEBAR FILTERS ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 RCM Analytics")
    st.markdown("---")
    st.markdown("**Filters**")

    date_filter = st.selectbox(
        "📅 Date",
        ["All", "2026-04-21", "2026-04-22", "2026-04-23"]
    )

    payer_filter = st.selectbox(
        "💊 Payer",
        ["All", "Anthem BCBS", "Aetna", "Cigna", "UnitedHealth",
         "Humana", "Medicare", "Medicaid", "Tricare", "Self-Pay"]
    )

    facility_filter = st.selectbox(
        "🏥 Facility",
        ["All", "RVA Medical Center", "Henrico General",
         "Chippenham Hospital", "Bon Secours St Mary",
         "VCU Health System", "Sentara RMH",
         "Johnston Willis", "Parham Medical",
         "Retreat Doctors", "Sheltering Arms"]
    )

    claim_type_filter = st.selectbox(
        "📋 Claim Type",
        ["All", "Professional", "Institutional"]
    )

    st.markdown("---")
    st.markdown("**Data**")
    st.markdown("📅 Apr 21 — Apr 23, 2026")
    st.markdown("🏥 50 Facilities")
    st.markdown("💊 9 Payers")
    st.markdown("👨‍⚕️ 5,000 Providers")
    st.markdown("---")
    st.markdown(
        "🔗 [GitHub](https://github.com/gardasajay42/RCM_Healthcare_Analytics)",
        unsafe_allow_html=True
    )

# ── DASHBOARD HEADER ──────────────────────────────────────────
st.markdown("""
<div class='dashboard-title'>
    <h2 style='margin:0; color:white'>
        🏥 Healthcare Revenue Cycle Management Analytics
    </h2>
    <p style='margin:5px 0 0 0; color:#B5D4F4; font-size:14px'>
        Virginia Hospital Network · Real-time Revenue Cycle Visibility
    </p>
</div>
""", unsafe_allow_html=True)

# ── ROW 1: KPI CARDS ─────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Key Performance Indicators</div>", unsafe_allow_html=True)

kpi_df, kpi_err = load_kpis(payer_filter, facility_filter, date_filter, claim_type_filter)

if kpi_err:
    st.error(f"Error loading KPIs: {kpi_err}")
else:
    k1, k2, k3, k4, k5 = st.columns(5)
    try:
        total_claims    = kpi_df["total_claims"].iloc[0]
        net_collections = kpi_df["net_collections"].iloc[0]
        collection_rate = kpi_df["collection_rate"].iloc[0]
        denial_rate     = kpi_df["denial_rate"].iloc[0]
        gross_charges   = kpi_df["gross_charges"].iloc[0]

        k1.metric("Total Claims",        f"{int(total_claims):,}")
        k2.metric("Net Collections",     f"${net_collections/1e9:.2f}bn")
        k3.metric("Collection Rate",     f"{collection_rate:.1f}%")
        k4.metric("Denial Rate",         f"{denial_rate:.1f}%")
        k5.metric("Gross Charges",       f"${gross_charges/1e9:.2f}bn")
    except Exception as e:
        st.warning(f"Could not render KPIs: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 2: CHARTS ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 Revenue Analytics</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Collections by Payer
with col1:
    df_pay, err = load_collections_by_payer(payer_filter, facility_filter, date_filter)
    if not err and df_pay is not None and len(df_pay) > 0:
        fig = px.bar(
            df_pay,
            x="cash_collected",
            y="payer_name",
            orientation="h",
            title="Net Collections by Payer",
            color="cash_collected",
            color_continuous_scale="Blues"
        )
        fig.update_layout(
            showlegend=False,
            height=350,
            yaxis=dict(categoryorder="total ascending"),
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

# Claims by Type Donut
with col2:
    df_type, err = load_claims_by_type(payer_filter, facility_filter, date_filter)
    if not err and df_type is not None and len(df_type) > 0:
        fig = px.pie(
            df_type,
            names="claim_type",
            values="claim_count",
            title="Total Claims by Claim Type",
            hole=0.45,
            color_discrete_sequence=["#1F6AA5", "#378ADD"]
        )
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

# ── ROW 3: DENIAL TABLE + PERFORMANCE TABLE ───────────────────
st.markdown("<div class='section-header'>📋 Performance Details</div>", unsafe_allow_html=True)

col3, col4 = st.columns([1, 2])

# Denial Rate by Payer
with col3:
    df_denial, err = load_denial_by_payer(payer_filter, facility_filter, date_filter)
    if not err and df_denial is not None and len(df_denial) > 0:
        st.markdown("**Denial Rate by Payer**")
        st.dataframe(
            df_denial.style.format({"denial_rate_pct": "{:.2f}%"}),
            use_container_width=True,
            height=300
        )

# Performance Table
with col4:
    df_perf, err = load_performance_table(payer_filter, facility_filter, date_filter)
    if not err and df_perf is not None and len(df_perf) > 0:
        st.markdown("**Performance by Facility and Payer**")
        st.dataframe(
            df_perf.style.format({
                "Gross_Charges":      "${:,.0f}",
                "Cash_Collected":     "${:,.0f}",
                "Collection_Rate_Pct":"{:.1f}%",
                "Denial_Rate_Pct":    "{:.1f}%"
            }),
            use_container_width=True,
            height=300
        )

# ── AI ASSISTANT SECTION ──────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🤖 AI Analytics Assistant — Ask Anything</div>", unsafe_allow_html=True)

st.markdown("""
<div style='background:#EEF4FB; padding:12px; border-radius:8px; margin:10px 0;
border-left: 4px solid #1F6AA5; font-size:13px; color:#333'>
Ask any question beyond the dashboard — get instant SQL, data and business insight.
</div>
""", unsafe_allow_html=True)

# Example questions
st.markdown("**Quick questions:**")
eq1, eq2, eq3, eq4 = st.columns(4)
with eq1:
    if st.button("Top denial reasons", use_container_width=True):
        st.session_state.ai_question = "Show me the top denial reasons by denied amount"
with eq2:
    if st.button("High risk providers", use_container_width=True):
        st.session_state.ai_question = "Which providers are flagged High Risk?"
with eq3:
    if st.button("AR aging breakdown", use_container_width=True):
        st.session_state.ai_question = "Show outstanding AR by aging bucket"
with eq4:
    if st.button("Collections trend", use_container_width=True):
        st.session_state.ai_question = "Compare cash collected across all 3 dates"

ai_question = st.text_input(
    "Or type your own question:",
    value=st.session_state.get("ai_question", ""),
    placeholder="e.g. Which providers in Cardiology have the highest denial rate?"
)

if st.button("🔍 Analyze", type="primary") and ai_question:

    with st.spinner("Generating SQL..."):
        sql_query = generate_sql(ai_question)

    with st.expander("📝 View Generated SQL", expanded=False):
        st.code(sql_query, language="sql")

    with st.spinner("Querying Databricks..."):
        df_ai, error = run_query(sql_query)

    if error:
        st.error(f"Query error: {error}")
    else:
        with st.spinner("Building visualization..."):
            visual_type = decide_visual(ai_question, df_ai)

        numeric_cols = df_ai.select_dtypes(include="number").columns.tolist()
        text_cols    = df_ai.select_dtypes(exclude="number").columns.tolist()

        if visual_type == "KPI" and numeric_cols:
            cols = st.columns(min(len(numeric_cols), 5))
            for i, col in enumerate(numeric_cols[:5]):
                val = df_ai[col].iloc[0]
                cols[i].metric(
                    col.replace("_", " ").title(),
                    f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
                )

        elif visual_type == "BAR" and text_cols and numeric_cols:
            fig = px.bar(
                df_ai,
                x=numeric_cols[0],
                y=text_cols[0],
                orientation="h",
                color=numeric_cols[0],
                color_continuous_scale="Blues",
                title=ai_question
            )
            fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        elif visual_type == "LINE":
            date_cols = [c for c in df_ai.columns if "date" in c.lower()]
            x_col = date_cols[0] if date_cols else df_ai.columns[0]
            fig = px.line(
                df_ai, x=x_col, y=numeric_cols[0],
                markers=True, title=ai_question
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        elif visual_type == "PIE" and text_cols and numeric_cols:
            fig = px.pie(
                df_ai,
                names=text_cols[0],
                values=numeric_cols[0],
                hole=0.4,
                title=ai_question
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.dataframe(df_ai, use_container_width=True)

        if visual_type != "TABLE":
            with st.expander("📋 View Raw Data"):
                st.dataframe(df_ai, use_container_width=True)
                st.caption(f"{len(df_ai)} rows")

        with st.spinner("Generating insight..."):
            insight = get_insight(ai_question, df_ai)

        st.info(f"💡 {insight}")

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray; font-size:12px'>"
    "Developed by Ajay Gardas · BI & Data Engineering · "
    "<a href='https://github.com/gardasajay42/RCM_Healthcare_Analytics' target='_blank'>GitHub</a> · "
    "Powered by Anthropic Claude AI + Databricks"
    "</div>",
    unsafe_allow_html=True
)
