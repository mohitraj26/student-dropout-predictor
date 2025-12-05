import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pickle
import sqlite3
import hashlib
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Student Dropout Predictor", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DARK MODE CSS STYLING ---
st.markdown("""
<style>
    /* GLOBAL DARK THEME SETTINGS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117; 
        color: #e0e0e0;
    }
    
    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #1a1c24;
        border-right: 1px solid #2d2d2d;
    }
    
    /* METRIC CARDS - GLASSMORPHISM */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* TABS STYLING */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #2d2d2d;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent;
        border: 1px solid transparent;
        color: #94a3b8;
        font-weight: 600;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
        border: 1px solid #3b82f6;
    }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }

    /* FORM CONTAINERS */
    [data-testid="stForm"] {
        background-color: #161920;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #2d2d2d;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    
    /* REMOVE HEADER BUT KEEP HAMBURGER MENU */
    /* We only hide the decoration, not the toolbar itself */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
    
    /* FOOTER CLEANUP */
    footer {visibility: hidden;}
    #MainMenu {visibility: visible;} /* Ensure menu is visible */
    
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('processed_student_data.csv')
    except FileNotFoundError:
        df = pd.read_csv('fully_transformed_student_dataset.csv')
    return df

@st.cache_resource
def load_model():
    try:
        with open('student_dropout_model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        return None

df = load_data()
model = load_model()

# --- Auth Utils ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

create_user_table()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- 4. NAVIGATION SIDEBAR ---
if st.session_state['logged_in']:
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                            border: 2px solid #3b82f6; width: 90px; height: 90px; 
                            border-radius: 50%; display: flex; align-items: center; 
                            justify-content: center; margin: 0 auto; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);">
                    <span style="font-size: 45px;">🎓</span>
                </div>
                <h2 style="margin-top: 15px; color: #ffffff; font-weight: 700;">Student Dropout Predictor</h2>
                <div style="background-color: rgba(59, 130, 246, 0.1); color: #3b82f6; 
                            padding: 4px 12px; border-radius: 12px; display: inline-block; 
                            font-size: 0.8rem; font-weight: 600; margin-top: 5px;">
                    v2.0 Pro
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.write(f"👤 **User:** {st.session_state['username']}")
        st.write("---")
        
        menu = ["Dashboard", "Prediction Tool"]
        choice = st.radio("MENU", menu, label_visibility="collapsed")
        
        st.write("---")
        if st.button("Sign Out", type="secondary", width="stretch"): # FIX: use width="stretch"
            st.session_state['logged_in'] = False
            st.rerun()
else:
    choice = "Login"

# =============================================================================
# VIEW 1: LOGIN PAGE
# =============================================================================
if choice == "Login":
    c1, c2, c3 = st.columns([1, 1.2, 1])
    
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align: center; padding: 20px;">
                <h1 style="background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                           font-weight: 800; font-size: 3rem;">
                    Student Dropout Predictor
                </h1>
                <p style="color: #94a3b8; font-size: 1.1rem; margin-top: -10px;">
                    Next-Gen Dropout Prediction & Analytics
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        tab1, tab2 = st.tabs(["🔐 Access", "📝 Join"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="admin")
                password = st.text_input("Password", type='password', placeholder="••••••")
                # FIX: use width="stretch"
                submit_login = st.form_submit_button("Launch Dashboard", width="stretch")
            
            if submit_login:
                if login_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.toast("Access Granted", icon="🔓")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid credentials")
        
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type='password')
                # FIX: use width="stretch"
                submit_signup = st.form_submit_button("Create Account", width="stretch")
                
            if submit_signup:
                if add_user(new_user, new_pass):
                    st.success("Account ready! Please sign in.")
                else:
                    st.warning("Username taken.")

# =============================================================================
# VIEW 2: DASHBOARD
# =============================================================================
elif choice == "Dashboard":
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem;">Executive Overview</h1>
                <p style="color: #94a3b8; margin: 0;">Real-time cohort analysis and retention metrics.</p>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px 12px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; border: 1px solid rgba(16, 185, 129, 0.2);">
                    ● System Active
                </span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # --- FILTERS ---
    with st.expander("🔽 Filter Configuration", expanded=False):
        f1, f2, f3 = st.columns(3)
        courses = df['Course Name'].unique()
        sel_courses = f1.multiselect("Academic Program", courses, default=courses[:1])
        
        nationalities = df['Nationality'].unique()
        sel_nat = f2.multiselect("Nationality", nationalities, default=nationalities[:3])
        
        quals = df['Previous Qualification'].unique()
        sel_qual = f3.multiselect("Qualification", quals, default=quals[:3])
    
    # Apply Filters
    df_viz = df.copy()
    if sel_courses: df_viz = df_viz[df_viz['Course Name'].isin(sel_courses)]
    if sel_nat: df_viz = df_viz[df_viz['Nationality'].isin(sel_nat)]
    if sel_qual: df_viz = df_viz[df_viz['Previous Qualification'].isin(sel_qual)]
        
    if df_viz.empty:
        st.warning("No data found matching these filters.")
    else:
        # --- KPI CARDS ---
        m1, m2, m3, m4 = st.columns(4)
        
        dropout_rate = (df_viz['Student Status'] == 'Dropout').mean() * 100
        avg_grade = df_viz['Average Grade (2nd Sem)'].mean()
        high_risk_count = len(df_viz[(df_viz['Student Status'] == 'Dropout') & (df_viz['Is Debtor'] == 1)])
        
        m1.metric("Active Students", f"{len(df_viz):,}", "Filtered Cohort")
        m2.metric("Dropout Rate", f"{dropout_rate:.1f}%", "-2.4%" if dropout_rate < 30 else "+1.2%", delta_color="inverse")
        m3.metric("Avg Performance", f"{avg_grade:.1f}", "Grade Points (0-20)")
        m4.metric("Financial Risk", high_risk_count, "Debtors", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- TABS ---
        tab_deep, tab_corr, tab_factors, tab_trends = st.tabs([
            "🔍 Deep Dive", "🔥 Risk Matrix", "👨‍👩‍👧 Demographics", "📈 Trajectory"
        ])
        
        # Helper for dark plots
        def update_dark_layout(fig):
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig

        # TAB 1: DEEP DIVE
        with tab_deep:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("Program Health")
                if 'Course Name' in df_viz.columns:
                    sunburst_data = df_viz.groupby(['Course Name', 'Student Status']).size().reset_index(name='Count')
                    fig_sun = px.sunburst(
                        sunburst_data, path=['Course Name', 'Student Status'], values='Count',
                        color='Student Status', color_discrete_map={'Dropout': '#ef4444', 'Graduate': '#10b981', 'Enrolled': '#3b82f6'}
                    )
                    # FIX: use width="stretch"
                    st.plotly_chart(update_dark_layout(fig_sun), width="stretch")
            
            with c2:
                st.subheader("Grade Distribution")
                try:
                    grad = df_viz[df_viz['Student Status'] == 'Graduate']['Average Grade (2nd Sem)'].dropna()
                    drop = df_viz[df_viz['Student Status'] == 'Dropout']['Average Grade (2nd Sem)'].dropna()
                    if len(grad) > 1 and len(drop) > 1:
                        fig_dist = ff.create_distplot([grad, drop], ['Graduates', 'Dropouts'], show_hist=False, colors=['#10b981', '#ef4444'])
                        fig_dist.update_layout(legend=dict(orientation="h", y=1.1))
                        # FIX: use width="stretch"
                        st.plotly_chart(update_dark_layout(fig_dist), width="stretch")
                except: st.info("Insufficient data for distribution.")

        # TAB 2: CORRELATIONS
        with tab_corr:
            st.subheader("Risk Correlations")
            hm_df = df_viz.copy()
            hm_df['Is_Dropout'] = hm_df['Student Status'].apply(lambda x: 1 if x == 'Dropout' else 0)
            
            bin_map = {'Yes': 1, 'No': 0, 'Male': 1, 'Female': 0}
            for c in ['Tuition Fees Up-to-Date', 'Is Debtor', 'Gender (1=Male, 0=Female)']:
                if c in hm_df.columns: hm_df[c] = hm_df[c].map(bin_map)
            
            target_cols = ['Is_Dropout', 'Age at Enrollment', 'Average Grade (2nd Sem)', 'Tuition Fees Up-to-Date']
            avail_cols = [c for c in target_cols if c in hm_df.columns]
            
            if avail_cols:
                corr = hm_df[avail_cols].corr()
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
                # FIX: use width="stretch"
                st.plotly_chart(update_dark_layout(fig_corr), width="stretch")

        # TAB 3: PARENTAL
        with tab_factors:
            st.subheader("Socio-Economic Factors")
            c1, c2 = st.columns(2)
            def plot_bar(col, title, color):
                d = df_viz.groupby(col)['Student Status'].apply(lambda x: (x == 'Dropout').mean()).reset_index(name='Rate').sort_values('Rate', ascending=False).head(8)
                fig = px.bar(d, x=col, y='Rate', title=title, color_discrete_sequence=[color])
                return update_dark_layout(fig)
            
            # FIX: use width="stretch"
            c1.plotly_chart(plot_bar("Father's Qualification", "Father's Edu Impact", "#3b82f6"), width="stretch")
            c2.plotly_chart(plot_bar("Mother's Qualification", "Mother's Edu Impact", "#ec4899"), width="stretch")

        # TAB 4: TRENDS
        with tab_trends:
            st.subheader("Age vs Dropout Risk")
            trend = df_viz.groupby('Age at Enrollment')['Student Status'].apply(lambda x: (x == 'Dropout').mean()).reset_index()
            fig_trend = px.line(trend, x='Age at Enrollment', y='Student Status', markers=True, title="Risk Trajectory by Age")
            fig_trend.update_traces(line_color='#ef4444')
            # FIX: use width="stretch"
            st.plotly_chart(update_dark_layout(fig_trend), width="stretch")

# =============================================================================
# VIEW 3: PREDICTION TOOL
# =============================================================================
elif choice == "Prediction Tool":
    st.markdown(
        """
        <h1 style="color: #fafafa;">🤖 AI Risk Assessment</h1>
        <p style="color: #94a3b8;">Enter student parameters to generate a real-time dropout probability score.</p>
        <hr style="border-color: #414141;">
        """, 
        unsafe_allow_html=True
    )

    if model is None:
        st.error("⚠️ Model file not found. Please run the training notebook.")
    else:
        # Layout: 2 Columns
        col_input, col_viz = st.columns([1.5, 1], gap="large")

        with col_input:
            with st.form("predict_form"):
                st.markdown("#### Student Profile")
                
                c1, c2 = st.columns(2)
                with c1:
                    tuition = st.selectbox("Tuition Fees Paid?", ["Yes", "No"])
                    debtor = st.selectbox("Is Debtor?", ["Yes", "No"])
                    scholarship = st.selectbox("Scholarship?", ["Yes", "No"])
                with c2:
                    gender = st.selectbox("Gender", ["Male", "Female"])
                    age = st.slider("Age at Enrollment", 17, 60, 20)
                    units = st.slider("Approved Units (Sem 1)", 0, 30, 5)
                
                grade = st.slider("Average Grade (Sem 2)", 0.0, 20.0, 12.0)
                
                st.markdown("<br>", unsafe_allow_html=True)
                # FIX: use width="stretch"
                predict_btn = st.form_submit_button("Run Analysis", width="stretch")

        with col_viz:
            st.markdown("#### Risk Gauge")
            if predict_btn:
                # Prepare Input
                input_df = pd.DataFrame([[
                    1 if tuition == 'Yes' else 0,
                    1 if debtor == 'Yes' else 0,
                    1 if gender == 'Male' else 0,
                    1 if scholarship == 'Yes' else 0,
                    age, grade, units
                ]], columns=[
                    'Tuition Fees Up-to-Date', 'Is Debtor', 'Gender (1=Male, 0=Female)', 
                    'Scholarship Holder', 'Age at Enrollment', 'Average Grade (2nd Sem)', 
                    'Approved Units (1st Sem)'
                ])
                
                # Predict
                with st.spinner("Processing..."):
                    time.sleep(0.5)
                    pred = model.predict(input_df)[0]
                    prob = model.predict_proba(input_df).max()

                # Visual Result
                is_risk = pred == 1
                color = "#ef4444" if is_risk else "#10b981"
                title = "Dropout Risk" if is_risk else "Success Prob."
                
                # Gauge Chart - Dark Mode
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = prob * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': title, 'font': {'size': 20, 'color': '#e0e0e0'}},
                    number = {'font': {'color': '#e0e0e0'}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickcolor': "white"},
                        'bar': {'color': color},
                        'bgcolor': "rgba(0,0,0,0)",
                        'steps': [
                            {'range': [0, 50], 'color': "#333333"},
                            {'range': [50, 80], 'color': "#444444"},
                            {'range': [80, 100], 'color': "#555555"}
                        ],
                    }
                ))
                fig_gauge.update_layout(
                    height=280, 
                    margin=dict(l=10, r=10, t=40, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={'color': "#e0e0e0"}
                )
                # FIX: use width="stretch"
                st.plotly_chart(fig_gauge, width="stretch")
                
                if is_risk:
                    st.error("⚠️ **High Risk Alert**")
                    st.caption("Action: Schedule counseling immediately.")
                else:
                    st.success("✅ **On Track**")
                    st.caption("Status: Student is performing well.")
            else:
                # Empty State
                st.info("👈 Enter details to start analysis.")