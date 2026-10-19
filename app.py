from pathlib import Path
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.data_loader import validate_transactions, validate_network, DataValidationError
from src.cashflow_engine import forecast_business, summarize_forecast
from src.scenario_engine import apply_payment_delay
from src.action_optimizer import rank_actions
from src.agent import generate_agent_brief
from src.network_risk import propagate_payment_shock
from src.copilot_features import explain_cashflow_question, ask_optional_llm, risk_radar, financing_options, counterparty_vulnerability, rule_based_chat, ask_local_ollama
from src.security import require_permission, AuthorizationError, make_audit_record
from src.auth_store import init_db, user_count, create_user, authenticate, write_audit, read_audit
from src.security_policy import authorize
from src.input_quality import transaction_quality_report, network_quality_report, build_scenario_transactions

ROOT=Path(__file__).parent
st.set_page_config(page_title="CashFlow Sentinel AI",page_icon="🛡️",layout="wide")

if "appearance_mode" not in st.session_state:
    st.session_state.appearance_mode = "Light"

brand_column, theme_column = st.columns([4, 1.35])
with brand_column:
    st.markdown(
        '<div class="top-brand"><span class="top-brand-mark">C</span>'
        '<span><strong>CashFlow Sentinel AI</strong>'
        '<small>SME FINANCE COPILOT</small></span></div>',
        unsafe_allow_html=True,
    )
with theme_column:
    st.radio(
        "Appearance",
        ("Light", "Dark"),
        horizontal=True,
        key="appearance_mode",
    )

