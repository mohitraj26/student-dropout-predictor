import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
import sqlite3
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="Student Success AI", layout="wide")

# --- 1. DATA & MODEL LOADING ---
@st.cache_data
def load_data():
    # Load the processed data (Cleaned version from Step 1)
    # This file should contain String labels (e.g., "Yes", "No", "Arts") for the dashboard to look good.
    try:
        df = pd.read_csv('processed_student_data.csv')
    except FileNotFoundError:
        # Fallback if processed data isn't found, try original
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

# --- 2. AUTHENTICATION UTILS ---
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

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. NAVIGATION ---
# We use a sidebar for navigation to keep the main area clean
st.sidebar.title("Navigation")
menu = ["Home/Login", "Dashboard (Step 3)", "Prediction Tool (Step 6)"]
choice = st.sidebar.selectbox("Go to:", menu)

# =============================================================================
# VIEW 1: LOGIN / HOME
# =============================================================================
if choice == "Home/Login":
    st.title("🎓 Student Dropout Prediction System")
    st.markdown("Welcome! Please login to access the Dashboard and Prediction tools.")
    
    if not st.session_state['logged_in']:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                if login_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid Username/Password")
        
        with tab2:
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type='password')
            if st.button("Create Account"):
                if add_user(new_user, new_pass):
                    st.success("Account created! Please login.")
                else:
                    st.warning("User already exists.")
    else:
        st.success(f"Logged in as: **{st.session_state['username']}**")
        st.info("Use the sidebar to navigate to the **Dashboard** or **Prediction Tool**.")
        
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

# =============================================================================
# VIEW 2: DASHBOARD (Task 3 - Enhanced)
# =============================================================================
elif choice == "Dashboard (Step 3)":
    if not st.session_state['logged_in']:
        st.warning("🔒 Please Login to access the Dashboard.")
    else:
        st.title("📊 Interactive Analysis Dashboard")
        st.markdown("### Insights into student performance and dropout risks.")
        
        # --- Sidebar Filters (Specific to Dashboard) ---
        st.sidebar.markdown("---")
        st.sidebar.header("Dashboard Filters")
        
        # 1. Course Filter
        courses = df['Course Name'].unique()
        selected_courses = st.sidebar.multiselect("Select Course", courses, default=courses[:3])
        
        # 2. Nationality Filter
        nationalities = df['Nationality'].unique()
        selected_nationality = st.sidebar.multiselect("Select Nationality", nationalities, default=nationalities[:3])
        
        # 3. Qualification Filter
        qualifications = df['Previous Qualification'].unique()
        selected_qualification = st.sidebar.multiselect("Select Previous Qualification", qualifications, default=qualifications[:3])
        
        # Apply Filters
        df_viz = df[
            (df['Course Name'].isin(selected_courses)) &
            (df['Nationality'].isin(selected_nationality)) &
            (df['Previous Qualification'].isin(selected_qualification))
        ].copy()
        
        if df_viz.empty:
            st.warning("No data matches your filters. Please adjust your selection.")
        else:
            # --- KPI Metrics ---
            col1, col2, col3 = st.columns(3)
            total_students = len(df_viz)
            dropout_rate = (df_viz['Student Status'] == 'Dropout').mean() * 100
            avg_grade = df_viz['Average Grade (2nd Sem)'].mean()

            col1.metric("Total Students (Filtered)", total_students)
            col2.metric("Dropout Rate", f"{dropout_rate:.1f}%")
            col3.metric("Avg Grade (2nd Sem)", f"{avg_grade:.1f}")

            st.markdown("---")

            # --- 1. Heatmap ---
            st.subheader("1. Correlation Heatmap")
            
            # Prepare data for heatmap (Convert Text to Numbers)
            heatmap_df = df_viz.copy()
            
            # Encode Target
            heatmap_df['Is_Dropout'] = heatmap_df['Student Status'].apply(lambda x: 1 if x == 'Dropout' else 0)
            
            # Convert Yes/No to 1/0
            binary_map = {'Yes': 1, 'No': 0, 'Male': 1, 'Female': 0}
            for col in ['Tuition Fees Up-to-Date', 'Scholarship Holder', 'Is Debtor', 'Gender (1=Male, 0=Female)']:
                if col in heatmap_df.columns and heatmap_df[col].dtype == 'object':
                    heatmap_df[col] = heatmap_df[col].map(binary_map)

            # Select numeric columns for correlation
            corr_cols = [
                'Is_Dropout', 'Age at Enrollment', 'Average Grade (2nd Sem)', 
                'Unemployment Rate (%)', 'Tuition Fees Up-to-Date', 'Scholarship Holder'
            ]
            # Verify columns exist
            valid_cols = [c for c in corr_cols if c in heatmap_df.columns]
            
            if valid_cols:
                corr = heatmap_df[valid_cols].corr()
                fig_corr = px.imshow(
                    corr, text_auto=True, aspect="auto",
                    color_continuous_scale='RdBu_r',
                    title="Feature Correlation Matrix"
                )
                st.plotly_chart(fig_corr, use_container_width=True)

            # --- 2. Comparative Charts ---
            st.subheader("2. Parental Qualification Impact")
            
            c1, c2 = st.columns(2)
            
            # Helper to get dropout rates
            def get_dropout_rates(col_name):
                return df_viz.groupby(col_name)['Student Status'].apply(lambda x: (x == 'Dropout').mean()).sort_values(ascending=False).head(10)

            with c1:
                dad_data = get_dropout_rates("Father's Qualification").reset_index(name='Dropout Rate')
                fig_dad = px.bar(dad_data, x="Father's Qualification", y="Dropout Rate", 
                                 title="Top 10 High-Risk Father's Qualifications", color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig_dad, use_container_width=True)
                
            with c2:
                mom_data = get_dropout_rates("Mother's Qualification").reset_index(name='Dropout Rate')
                fig_mom = px.bar(mom_data, x="Mother's Qualification", y="Dropout Rate", 
                                 title="Top 10 High-Risk Mother's Qualifications", color_discrete_sequence=['#EF553B'])
                st.plotly_chart(fig_mom, use_container_width=True)

            # --- 3. Trends ---
            st.subheader("3. Trend Analysis")
            tab_age, tab_eco = st.tabs(["Age Trend", "Economic Trend"])
            
            with tab_age:
                age_trend = df_viz.groupby('Age at Enrollment')['Student Status'].apply(lambda x: (x == 'Dropout').mean()).reset_index(name='Dropout Rate')
                fig_age = px.line(age_trend, x='Age at Enrollment', y='Dropout Rate', markers=True, title="Dropout Risk by Age")
                st.plotly_chart(fig_age, use_container_width=True)
                
            with tab_eco:
                eco_trend = df_viz.groupby('Unemployment Rate (%)')['Student Status'].apply(lambda x: (x == 'Dropout').mean()).reset_index(name='Dropout Rate')
                # Try-except for OLS trendline in case statsmodels is missing
                try:
                    fig_eco = px.scatter(eco_trend, x='Unemployment Rate (%)', y='Dropout Rate', trendline="ols", title="Dropout Risk vs Unemployment")
                except:
                    fig_eco = px.scatter(eco_trend, x='Unemployment Rate (%)', y='Dropout Rate', title="Dropout Risk vs Unemployment (Trendline unavailable)")
                st.plotly_chart(fig_eco, use_container_width=True)