dark_mode = st.session_state.appearance_mode == "Dark"
theme_tokens = (
    {
        "app": "#081329",
        "surface": "#10203d",
        "surface_muted": "#152847",
        "text": "#edf4ff",
        "muted": "#a7b6cc",
        "border": "#293c5c",
        "primary": "#5b9aff",
        "primary_hover": "#80b1ff",
        "success": "#38c99a",
        "warning": "#f0b653",
        "error": "#ff7581",
        "shadow": "0 18px 48px rgba(0, 0, 0, .24)",
    }
    if dark_mode
    else {
        "app": "#f4f7fd",
        "surface": "#ffffff",
        "surface_muted": "#f7f9fd",
        "text": "#101c36",
        "muted": "#64748b",
        "border": "#dce5f3",
        "primary": "#2878f0",
        "primary_hover": "#1e64d4",
        "success": "#16a779",
        "warning": "#b87516",
        "error": "#d83f51",
        "shadow": "0 18px 48px rgba(16, 38, 80, .08)",
    }
)
st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
        --cfs-app: {theme_tokens["app"]};
        --cfs-surface: {theme_tokens["surface"]};
        --cfs-muted-surface: {theme_tokens["surface_muted"]};
        --cfs-text: {theme_tokens["text"]};
        --cfs-muted: {theme_tokens["muted"]};
        --cfs-border: {theme_tokens["border"]};
        --cfs-primary: {theme_tokens["primary"]};
        --cfs-primary-hover: {theme_tokens["primary_hover"]};
        --cfs-success: {theme_tokens["success"]};
        --cfs-warning: {theme_tokens["warning"]};
        --cfs-error: {theme_tokens["error"]};
        --cfs-shadow: {theme_tokens["shadow"]};
    }}
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background: var(--cfs-app);
        color: var(--cfs-text);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stAppViewContainer"] > .main .block-container {{
        max-width: 1440px;
        padding: 1.25rem clamp(1rem, 3vw, 2.75rem) 3rem;
    }}
    .top-brand {{ display: flex; align-items: center; gap: .75rem; min-height: 3rem; color: var(--cfs-text); }}
    .top-brand-mark {{
        display: grid; place-items: center; width: 2.55rem; height: 2.55rem;
        border-radius: .85rem; color: white; font-weight: 800; font-size: 1.25rem;
        background: linear-gradient(140deg, #2878f0, #16c8e8);
        box-shadow: 0 7px 18px rgba(40, 120, 240, .2);
    }}
    .top-brand strong {{ display: block; font-size: 1rem; letter-spacing: -.02em; }}
    .top-brand small {{ display: block; margin-top: .12rem; color: var(--cfs-muted); font-size: .62rem; letter-spacing: .15em; }}
    [data-testid="stSidebar"] {{ background: var(--cfs-surface); border-right: 1px solid var(--cfs-border); }}
    [data-testid="stSidebar"] * {{ color: var(--cfs-text); }}
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {{
        color: var(--cfs-text);
    }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: var(--cfs-muted) !important; }}
    h1, h2, h3 {{ letter-spacing: -.035em; }}
    h2 {{ margin-top: 1.7rem !important; padding-top: .65rem; border-top: 1px solid var(--cfs-border); }}
    [data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stForm"], div[data-testid="stExpander"] > details {{
        background: var(--cfs-surface);
        border-color: var(--cfs-border) !important;
        border-radius: 16px;
        box-shadow: var(--cfs-shadow);
    }}
    [data-testid="stMetric"] {{ padding: 1rem 1.15rem; }}
    [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {{ color: var(--cfs-muted) !important; }}
    [data-testid="stMetricValue"] {{ color: var(--cfs-text) !important; }}
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {{
        background: var(--cfs-surface) !important;
        color: var(--cfs-text) !important;
        border-color: var(--cfs-border) !important;
    }}
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
        background: var(--cfs-surface) !important;
        border-color: var(--cfs-border) !important;
    }}
    [role="option"], [data-baseweb="menu"] * {{ color: var(--cfs-text) !important; }}
    [role="option"]:hover, [role="option"][aria-selected="true"] {{
        background: var(--cfs-muted-surface) !important;
    }}
    [data-testid="stCheckbox"] input {{ accent-color: var(--cfs-primary); }}
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{
        border-color: var(--cfs-primary);
    }}
    input::placeholder, textarea::placeholder {{ color: var(--cfs-muted) !important; opacity: .8; }}
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
    [data-testid="stFormSubmitButton"] button {{
        border-radius: 10px;
        border-color: var(--cfs-border);
        color: var(--cfs-text);
        transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
    }}
    [data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        border-color: var(--cfs-primary);
        color: var(--cfs-primary);
        transform: translateY(-1px);
    }}
    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"] {{
        color: #fff; background: var(--cfs-primary); border-color: var(--cfs-primary);
        font-weight: 700;
    }}
    [data-testid="stButton"] button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {{
        color: #fff; background: var(--cfs-primary-hover); border-color: var(--cfs-primary-hover);
    }}
    button:focus-visible, input:focus-visible, textarea:focus-visible {{
        outline: 3px solid #16c8e8 !important; outline-offset: 2px !important;
    }}
    [data-testid="stAlert"] {{
        background: var(--cfs-muted-surface);
        color: var(--cfs-text);
        border: 1px solid var(--cfs-border);
        border-radius: 12px;
    }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        border: 1px solid var(--cfs-border); border-radius: 12px; overflow: hidden;
    }}
    [data-testid="stRadio"] label {{ color: var(--cfs-text); }}
    .login-hero {{
        position: relative; overflow: hidden; min-height: 610px; padding: clamp(1.6rem, 4vw, 3.5rem);
        border-radius: 26px; color: #f5f8ff;
        background:
            radial-gradient(ellipse at 92% 14%, rgba(22, 200, 232, .22), transparent 32%),
            radial-gradient(ellipse at 8% 90%, rgba(82, 104, 248, .22), transparent 35%),
            linear-gradient(145deg, #081329 0%, #102650 68%, #153665 100%);
        box-shadow: 0 24px 64px rgba(8, 19, 41, .2);
    }}
    .hero-brand {{ display: flex; align-items: center; gap: .8rem; }}
    .hero-mark {{
        display: grid; place-items: center; width: 2.9rem; height: 2.9rem; border-radius: 1rem;
        color: white; background: linear-gradient(145deg, #2878f0, #16c8e8);
        box-shadow: 0 8px 24px rgba(22, 200, 232, .2);
    }}
    .hero-brand-name {{ font-size: 1.05rem; font-weight: 750; letter-spacing: -.02em; }}
    .hero-kicker {{ margin: 2.1rem 0 .75rem; color: #78dff1; font-size: .68rem; font-weight: 750; letter-spacing: .18em; }}
    .login-hero h1 {{ max-width: 620px; margin: 0; color: #fff; font-size: clamp(2rem, 4vw, 3.35rem); line-height: 1.08; letter-spacing: -.055em; }}
    .hero-copy {{ max-width: 590px; margin: 1rem 0 1.5rem; color: #c2d1e8; font-size: 1rem; line-height: 1.7; }}
    .hero-visual {{
        position: relative; height: 94px; margin: .4rem 0 1.45rem; overflow: hidden;
        border: 1px solid rgba(177, 209, 255, .14); border-radius: 14px;
        background: linear-gradient(90deg, rgba(255,255,255,.03), rgba(22,200,232,.08));
    }}
    .hero-visual:before, .hero-visual:after {{
        position: absolute; content: ""; left: 0; right: 0; height: 1px;
        background: rgba(183, 212, 255, .13);
    }}
    .hero-visual:before {{ top: 31px; }} .hero-visual:after {{ top: 63px; }}
    .hero-line {{
        position: absolute; inset: 20px 4% 10px; width: 92%; height: 65px;
    }}
    .feature-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }}
    .feature-item {{
        display: flex; align-items: center; gap: .7rem; min-height: 60px; padding: .65rem .75rem;
        border: 1px solid rgba(194, 215, 248, .16); border-radius: 12px;
        background: rgba(255,255,255,.055); color: #edf4ff; font-size: .85rem; font-weight: 600;
    }}
    .feature-icon {{ display: grid; place-items: center; flex: 0 0 30px; height: 30px; border-radius: 9px; color: #77e3f2; background: rgba(22,200,232,.12); }}
    .hero-disclaimer {{ margin-top: 1.4rem; color: #9fb2cf; font-size: .72rem; line-height: 1.5; }}
    .auth-heading {{ margin: .25rem 0 .25rem; font-size: 1.75rem; font-weight: 760; letter-spacing: -.04em; }}
    .auth-copy {{ margin: 0 0 1.15rem; color: var(--cfs-muted); line-height: 1.6; }}
    .auth-kicker {{ color: var(--cfs-primary); font-size: .68rem; font-weight: 750; letter-spacing: .15em; }}
    @media (max-width: 760px) {{
        [data-testid="stAppViewContainer"] > .main .block-container {{ padding: .8rem .75rem 2rem; }}
        .login-hero {{ min-height: auto; padding: 1.4rem; border-radius: 18px; }}
        .hero-kicker {{ margin-top: 1.4rem; }}
        .login-hero h1 {{ font-size: 2rem; }}
        .hero-visual {{ height: 72px; }}
        .feature-grid {{ gap: .5rem; }}
        .feature-item {{ min-height: 54px; padding: .5rem; font-size: .76rem; }}
        .top-brand strong {{ font-size: .9rem; }}
        .top-brand small {{ font-size: .55rem; }}
    }}
    @media (max-width: 420px) {{
        .feature-grid {{ grid-template-columns: 1fr; }}
        .top-brand-mark {{ width: 2.25rem; height: 2.25rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        *, *:before, *:after {{ scroll-behavior: auto !important; transition-duration: .01ms !important; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def record_auth_audit(*args):
    try:
        write_audit(*args)
    except (OSError, sqlite3.Error) as exc:
        return f"Security audit record could not be saved: {exc}"
    return None


def style_chart(figure):
    figure.update_layout(
        paper_bgcolor=theme_tokens["surface"],
        plot_bgcolor=theme_tokens["surface"],
        font={"color": theme_tokens["text"]},
        legend={"font": {"color": theme_tokens["text"]}},
        margin={"l": 20, "r": 20, "t": 28, "b": 20},
    )
    figure.update_xaxes(
        color=theme_tokens["muted"],
        gridcolor=theme_tokens["border"],
        zerolinecolor=theme_tokens["border"],
    )
    figure.update_yaxes(
        color=theme_tokens["muted"],
        gridcolor=theme_tokens["border"],
        zerolinecolor=theme_tokens["border"],
    )
    return figure


def render_login_panel():
    st.markdown(
        """
        <section class="login-hero" aria-label="CashFlow Sentinel AI product overview">
          <div class="hero-brand">
            <span class="hero-mark" aria-hidden="true">
              <svg width="25" height="25" viewBox="0 0 24 24" fill="none">
                <path d="M4 17.5 9 12l3.2 3.1L20 7" stroke="white" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M15.5 7H20v4.5" stroke="white" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span class="hero-brand-name">CashFlow Sentinel AI</span>
          </div>
          <p class="hero-kicker">SME FINANCE COPILOT</p>
          <h1>Cash flow clarity, built for better decisions.</h1>
          <p class="hero-copy">See how payment timing may affect liquidity, explore cash-flow scenarios,
            and compare practical options with evidence and uncertainty kept in view.</p>
          <div class="hero-visual" role="img" aria-label="Abstract cash-flow line illustration">
            <svg class="hero-line" viewBox="0 0 600 70" preserveAspectRatio="none" aria-hidden="true">
              <defs><linearGradient id="flow" x1="0" x2="1">
                <stop offset="0" stop-color="#2878f0"/><stop offset="1" stop-color="#16c8e8"/>
              </linearGradient></defs>
              <path d="M0 50 C50 50 55 29 105 35 S165 57 215 42 270 18 320 28 380 51 430 31 500 34 600 8"
                fill="none" stroke="url(#flow)" stroke-width="3" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="feature-grid">
            <div class="feature-item"><span class="feature-icon">↗</span>Forecast cash flow</div>
            <div class="feature-item"><span class="feature-icon">⌁</span>Simulate risks</div>
            <div class="feature-item"><span class="feature-icon">⇄</span>Compare options</div>
            <div class="feature-item"><span class="feature-icon">✓</span>Human-controlled decisions</div>
          </div>
          <p class="hero-disclaimer">Prototype for decision support. Forecasts are scenarios, not guarantees;
            all real-world actions remain under human control.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

# Local account authentication. Roles are loaded from SQLite, never chosen by the user in the dashboard.
init_db()
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
has_users = user_count() > 0
if not st.session_state.auth_user:
    left, right = st.columns([1.12, 1])
    with left:
        render_login_panel()
    with right:
        with st.container(border=True):
            if has_users:
                st.markdown('<p class="auth-kicker">SECURE WORKSPACE ACCESS</p>', unsafe_allow_html=True)
                st.markdown('<div class="auth-heading">Welcome back</div>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="auth-copy">Sign in to access your CashFlow Sentinel AI workspace.</p>',
                    unsafe_allow_html=True,
                )
                login_user = st.text_input("Username", key="login_username", placeholder="Your username")
                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                    placeholder="Your password",
                )
                if st.button("Sign in", type="primary", use_container_width=True, key="login_submit"):
                    user = authenticate(login_user, login_password)
                    if user:
                        st.session_state.auth_user = user
                        audit_warning = record_auth_audit(
                            user["username"], user["role"], "LOGIN", "local_app", "success"
                        )
                        if audit_warning:
                            st.session_state.auth_audit_warning = audit_warning
                        st.rerun()
                    else:
                        audit_warning = record_auth_audit(
                            login_user.strip().lower() or "unknown",
                            "viewer",
                            "LOGIN",
                            "local_app",
                            "denied",
                            "Invalid credentials",
                        )
                        st.error("Invalid username or password.")
                        if audit_warning:
                            st.warning(audit_warning)
                st.caption("New to this workspace? Ask your owner to create your account.")
            else:
                st.markdown('<p class="auth-kicker">LOCAL ACCOUNT SETUP</p>', unsafe_allow_html=True)
                st.markdown('<div class="auth-heading">Create your owner account</div>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="auth-copy">Set up the first local owner. Your password must be at least 12 characters.</p>',
                    unsafe_allow_html=True,
                )
                new_user = st.text_input("Owner username", key="first_owner_username")
                pw1 = st.text_input(
                    "Owner password",
                    type="password",
                    key="first_owner_password",
                )
                pw2 = st.text_input(
                    "Confirm password",
                    type="password",
                    key="first_owner_confirm",
                )
                if st.button(
                    "Create owner account",
                    type="primary",
                    use_container_width=True,
                    key="first_owner_create",
                ):
                    if pw1 != pw2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            created_username = create_user(new_user, pw1, "owner")
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            audit_warning = record_auth_audit(
                                created_username,
                                "owner",
                                "ACCOUNT_CREATED",
                                "local_owner",
                                "success",
                                "First local owner account created",
                            )
                            if audit_warning:
                                st.session_state.auth_audit_warning = audit_warning
                            st.session_state.auth_notice = "Owner account created. Sign in with your new credentials."
                            st.rerun()
                st.caption("This local prototype account store is not intended for internet-facing production use.")
            if st.session_state.get("auth_notice"):
                st.success(st.session_state.pop("auth_notice"))
            if st.session_state.get("auth_audit_warning"):
                st.warning(st.session_state.pop("auth_audit_warning"))
    st.stop()

current_user = st.session_state.auth_user
if st.session_state.get("auth_audit_warning"):
    st.warning(st.session_state.pop("auth_audit_warning"))
st.caption("SME Finance Copilot · Explainable liquidity risk and scenario decision support")
st.warning("DEMO ONLY — bundled data are synthetic. No bank connection, real payment, lending decision, or external message is performed.")
with st.sidebar:
    st.success(f"Signed in: {current_user['username']} · {current_user['role'].title()}")
    if st.button("Sign out"):
        write_audit(current_user['username'], current_user['role'], "LOGOUT", "local_app", "success")
        for key in [
            "copilot_answer",
            "time_machine_compare",
            "time_machine_forecasts",
            "time_machine_notes",
            "time_machine_config",
            "network_propagation_result",
            "last_network_result",
            "last_network_seed",
            "demo_audit_log",
            "v05_audit_records",
            "login_username",
            "login_password",
        ]:
            st.session_state.pop(key, None)
        st.session_state.auth_user = None
        st.rerun()
    if current_user['role'] == 'owner':
        with st.expander("Owner: create user"):
            with st.form("create_user_form"):
                uname = st.text_input("New username")
                upass = st.text_input("Temporary password (12+ characters)", type="password")
                urole = st.selectbox("Role", ["viewer", "analyst", "owner"])
                user_submit = st.form_submit_button("Create user")
            if user_submit:
                try:
                    create_user(uname, upass, urole)
                    write_audit(current_user['username'], current_user['role'], "USER_CREATED", uname, "success", f"Assigned role {urole}")
                    st.success("User created. Share credentials securely and ask them to change the password outside this demo if supported.")
                except ValueError as exc: st.error(str(exc))
role = {"viewer":"Tier 0 — Viewer", "analyst":"Tier 1 — Analyst", "owner":"Tier 2 — Owner review"}[current_user['role']]
@st.cache_data
def load_sample():
    return validate_transactions(pd.read_csv(ROOT/"data/sample_transactions.csv")),validate_network(pd.read_csv(ROOT/"data/sample_network.csv"))
try: sample_tx,sample_net=load_sample()
except Exception as e: st.error(f"Sample data error: {e}"); st.stop()
with st.sidebar:
    st.header("Data")
    upload=st.checkbox("Use uploaded CSVs")
    txfile=st.file_uploader("Transactions CSV",type=["csv"],disabled=not upload)
    netfile=st.file_uploader("Network CSV",type=["csv"],disabled=not upload)
    if upload and txfile and netfile:
        try:
            transactions=validate_transactions(pd.read_csv(txfile)); network=validate_network(pd.read_csv(netfile))
            tq = transaction_quality_report(transactions); nq = network_quality_report(network)
            st.success("Schema validation passed")
            with st.expander("Upload data-quality report", expanded=bool(tq["warnings"] or nq["warnings"])):
                st.write({"transactions": tq, "network": nq})
                st.caption("Duplicate-like rows are flagged, not automatically removed, because they may be separate legitimate transactions. Reconcile against your accounting system before using real data.")
        except Exception as e: st.error(f"Validation failed: {e}"); st.stop()
    elif upload: st.info("Upload both files to continue."); st.stop()
    else: transactions,network=sample_tx.copy(),sample_net.copy()
    businesses=transactions[["business_id","business_name"]].drop_duplicates()
    selected=st.selectbox("Business",businesses.business_id.tolist(),format_func=lambda x: businesses.loc[businesses.business_id==x,"business_name"].iloc[0])
    start=st.date_input("Forecast start date",value=transactions.date.min().date())
    horizon=st.slider("Horizon (days)",7,60,30)
    opening=st.number_input("Opening cash (currency units)",min_value=0.0,value=100000.0,step=5000.0)

st.subheader("1. Baseline forecast")
base=forecast_business(transactions,selected,opening,start,horizon); summary=summarize_forecast(base)
a,b,c=st.columns(3); a.metric("Ending cash",f"{summary['ending_cash']:,.0f}"); b.metric("Minimum cash",f"{summary['minimum_cash']:,.0f}"); c.metric("Shortfall days",summary["shortfall_days"])
if summary["first_shortfall_date"]: st.error(f"Potential negative cash begins {summary['first_shortfall_date']} (modelled scenario, not certainty).")
else: st.success("No negative closing balance in this baseline; liquidity is not guaranteed.")
fig=go.Figure(); fig.add_trace(go.Scatter(x=base.date,y=base.closing_cash,mode="lines+markers",name="Baseline")); fig.add_hline(y=0,line_dash="dash",annotation_text="Zero cash"); fig.update_layout(xaxis_title="Date",yaxis_title="Closing cash",height=350); st.plotly_chart(style_chart(fig),use_container_width=True)
with st.expander("Daily forecast table"): st.dataframe(base,use_container_width=True,hide_index=True)

st.subheader("2. Payment-delay shock test")
st.write("This deterministic stress test shifts a selected incoming payment date. It does not predict the probability of a delay.")
edges=network[network.to_business_id.astype(str)==str(selected)]
if edges.empty: st.info("No incoming network edge for this business in the current sample.")
else:
    labels=edges.apply(lambda r:f"{r.from_business_id} → {r.to_business_id} | {r.amount:,.0f}",axis=1).tolist(); choice=st.selectbox("Payer → receiver",labels); edge=edges.iloc[labels.index(choice)]; delay=st.slider("Simulated delay (days)",0,30,10)
    if st.button("Run shock simulation",type="primary"):
        try:
            require_permission(role, "run_simulation")
            changed,_=apply_payment_delay(transactions,network,edge.from_business_id,edge.to_business_id,delay); scenario=forecast_business(changed,selected,opening,start,horizon); ss=summarize_forecast(scenario)
            x,y,z=st.columns(3); x.metric("Scenario ending cash",f"{ss['ending_cash']:,.0f}",delta=f"{ss['ending_cash']-summary['ending_cash']:,.0f} vs baseline"); y.metric("Scenario minimum cash",f"{ss['minimum_cash']:,.0f}"); z.metric("Scenario shortfall days",ss["shortfall_days"],delta=ss["shortfall_days"]-summary["shortfall_days"])
            chart=go.Figure(); chart.add_trace(go.Scatter(x=base.date,y=base.closing_cash,name="Baseline",mode="lines+markers")); chart.add_trace(go.Scatter(x=scenario.date,y=scenario.closing_cash,name=f"{delay}-day delay",mode="lines+markers")); chart.add_hline(y=0,line_dash="dash"); chart.update_layout(xaxis_title="Date",yaxis_title="Closing cash",height=350); st.plotly_chart(style_chart(chart),use_container_width=True)
            st.info("This single-receiver chart is distinct from the multi-hop network stress simulation in section 3. Both are deterministic scenarios, not calibrated probability predictions.")
            log=pd.DataFrame([{"event":"SIMULATED_PAYMENT_DELAY","payer":edge.from_business_id,"receiver":edge.to_business_id,"delay_days":delay,"baseline_ending_cash":summary["ending_cash"],"scenario_ending_cash":ss["ending_cash"],"human_approval_required":True,"external_action_executed":False}])
            st.download_button("Download simulated action log CSV",log.to_csv(index=False),"simulated_action_log.csv","text/csv")
        except Exception as e: st.error(f"Scenario error: {e}")

st.subheader("3. Network-wide payment-shock propagation")
st.caption("Deterministic multi-hop stress test over connected payment edges. This is a scenario, not a calibrated probability forecast.")
if network.empty:
    st.info("No network records available.")
else:
    network_payers = sorted(network["from_business_id"].astype(str).unique().tolist())
    shock_payer = st.selectbox("Shock origin (payer)", network_payers, key="network_shock_payer")
    network_delay = st.slider("Initial shock delay (days)", 0, 30, 10, key="network_shock_delay")
    liquidity_buffer = st.number_input("Assumed liquidity buffer per connected edge", min_value=0.0, value=20000.0, step=5000.0, key="network_buffer")
    max_hops = st.slider("Maximum propagation hops", 1, 10, 5, key="network_max_hops")
    if st.button("Run multi-hop network simulation", type="primary", key="run_network_simulation"):
        try:
            require_permission(role, "run_simulation")
            propagation = propagate_payment_shock(network, shock_payer, int(network_delay), float(liquidity_buffer), int(max_hops))
            st.session_state["network_propagation_result"] = propagation
            write_audit(current_user["username"], current_user["role"], "NETWORK_STRESS_TEST", shock_payer, "success",
                        f"delay_days={network_delay}; buffer={liquidity_buffer}; hops={max_hops}; edges={len(propagation)}")
        except (AuthorizationError, ValueError, TypeError) as exc:
            st.error(f"Network simulation failed: {exc}")
    if "network_propagation_result" in st.session_state:
        propagation = st.session_state["network_propagation_result"]
        if propagation.empty:
            st.info("No connected payment edges were reached for this shock origin and hop limit.")
        else:
            st.metric("Edges examined", len(propagation))
            affected = propagation[propagation["propagation_triggered"]]
            st.metric("Edges where shock propagates under assumptions", len(affected))
            st.dataframe(propagation, use_container_width=True, hide_index=True)
            try:
                require_permission(role, "export_simulated_log")
                st.download_button("Download network propagation evidence CSV", propagation.to_csv(index=False), "network_propagation_evidence.csv", "text/csv")
            except AuthorizationError:
                st.info("Evidence export requires Analyst or Owner role in this demo policy.")

st.subheader("4. Illustrative action comparison")
st.caption("Amounts below are editable assumptions, not model predictions.")
gap=st.number_input("Estimated cash gap",min_value=0.0,value=30000.0,step=5000.0)
def action(name,relief,cost,feasible,evidence,uncertainty): return {"name":name,"estimated_cash_relief":relief,"estimated_cost":cost,"feasible":feasible,"evidence":evidence,"uncertainty":uncertainty}
actions=[action("Request early customer payment",25000,0,True,"Open invoice must be confirmed","High: customer may decline or pay late"),action("Negotiate supplier payment date",20000,1000,True,"Supplier bill due soon; agreement required","Medium/high: supplier approval required"),action("Delay optional inventory purchase",15000,2500,True,"Optional purchase; check stock and sales impact","Medium: stockout or lost sales risk"),action("New short-term borrowing",30000,3500,False,"Disabled: no lending integration","High: eligibility and repayment burden unknown")]
with st.expander("Edit action assumptions"):
    for i,a0 in enumerate(actions):
        a0["estimated_cash_relief"]=st.number_input(f"{a0['name']} relief",min_value=0.0,value=float(a0["estimated_cash_relief"]),step=2500.0,key=f"relief{i}")
        a0["estimated_cost"]=st.number_input(f"{a0['name']} cost",min_value=0.0,value=float(a0["estimated_cost"]),step=500.0,key=f"cost{i}")
        a0["feasible"]=st.checkbox(f"{a0['name']} feasible?",value=bool(a0["feasible"]),key=f"feasible{i}")
ranked=rank_actions(actions,gap); st.dataframe(pd.DataFrame([{"Action":r["name"],"Estimated relief":r["estimated_cash_relief"],"Estimated cost":r["estimated_cost"],"Net benefit estimate":r["net_estimated_benefit"],"Feasible":r["feasible"],"Evidence/assumption":r["evidence"],"Uncertainty/trade-off":r["uncertainty"],"Covers gap":r["covers_shortfall"]} for r in ranked]),use_container_width=True,hide_index=True)
st.warning("No action is executed. Verify assumptions and obtain business-owner approval before taking any real-world action.")

st.subheader("5. AI Agent — explainable decision brief")
st.caption("This MVP uses transparent rules over forecast and transaction records. It is an agent-style decision-support prototype, not a generative LLM or trained ML model.")
brief = generate_agent_brief(transactions, selected, base)
st.info(f"Agent type: {brief['agent_type']}")
st.write(brief["model_note"])
for item in brief["actions"]:
    with st.container(border=True):
        st.markdown(f"**{item['priority']} · {item['recommendation']}**")
        st.write(item["reason"])
        st.caption(f"Evidence: {item['evidence']}")
        st.caption(f"Uncertainty: {item['uncertainty']}")
        st.caption(f"Control: {item['approval']}")

st.subheader("6. Security controls & human approval")
st.warning("Permissions are linked to the authenticated local account. This prototype login is not a production identity provider; do not expose it to the public internet or upload highly sensitive data.")
if role.startswith("Tier 0"):
    st.info("Viewer mode: view forecasts and agent brief only. Simulation, exports, and review recording are blocked by policy.")
elif role.startswith("Tier 1"):
    st.info("Analyst mode: run simulations and export simulated evidence. Recording owner review decisions is blocked.")
else:
    st.info("Owner-review mode: run simulations, export evidence, and record human review decisions. No external action is available.")
with st.form("approval_form"):
    proposed_action = st.selectbox("Action to review", [a["name"] for a in actions])
    decision = st.radio("Review decision", ["Needs more evidence", "Approved for human follow-up", "Rejected"], horizontal=True)
    note = st.text_input("Reason / evidence note", max_chars=250)
    submitted = st.form_submit_button("Record review decision")
    if submitted:
        try:
            record = make_audit_record(role, proposed_action, decision, note, pd.Timestamp.now(tz="UTC").isoformat())
            if "demo_audit_log" not in st.session_state:
                st.session_state["demo_audit_log"] = []
            st.session_state["demo_audit_log"].append(record)
            write_audit(current_user["username"], current_user["role"], "HUMAN_REVIEW", proposed_action, decision, note)
            st.success("Review decision saved to persistent local SQLite audit log. No real-world action was executed.")
        except (AuthorizationError, ValueError) as e:
            st.error(str(e))
if st.session_state.get("demo_audit_log"):
    audit = pd.DataFrame(st.session_state["demo_audit_log"])
    st.dataframe(audit, use_container_width=True, hide_index=True)
    try:
        require_permission(role, "export_simulated_log")
        st.download_button("Download demo security audit log CSV", audit.to_csv(index=False), "demo_security_audit_log.csv", "text/csv")
    except AuthorizationError:
        st.info("Audit log export requires Tier 1 Analyst or Tier 2 Owner in this demo policy.")


st.subheader("7. Enforced demo authorization checks")
st.caption("Role comes from the signed-in local account. This local prototype is not production-grade IAM.")
demo_role = current_user["role"]
st.caption(f"Authenticated role from local account store: {demo_role}")
requested_permission = st.selectbox("Permission to check", ["view", "simulate", "export", "review"], key="requested_permission")
if st.button("Check authorization", key="check_authorization"):
    try:
        authorize(demo_role, requested_permission)
        st.success(f"ALLOW: {demo_role} may perform '{requested_permission}'.")
    except AuthorizationError as exc:
        st.error(f"BLOCKED: {exc}")
with st.form("owner_review_v05"):
    st.write("Human review record (owner permission required)")
    review_action = st.text_input("Proposed action", value="Request customer payment confirmation", max_chars=120)
    review_decision = st.selectbox("Review decision", ["Needs more evidence", "Approved for human follow-up", "Rejected"])
    review_note = st.text_input("Review note", max_chars=250)
    review_submit = st.form_submit_button("Record review decision")
    if review_submit:
        try:
            audit_record = make_audit_record(
                role,
                review_action,
                review_decision,
                review_note,
                pd.Timestamp.now(tz="UTC").isoformat(),
            )
            if "v05_audit_records" not in st.session_state:
                st.session_state["v05_audit_records"] = []
            st.session_state["v05_audit_records"].append(audit_record)
            write_audit(
                current_user["username"],
                current_user["role"],
                "HUMAN_REVIEW",
                review_action,
                review_decision,
                review_note,
            )
            st.success("Review decision saved to persistent local SQLite audit log. No external action was executed.")
        except (AuthorizationError, ValueError) as exc:
            st.error(f"BLOCKED: {exc}")
if current_user["role"] == "owner":
    persisted = pd.DataFrame(read_audit())
    if not persisted.empty:
        st.markdown("**Persistent audit log (SQLite)**")
        st.dataframe(persisted, use_container_width=True, hide_index=True)
        st.download_button("Download persistent audit log CSV", persisted.to_csv(index=False), "persistent_audit_log.csv", "text/csv")


st.subheader("8. Finance Chat — Python Rules + Free Local AI")
st.caption("Python rules work offline. Optional Ollama mode runs a small language model locally; no OpenAI API key is needed. Financial calculations remain in Python.")
chat_mode = st.radio("Chat engine", ["Python Rule-Based (offline)", "Ollama Local AI (free)"] , horizontal=True, key="finance_chat_mode")
if chat_mode == "Ollama Local AI (free)":
    ollama_model = st.text_input("Local Ollama model", value="qwen2.5:3b", help="For 8 GB RAM, start with qwen2.5:3b. If slow, try qwen2.5:1.5b.", key="ollama_model")
    ollama_url = st.text_input("Ollama URL", value="http://localhost:11434", key="ollama_url")
else:
    ollama_model = "qwen2.5:3b"
    ollama_url = "http://localhost:11434"
question = st.text_input("Ask about this business", placeholder="Why is my cash decreasing? / Is there a cash shortage risk? / Which customer payments matter most?", key="finance_chat_question")
if st.button("Ask Finance Copilot", type="primary", key="ask_finance_copilot"):
    try:
        require_permission(role, "view_agent")
        if not question.strip():
            st.warning("Enter a question first.")
        elif chat_mode == "Ollama Local AI (free)":
            with st.spinner("Waiting for local Ollama model..."):
                answer = ask_local_ollama(question, transactions, selected, base, ollama_model, ollama_url)
            st.session_state["copilot_answer"] = answer
        else:
            answer = rule_based_chat(question, transactions, selected, base)
            st.session_state["copilot_answer"] = answer
    except Exception as exc:
        st.error(f"Chat could not answer: {exc}")
        if chat_mode == "Ollama Local AI (free)":
            st.info("Fallback: switch to Python Rule-Based (offline), or check that Ollama is running and the selected model is installed.")
if st.session_state.get("copilot_answer"):
    answer = st.session_state["copilot_answer"]
    st.caption("Mode: " + answer.get("mode", "Python rule-based chat"))
    st.markdown(answer.get("answer", "No answer returned."))
    st.caption("Uncertainty: " + answer.get("uncertainty", "Verify against the underlying records."))
    with st.expander("Evidence used for this answer", expanded=True):
        evidence = answer.get("evidence", pd.DataFrame())
        if isinstance(evidence, pd.DataFrame) and not evidence.empty:
            st.dataframe(evidence, use_container_width=True, hide_index=True)
        else:
            st.info("No row-level evidence was needed for this response. Check the selected business and data coverage.")
    if st.button("Clear chat answer", key="clear_finance_chat"):
        st.session_state.pop("copilot_answer", None)
        st.rerun()

st.subheader("9. Explainable Financial Risk Radar")
radar = risk_radar(transactions, network, selected, base)
st.dataframe(radar, use_container_width=True, hide_index=True)
st.caption("Severity labels follow simple demo thresholds, not calibrated probabilities or regulated credit-risk scores.")

st.subheader("10. Smart Financing & Micro-Loan — mock comparison")
st.caption("Illustrative products only. These are not live offers, market quotes, loan eligibility decisions, or financial advice.")
financing_gap = st.number_input("Cash gap to finance (currency units)", min_value=0.0, value=30000.0, step=5000.0, key="financing_gap")
financing = financing_options(financing_gap)
st.dataframe(financing, use_container_width=True, hide_index=True)
st.info("Rates, fees and approval speeds are synthetic assumptions. Confirm real APR, fees, collateral, recourse, eligibility and repayment terms with regulated providers before making a decision.")

st.subheader("11. Supply Chain Cascade Risk & Counterparty Vulnerability Matrix")
st.caption("Top counterparties ranked by recorded exposure amount. This is an exposure proxy, not a default probability.")
vulnerability = counterparty_vulnerability(transactions, network, selected)
if vulnerability.empty:
    st.info("No counterparty records found for the selected business.")
else:
    st.dataframe(vulnerability, use_container_width=True, hide_index=True)
    st.markdown("**Top 3 critical bottlenecks**")
    for _, row in vulnerability.head(3).iterrows():
        st.write(f"- **{row['Counterparty']}** — exposure {row['Exposure amount']:,.0f}; score {row['Criticality score']:.1f}/100. Evidence: {row['Evidence']}. Uncertainty: {row['Uncertainty']}.")

st.subheader("12. Financial Time Machine — Baseline vs Scenario A vs Scenario B")
st.caption("Compare two independent what-if scenarios against the same baseline. Results are deterministic cash-flow simulations, not probability forecasts. Price reduction is a conservative cash-impact assumption, not a demand or margin model.")
scenario_types = ["No change", "Customer payment delayed", "Inventory purchase", "Price reduced"]
sc_a, sc_b = st.columns(2)
with sc_a:
    st.markdown("**Scenario A**")
    type_a = st.selectbox("Scenario A type", scenario_types, index=1, key="tm_type_a")
    amount_a = st.number_input("Scenario A amount", min_value=0.0, value=50000.0, step=5000.0, key="tm_amount_a")
    days_a = st.slider("Scenario A delay / offset (days)", 0, 30, 15, key="tm_days_a")
    price_a = st.slider("Scenario A price reduction (%)", 0, 100, 10, key="tm_price_a")
with sc_b:
    st.markdown("**Scenario B**")
    type_b = st.selectbox("Scenario B type", scenario_types, index=2, key="tm_type_b")
    amount_b = st.number_input("Scenario B amount", min_value=0.0, value=50000.0, step=5000.0, key="tm_amount_b")
    days_b = st.slider("Scenario B delay / offset (days)", 0, 30, 7, key="tm_days_b")
    price_b = st.slider("Scenario B price reduction (%)", 0, 100, 10, key="tm_price_b")
if st.button("Compare Baseline vs A vs B", type="primary", key="run_time_machine"):
    try:
        require_permission(role, "run_simulation")
        tx_a, note_a = build_scenario_transactions(transactions, selected, "Baseline" if type_a == "No change" else type_a, amount_a, days_a, start, horizon, price_a)
        tx_b, note_b = build_scenario_transactions(transactions, selected, "Baseline" if type_b == "No change" else type_b, amount_b, days_b, start, horizon, price_b)
        fc_a = forecast_business(tx_a, selected, opening, start, horizon)
        fc_b = forecast_business(tx_b, selected, opening, start, horizon)
        sum_a, sum_b = summarize_forecast(fc_a), summarize_forecast(fc_b)
        compare = pd.DataFrame([
            {"Scenario":"Baseline", "Ending cash":summary["ending_cash"], "Minimum cash":summary["minimum_cash"], "Shortage days":summary["shortfall_days"], "Change in ending cash":0.0},
            {"Scenario":f"A — {type_a}", "Ending cash":sum_a["ending_cash"], "Minimum cash":sum_a["minimum_cash"], "Shortage days":sum_a["shortfall_days"], "Change in ending cash":sum_a["ending_cash"]-summary["ending_cash"]},
            {"Scenario":f"B — {type_b}", "Ending cash":sum_b["ending_cash"], "Minimum cash":sum_b["minimum_cash"], "Shortage days":sum_b["shortfall_days"], "Change in ending cash":sum_b["ending_cash"]-summary["ending_cash"]},
        ])
        st.session_state["time_machine_compare"] = compare
        st.session_state["time_machine_forecasts"] = {"Baseline":base, f"A — {type_a}":fc_a, f"B — {type_b}":fc_b}
        st.session_state["time_machine_notes"] = {"Scenario A":note_a, "Scenario B":note_b}
        st.session_state["time_machine_config"] = {"type_a":type_a,"amount_a":amount_a,"days_a":days_a,"price_a":price_a,"type_b":type_b,"amount_b":amount_b,"days_b":days_b,"price_b":price_b}
        write_audit(current_user["username"], current_user["role"], "WHAT_IF_COMPARE", str(selected), "success", "Baseline compared with two independent deterministic scenarios")
    except (AuthorizationError, ValueError) as exc:
        st.error(f"Scenario comparison blocked: {exc}")
if st.session_state.get("time_machine_compare") is not None:
    st.dataframe(st.session_state["time_machine_compare"], use_container_width=True, hide_index=True)
    notes = st.session_state.get("time_machine_notes", {})
    st.write("**Scenario A assumption:** " + notes.get("Scenario A", ""))
    st.write("**Scenario B assumption:** " + notes.get("Scenario B", ""))
    forecasts = st.session_state.get("time_machine_forecasts", {})
    tmfig = go.Figure()
    for name, frame in forecasts.items():
        tmfig.add_trace(go.Scatter(x=frame.date, y=frame.closing_cash, mode="lines+markers", name=name))
    tmfig.add_hline(y=0, line_dash="dash", annotation_text="Zero cash")
    tmfig.update_layout(xaxis_title="Date", yaxis_title="Closing cash", height=380)
    st.plotly_chart(style_chart(tmfig), use_container_width=True)
    cfg = st.session_state.get("time_machine_config", {})
    if cfg:
        st.download_button("Download scenario comparison CSV", st.session_state["time_machine_compare"].to_csv(index=False), "what_if_baseline_scenario_a_scenario_b.csv", "text/csv")


with st.expander("Known limitations"):
    st.markdown("- Bundled records are synthetic.\n- Opening cash is user-entered and not reconciled with a bank.\n- Expected inflows may not arrive on time.\n- Multi-hop propagation is deterministic and conservative; buffer values are assumptions, not calibrated liquidity measurements.\n- Action relief and costs are manual assumptions.\n- The current copilot uses deterministic evidence-grounded logic by default; optional LLM wording can still be wrong and must be checked against the evidence table. Financing products and time-machine shocks are illustrative assumptions. Upload quality diagnostics flag duplicate-like rows and missing counterparties but do not automatically reconcile them. Local password-based authentication and persistent SQLite audit records are implemented for this prototype. This is not a production identity provider; deployment still needs HTTPS/TLS, secret management, backup/retention policy, rate limiting, MFA and independent security review. Real-world forecast validation requires authorized, independently reconciled actual daily cash outcomes.")
st.caption("CashFlow Sentinel AI • Explainable SME Finance Copilot • Synthetic data • Decision support only")