# =============================================================================
# VIEW 3: PREDICTION TOOL (Task 6)
# =============================================================================
elif choice == "Prediction Tool (Step 6)":
    if not st.session_state['logged_in']:
        st.warning("🔒 Please Login to use the Prediction Tool.")
    elif model is None:
        st.error("⚠️ Model file (`student_dropout_model.pkl`) not found. Please run the analysis notebook first.")
    else:
        st.title("🤖 Real-Time Dropout Predictor")
        st.markdown("Enter student details below to predict their likelihood of dropping out.")
        
        with st.form("prediction_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tuition = st.selectbox("Tuition Fees Up-to-Date?", ["Yes", "No"])
                debtor = st.selectbox("Is the Student a Debtor?", ["Yes", "No"])
            
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female"])
                scholarship = st.selectbox("Scholarship Holder?", ["Yes", "No"])
            
            with col3:
                age = st.number_input("Age at Enrollment", 17, 70, 20)
                grade = st.number_input("2nd Sem Grade (0-20)", 0.0, 20.0, 12.0)
                units = st.number_input("Approved Units (1st Sem)", 0, 30, 5)
            
            submit_button = st.form_submit_button("Predict Outcome")
            
        if submit_button:
            # Prepare Input Data (Must match model training features)
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
            
            try:
                prediction = model.predict(input_df)[0]
                probability = model.predict_proba(input_df).max()
                
                st.markdown("---")
                # 1 = Dropout, 0 = Graduate/Enrolled (based on common encoding)
                if prediction == 1:
                    st.error(f"⚠️ **Prediction: Dropout Risk**")
                    st.metric("Confidence Level", f"{probability:.1%}")
                    st.markdown("👉 **Recommendation:** Student shows high risk factors (Debt/Grades). Immediate academic counseling is advised.")
                else:
                    st.success(f"✅ **Prediction: Likely to Graduate**")
                    st.metric("Confidence Level", f"{probability:.1%}")
                    st.markdown("👉 **Recommendation:** Student is on track. Continue standard monitoring.")
                    
            except Exception as e:
                st.error(f"Prediction Error: {e}")