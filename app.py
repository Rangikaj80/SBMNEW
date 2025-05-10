import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
from PIL import Image
import numpy as np
import calendar
from streamlit_option_menu import option_menu

# Set page configuration
st.set_page_config(
    page_title="Retail Business Manager",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection function
def init_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["db_host"],
            database=st.secrets["db_name"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"]
        )
    except Exception as e:
        # Fallback to SQLite for local development if PostgreSQL connection fails
        st.warning("Using SQLite for local development. For production, set up PostgreSQL in Streamlit secrets.")
        import sqlite3
        return sqlite3.connect('shop_management.db')

# Apply custom CSS with enhanced vibrant design
def apply_custom_style():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #6C63FF;  /* Vibrant purple */
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.8rem;
        color: #333;
        font-weight: 600;
        margin: 1rem 0;
    }
    .card {
        border-radius: 15px;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        border-top: 5px solid #6C63FF;
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .metric-card {
        background: linear-gradient(145deg, #f8f9fa, #ffffff);
        border-left: 5px solid #6C63FF;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(108, 99, 255, 0.1);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        box-shadow: 0 6px 15px rgba(108, 99, 255, 0.2);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #6C63FF;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        font-weight: 500;
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
        background-color: #6C63FF;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #5A52D5;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(108, 99, 255, 0.2);
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #dc3545;
    }
    .placeholder-box {
        background: linear-gradient(145deg, #f1f3f4, #ffffff);
        border-radius: 15px;
        text-align: center;
        padding: 40px;
        color: #6C63FF;
        margin: 20px 0;
        border: 1px dashed #6C63FF;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.1);
        transition: all 0.3s ease;
    }
    .placeholder-box:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(108, 99, 255, 0.15);
    }
    .icon-large {
        font-size: 3.5rem;
        color: #6C63FF;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f8f9fa;
        border-radius: 5px 5px 0 0;
        gap: 1px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6C63FF !important;
        color: white !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid #e6e6e6;
    }
    div[data-testid="stExpander"] > details > summary {
        background-color: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 10px 10px 0 0;
    }
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #f0f0f0;
    }
    div[data-testid="stExpander"] > details > summary > p {
        font-weight: 600;
    }
    div[data-testid="stExpander"] > details[open] > summary {
        border-bottom: 1px solid #e6e6e6;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# Display a placeholder with animation
def display_placeholder(icon, text):
    st.markdown(f"""
    <div class="placeholder-box">
        <div class="icon-large">{icon}</div>
        <h3>{text}</h3>
    </div>
    """, unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = init_connection()
    try:
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            # PostgreSQL connection
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                         last_login TEXT, email TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS transactions
                        (id SERIAL PRIMARY KEY, shop_name TEXT, date TEXT,
                         sales REAL, cost REAL, cash_out REAL, expenses TEXT, bank_deposit REAL,
                         created_by TEXT, created_at TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS cheques 
                        (id SERIAL PRIMARY KEY, date TEXT, shop_name TEXT,
                         amount REAL, payee TEXT, status TEXT, 
                         cheque_number TEXT, bank TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS inventory
                        (id SERIAL PRIMARY KEY, item TEXT, quantity INTEGER, 
                         shop_name TEXT, updated_at TEXT)''')
            
        else:
            # SQLite connection
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                         last_login TEXT, email TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS transactions
                        (id INTEGER PRIMARY KEY, shop_name TEXT, date TEXT,
                         sales REAL, cost REAL, cash_out REAL, expenses TEXT, bank_deposit REAL,
                         created_by TEXT, created_at TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS cheques 
                        (id INTEGER PRIMARY KEY, date TEXT, shop_name TEXT,
                         amount REAL, payee TEXT, status TEXT, 
                         cheque_number TEXT, bank TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS inventory
                        (id INTEGER PRIMARY KEY, item TEXT, quantity INTEGER, 
                         shop_name TEXT, updated_at TEXT)''')
        
        conn.commit()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
    finally:
        conn.close()

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def add_transaction(shop_name, date, sales, cost, cash_out, expenses, bank_deposit):
    conn = init_connection()
    try:
        c = conn.cursor()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            c.execute('''INSERT INTO transactions (shop_name, date, sales, cost, cash_out, expenses, bank_deposit, created_by, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                      (shop_name, date.strftime('%Y-%m-%d'), sales, cost, cash_out, json.dumps(expenses), bank_deposit, 
                       st.session_state.user, created_at))
        else:
            c.execute('''INSERT INTO transactions (shop_name, date, sales, cost, cash_out, expenses, bank_deposit, created_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (shop_name, date.strftime('%Y-%m-%d'), sales, cost, cash_out, json.dumps(expenses), bank_deposit, 
                       st.session_state.user, created_at))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error adding transaction: {e}")
    finally:
        conn.close()
    
    # Show success notification
    st.session_state.show_notification = True
    st.session_state.notification_message = f"Transaction for {shop_name} added successfully!"
    st.session_state.notification_type = "success"

def add_cheque(date, shop_name, amount, payee, cheque_number, bank):
    conn = init_connection()
    try:
        c = conn.cursor()
        
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            c.execute('''INSERT INTO cheques (date, shop_name, amount, payee, status, cheque_number, bank)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                      (date.strftime('%Y-%m-%d'), shop_name, amount, payee, 'Pending', cheque_number, bank))
        else:
            c.execute('''INSERT INTO cheques (date, shop_name, amount, payee, status, cheque_number, bank)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (date.strftime('%Y-%m-%d'), shop_name, amount, payee, 'Pending', cheque_number, bank))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error adding cheque: {e}")
    finally:
        conn.close()
    
    # Show success notification
    st.session_state.show_notification = True
    st.session_state.notification_message = f"Cheque for {payee} added successfully!"
    st.session_state.notification_type = "success"

def update_cheque_status(cheque_id, status):
    conn = init_connection()
    try:
        c = conn.cursor()
        
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            c.execute("UPDATE cheques SET status = %s WHERE id = %s", (status, cheque_id))
        else:
            c.execute("UPDATE cheques SET status = ? WHERE id = ?", (status, cheque_id))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error updating cheque status: {e}")
    finally:
        conn.close()

def get_transactions(shop_filter=None, date_from=None, date_to=None):
    conn = init_connection()
    try:
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            query = "SELECT * FROM transactions"
            params = []
            
            if shop_filter or date_from or date_to:
                query += " WHERE"
                
                if shop_filter and shop_filter != "All":
                    query += " shop_name = %s"
                    params.append(shop_filter)
                    
                if date_from:
                    if params:
                        query += " AND"
                    query += " date >= %s"
                    params.append(date_from.strftime('%Y-%m-%d'))
                    
                if date_to:
                    if params:
                        query += " AND"
                    query += " date <= %s"
                    params.append(date_to.strftime('%Y-%m-%d'))
            
            # Use pandas for PostgreSQL with params
            df = pd.read_sql_query(query, conn, params=tuple(params))
        else:
            # SQLite version
            query = "SELECT * FROM transactions"
            params = []
            
            if shop_filter or date_from or date_to:
                query += " WHERE"
                
                if shop_filter and shop_filter != "All":
                    query += " shop_name = ?"
                    params.append(shop_filter)
                    
                if date_from:
                    if params:
                        query += " AND"
                    query += " date >= ?"
                    params.append(date_from.strftime('%Y-%m-%d'))
                    
                if date_to:
                    if params:
                        query += " AND"
                    query += " date <= ?"
                    params.append(date_to.strftime('%Y-%m-%d'))
            
            df = pd.read_sql_query(query, conn, params=params)
        
        return df
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_cheques(status_filter=None):
    conn = init_connection()
    try:
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            query = "SELECT * FROM cheques"
            params = []
            
            if status_filter and status_filter != "All":
                query += " WHERE status = %s"
                params.append(status_filter)
                
            # Use pandas for PostgreSQL with params
            df = pd.read_sql_query(query, conn, params=tuple(params))
        else:
            # SQLite version
            query = "SELECT * FROM cheques"
            params = []
            
            if status_filter and status_filter != "All":
                query += " WHERE status = ?"
                params.append(status_filter)
                
            df = pd.read_sql_query(query, conn, params=params)
        
        return df
    except Exception as e:
        st.error(f"Error fetching cheques: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def calculate_bank_balance():
    conn = init_connection()
    try:
        c = conn.cursor()
        
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            c.execute("SELECT SUM(bank_deposit) FROM transactions")
            total_deposits = c.fetchone()[0] or 0
            c.execute("SELECT SUM(amount) FROM cheques WHERE status='Pending'")
            total_cheques = c.fetchone()[0] or 0
        else:
            c.execute("SELECT SUM(bank_deposit) FROM transactions")
            total_deposits = c.fetchone()[0] or 0
            c.execute("SELECT SUM(amount) FROM cheques WHERE status='Pending'")
            total_cheques = c.fetchone()[0] or 0
        
        return total_deposits - total_cheques
    except Exception as e:
        st.error(f"Error calculating bank balance: {e}")
        return 0
    finally:
        conn.close()

def get_monthly_performance():
    conn = init_connection()
    try:
        # Get sales for the last 6 months
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Check if we're using PostgreSQL or SQLite
        if conn.__class__.__module__.startswith('psycopg2'):
            query = f"""
            SELECT 
                to_char(to_date(date, 'YYYY-MM-DD'), 'YYYY-MM') as month,
                SUM(sales) as total_sales,
                shop_name
            FROM transactions
            WHERE date >= '{six_months_ago}'
            GROUP BY month, shop_name
            ORDER BY month
            """
        else:
            query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(sales) as total_sales,
                shop_name
            FROM transactions
            WHERE date >= '{six_months_ago}'
            GROUP BY month, shop_name
            ORDER BY month
            """
        
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error getting monthly performance: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def predict_next_month_sales():
    # Get historical data
    df = get_transactions()
    
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Group by month and calculate total sales
    monthly_sales = df.groupby(['month', 'shop_name'])['sales'].sum().reset_index()
    
    # If we have enough data, use a simple moving average
    # Otherwise, just return the average sales
    shops = df['shop_name'].unique()
    predictions = {}
    
    for shop in shops:
        shop_data = monthly_sales[monthly_sales['shop_name'] == shop]
        if len(shop_data) >= 3:
            # Use the last 3 months average
            last_3_months = shop_data.tail(3)
            predictions[shop] = last_3_months['sales'].mean()
        else:
            # Use whatever data we have
            predictions[shop] = shop_data['sales'].mean()
    
    return predictions

# Initialize the database
init_db()

# Custom notification component
def show_notification():
    if st.session_state.get('show_notification', False):
        if st.session_state.notification_type == "success":
            st.success(st.session_state.notification_message)
        else:
            st.error(st.session_state.notification_message)
        
        # Clear notification after 3 seconds
        time.sleep(3)
        st.session_state.show_notification = False

# Main app
def main():
    # Start with a loading animation
    if 'app_loaded' not in st.session_state:
        with st.spinner("Loading Retail Business Manager..."):
            time.sleep(0.8)
            st.session_state.app_loaded = True
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'show_notification' not in st.session_state:
        st.session_state.show_notification = False
    
    if st.session_state.user:
        authenticated_app()
    else:
        auth_page()

def auth_page():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<h1 class='main-header'>Retail Business Manager</h1>", unsafe_allow_html=True)
        display_placeholder("🔑", "Secure Login System")
        st.markdown("""
        <div style='text-align: center;'>
            <h3 style='color: #6C63FF;'>Welcome to your comprehensive retail management solution</h3>
            <p>Track sales, manage expenses, monitor inventory, and make data-driven decisions</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("<h3 class='sub-header'>Login to Your Account</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                login_button = st.button("Login", use_container_width=True)
            
            if login_button:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Logging you in..."):
                        conn = init_connection()
                        try:
                            c = conn.cursor()
                            
                            # Check if we're using PostgreSQL or SQLite
                            if conn.__class__.__module__.startswith('psycopg2'):
                                c.execute("SELECT password FROM users WHERE username = %s", (username,))
                            else:
                                c.execute("SELECT password FROM users WHERE username = ?", (username,))
                            
                            result = c.fetchone()
                            
                            if result and check_password(password, result[0]):
                                # Update last login
                                if conn.__class__.__module__.startswith('psycopg2'):
                                    c.execute("UPDATE users SET last_login = %s WHERE username = %s", 
                                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
                                else:
                                    c.execute("UPDATE users SET last_login = ? WHERE username = ?", 
                                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
                                
                                conn.commit()
                                st.session_state.user = username
                                st.success("Logged in successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                        except Exception as e:
                            st.error(f"Login error: {e}")
                        finally:
                            conn.close()

        with tab2:
            st.markdown("<h3 class='sub-header'>Create New Account</h3>", unsafe_allow_html=True)
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                signup_button = st.button("Sign Up", use_container_width=True)
            
            if signup_button:
                if not new_username or not new_email or not new_password:
                    st.error("Please fill all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Creating your account..."):
                        conn = init_connection()
                        try:
                            c = conn.cursor()
                            
                            # Check if we're using PostgreSQL or SQLite
                            if conn.__class__.__module__.startswith('psycopg2'):
                                c.execute("SELECT * FROM users WHERE username = %s", (new_username,))
                            else:
                                c.execute("SELECT * FROM users WHERE username = ?", (new_username,))
                            
                            if c.fetchone():
                                st.error("Username already exists")
                            else:
                                hashed_password = hash_password(new_password)
                                
                                if conn.__class__.__module__.startswith('psycopg2'):
                                    c.execute("INSERT INTO users (username, password, role, last_login, email) VALUES (%s, %s, %s, %s, %s)", 
                                             (new_username, hashed_password, 'user', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), new_email))
                                else:
                                    c.execute("INSERT INTO users (username, password, role, last_login, email) VALUES (?, ?, ?, ?, ?)", 
                                             (new_username, hashed_password, 'user', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), new_email))
                                
                                conn.commit()
                                st.success("Account created successfully! Please log in.")
                        except Exception as e:
                            st.error(f"Account creation error: {e}")
                        finally:
                            conn.close()
        st.markdown("</div>", unsafe_allow_html=True)

def authenticated_app():
    # Display notification if any
    show_notification()
    
    # Sidebar with profile and navigation
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(120deg, #6C63FF 0%, #5A52D5 100%); 
                     padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white;">
            <h3>Welcome, {st.session_state.user}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate and display bank balance
        bank_balance = calculate_bank_balance()
        
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>Current Bank Balance</p>
            <p class='metric-value'>LKR {bank_balance:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Next month prediction summary
        predictions = predict_next_month_sales()
        if predictions:
            st.markdown("<div class='metric-card' style='margin-top: 15px;'>", unsafe_allow_html=True)
            st.markdown("<p class='metric-label'>Predicted Sales (Next Month)</p>", unsafe_allow_html=True)
            for shop, amount in predictions.items():
                st.markdown(f"""
                <div style="background: linear-gradient(120deg, #E0E7FF 0%, #F9F9FF 100%); 
                             padding: 10px; border-radius: 10px; margin-bottom: 10px; 
                             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                    <p style="margin:0; font-weight:600;">{shop}</p>
                    <p style="margin:0; font-size:1.2rem; color:#6C63FF;">LKR {amount:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Navigation menu with icons
        selected = option_menu(
            "Main Menu",
            ["Dashboard", "Daily Sales", "Bank Transactions", "Data Import", "Sales Analytics", "Prediction", "Settings"],
            icons=["house", "cash-coin", "bank", "file-earmark-arrow-up", "graph-up", "lightbulb", "gear"],
           
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "#f8f9fa", "border-radius": "10px"},
                "icon": {"color": "#6C63FF", "font-size": "16px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#6C63FF"},
            }
        )
        
        st.button("Logout", on_click=logout, type="primary")
    
    # Main content area
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Daily Sales":
        daily_sales_page()
    elif selected == "Bank Transactions":
        bank_transactions_page()
    elif selected == "Data Import":
        data_import_page()
    elif selected == "Sales Analytics":
        sales_visualization_page()
    elif selected == "Prediction":
        prediction_page()
    elif selected == "Settings":
        settings_page()

def dashboard_page():
    st.markdown("<h1 class='main-header'>Business Dashboard</h1>", unsafe_allow_html=True)
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    # Get transaction data
    df = get_transactions()

    
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['expenses'] = df['expenses'].apply(json.loads)
        
        # ADD THE NEW PROFIT CALCULATIONS HERE, BEFORE DISPLAYING METRICS
        # Calculate profits
        df['gross_profit'] = df['sales'] - df['cost']
        total_expenses = df.apply(lambda row: sum(v for k, v in row['expenses'].items() 
                                               if k != 'description' and isinstance(v, (int, float))), axis=1)
        df['net_profit'] = df['gross_profit'] - total_expenses
        
        # Total sales
        total_sales = df['sales'].sum()

    
        
        # Gross profit
        col2.markdown(f"""
        <div style="background: linear-gradient(120deg, #E0FFE4 0%, #F9FFF9 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <p style="margin:0; color:#666; font-weight:500;">Total Gross Profit</p>
            <h2 style="margin:5px 0; color:#00D09C;">LKR {df['gross_profit'].sum():,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Net profit
        col3.markdown(f"""
        <div style="background: linear-gradient(120deg, #E0E7FF 0%, #F9F9FF 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <p style="margin:0; color:#666; font-weight:500;">Total Net Profit</p>
            <h2 style="margin:5px 0; color:#6C63FF;">LKR {df['net_profit'].sum():,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    
        
        # This month's sales
        current_month = datetime.now().strftime('%Y-%m')
        this_month_sales = df[df['date'].dt.strftime('%Y-%m') == current_month]['sales'].sum()
        col2.markdown(f"""
        <div style="background: linear-gradient(120deg, #FFE0E0 0%, #FFF9F9 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <p style="margin:0; color:#666; font-weight:500;">This Month</p>
            <h2 style="margin:5px 0; color:#FF6584;">LKR {this_month_sales:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Bank balance
        bank_balance = calculate_bank_balance()
        col3.markdown(f"""
        <div style="background: linear-gradient(120deg, #E0FFE4 0%, #F9FFF9 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <p style="margin:0; color:#666; font-weight:500;">Bank Balance</p>
            <h2 style="margin:5px 0; color:#00D09C;">LKR {bank_balance:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Pending cheques
        cheques_df = get_cheques('Pending')
        total_pending = cheques_df['amount'].sum() if not cheques_df.empty else 0
        col4.markdown(f"""
        <div style="background: linear-gradient(120deg, #FFF4E0 0%, #FFFDF9 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <p style="margin:0; color:#666; font-weight:500;">Pending Cheques</p>
            <h2 style="margin:5px 0; color:#FFB800;">LKR {total_pending:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Shop performance chart
        st.markdown("<h2 class='sub-header'>Shop Performance</h2>", unsafe_allow_html=True)
        
        performance_df = get_monthly_performance()
        if not performance_df.empty:
            fig = px.line(performance_df, 
                         x='month', 
                         y='total_sales', 
                         color='shop_name',
                         title='Monthly Sales by Shop',
                         labels={'total_sales': 'Total Sales (LKR)', 'month': 'Month', 'shop_name': 'Shop'},
                         markers=True)
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Sales (LKR)',
                legend_title='Shop',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif", size=12),
                colorway=["#6C63FF", "#FF6584", "#00D09C", "#FFB800", "#FF5252"],
                margin=dict(l=40, r=40, t=40, b=40),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent transactions and notifications
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3>Recent Transactions</h3>", unsafe_allow_html=True)
            recent_transactions = df.sort_values('date', ascending=False).head(5)
            
            for _, row in recent_transactions.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="padding: 15px; margin-bottom: 15px; border-radius: 10px; 
                                background: linear-gradient(145deg, #f8f9fa, #ffffff);
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
                                border-left: 5px solid #6C63FF;">
                        <p style="margin: 0; font-weight: 600; color: #6C63FF;">{row['shop_name']}</p>
                        <p style="margin: 0; color: #666;">{row['date'].strftime('%d %b, %Y')}</p>
                        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                            <span>Sales: <b>LKR {row['sales']:,.2f}</b></span>
                            <span>Deposit: <b>LKR {row['bank_deposit']:,.2f}</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3>Upcoming Cheques</h3>", unsafe_allow_html=True)
            upcoming_cheques = cheques_df.sort_values('date').head(5) if not cheques_df.empty else pd.DataFrame()
            
            if not upcoming_cheques.empty:
                for _, row in upcoming_cheques.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 15px; margin-bottom: 15px; border-radius: 10px; 
                                    background: linear-gradient(145deg, #f8f9fa, #ffffff);
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
                                    border-left: 5px solid #FFB800;">
                            <p style="margin: 0; font-weight: 600; color: #FFB800;">{row['payee']}</p>
                            <p style="margin: 0; color: #666;">{row['date']}</p>
                            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                                <span>Amount: <b>LKR {row['amount']:,.2f}</b></span>
                                <span>Shop: <b>{row['shop_name']}</b></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No upcoming cheques")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No transaction data available yet. Start by adding daily sales entries.")
        display_placeholder("📊", "Add transactions to view your dashboard")

def data_import_page():
    st.markdown("<h1 class='main-header'>Bulk Data Import</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 class='sub-header'>Import Monthly Data</h2>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])
        
        if uploaded_file is not None:
            try:
                # Determine file type and read accordingly
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.markdown("<h3>Preview of Uploaded Data</h3>", unsafe_allow_html=True)
                st.dataframe(df.head(), use_container_width=True)
                
                # Data validation checks
                required_columns = ['date', 'shop_name', 'sales', 'cost', 'cash_out', 'expenses', 'bank_deposit']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                    st.markdown("""
                    <div class='error-message'>
                        Your file should have the following columns:
                        <ul>
                            <li>date - in YYYY-MM-DD format</li>
                            <li>shop_name - name of the shop</li>
                            <li>sales - daily sales amount</li>
                            <li>cost - cost of goods sold</li>
                            <li>cash_out - cash taken out</li>
                            <li>expenses - JSON string of expenses</li>
                            <li>bank_deposit - amount deposited to bank</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Provide template for expenses if needed
                    expense_template = {
                        "salary": 0,
                        "rent": 0,
                        "light_bill": 0,
                        "water_bill": 0,
                        "phone_bill": 0,
                        "petty_cash": 0,
                        "home": 0,
                        "other_expenses": 0,
                        "description": ""
                    }
                    
                    # Verify expenses column format (if not JSON, provide option to map columns)
                    if 'expenses' in df.columns:
                        try:
                            # Try to parse the first expenses entry as JSON
                            json.loads(df['expenses'].iloc[0])
                        except:
                            st.warning("Expenses column is not in JSON format. Please map individual expense columns.")
                            expense_cols = {}
                            for exp_key in expense_template.keys():
                                if exp_key in df.columns:
                                    expense_cols[exp_key] = exp_key
                                else:
                                    expense_cols[exp_key] = None
                            
                            # Let user map columns
                            with st.expander("Map Expense Columns"):
                                mapped_expense_cols = {}
                                for exp_key in expense_template.keys():
                                    mapped_expense_cols[exp_key] = st.selectbox(
                                        f"Map column for {exp_key}",
                                        [None] + list(df.columns),
                                        index=0 if expense_cols[exp_key] is None else list(df.columns).index(expense_cols[exp_key]) + 1
                                    )
                            
                            # Transform mapped columns into expenses JSON
                            def create_expenses_json(row):
                                expenses = expense_template.copy()
                                for exp_key, col_name in mapped_expense_cols.items():
                                    if col_name is not None:
                                        expenses[exp_key] = float(row[col_name]) if pd.notna(row[col_name]) else 0
                                return json.dumps(expenses)
                            
                            df['expenses'] = df.apply(create_expenses_json, axis=1)
                    
                    # Import data button
                    if st.button("Import Data"):
                        with st.spinner("Importing data..."):
                            # Connect to database
                            conn = init_connection()
                            c = conn.cursor()
                            
                            # Track successful and failed imports
                            success_count = 0
                            failed_rows = []
                            
                            for idx, row in df.iterrows():
                                try:
                                    # Format date if needed
                                    if isinstance(row['date'], str):
                                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
                                    else:
                                        date_obj = row['date']
                                    
                                    # Insert into database
                                    if conn.__class__.__module__.startswith('psycopg2'):
                                        c.execute('''
                                            INSERT INTO transactions 
                                            (shop_name, date, sales, cost, cash_out, expenses, bank_deposit, created_by, created_at)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        ''', (
                                            row['shop_name'],
                                            date_obj.strftime('%Y-%m-%d'),
                                            row['sales'],
                                            row['cost'],
                                            row['cash_out'],
                                            row['expenses'],
                                            row['bank_deposit'],
                                            st.session_state.user,
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        ))
                                    else:
                                        c.execute('''
                                            INSERT INTO transactions 
                                            (shop_name, date, sales, cost, cash_out, expenses, bank_deposit, created_by, created_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        ''', (
                                            row['shop_name'],
                                            date_obj.strftime('%Y-%m-%d'),
                                            row['sales'],
                                            row['cost'],
                                            row['cash_out'],
                                            row['expenses'],
                                            row['bank_deposit'],
                                            st.session_state.user,
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        ))
                                    
                                    success_count += 1
                                except Exception as e:
                                    failed_rows.append((idx, str(e)))
                            
                            # Commit changes
                            conn.commit()
                            conn.close()
                            
                            # Show results
                            if success_count > 0:
                                st.success(f"Successfully imported {success_count} transactions!")
                            
                            if failed_rows:
                                st.error(f"Failed to import {len(failed_rows)} rows")
                                with st.expander("View failed rows"):
                                    for idx, error in failed_rows:
                                        st.write(f"Row {idx}: {error}")
            
            except Exception as e:
                st.error(f"Error processing file: {e}")
        
        # Also provide a template file for download
        st.markdown("<h3>Download Template</h3>", unsafe_allow_html=True)
        st.markdown("""
        Download our template file to ensure your data is formatted correctly:
        """)
        
        # Create a template DataFrame
        template_df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-01'],
            'shop_name': ['Gampaha', 'Nittambuwa'],
            'sales': [10000, 12000],
            'cost': [7000, 8000],
            'cash_out': [500, 600],
            'expenses': [json.dumps({"salary": 1000, "rent": 500, "light_bill": 200, "description": "January expenses"}),
                         json.dumps({"salary": 1200, "rent": 500, "light_bill": 220, "description": "January expenses"})],
            'bank_deposit': [2000, 2500]
        })
        
        # Convert to CSV for download
        csv = template_df.to_csv(index=False)
        st.download_button(
            label="Download CSV Template",
            data=csv,
            file_name="transactions_template.csv",
            mime="text/csv"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        display_placeholder("📁", "Bulk Data Import")
        
        st.markdown("""
        <div class='card' style='margin-top: 20px;'>
            <h3>Import Instructions</h3>
            <p>Follow these steps for a successful import:</p>
            <ol>
                <li>Download our template file</li>
                <li>Fill in your data for the month</li>
                <li>Ensure all required fields are complete</li>
                <li>Upload the completed file</li>
                <li>Review the preview and verify data</li>
                <li>Click "Import Data" to add to database</li>
            </ol>
            <p><strong>Note:</strong> The expenses column should be a JSON string or you can map individual expense columns.</p>
        </div>
        """, unsafe_allow_html=True)


def daily_sales_page():
    st.markdown("<h1 class='main-header'>Daily Sales Entry</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("sales_form"):
            col1, col2 = st.columns(2)
            with col1:
                shop_name = st.selectbox("Shop Name", ["Gampaha", "Nittambuwa"])
            with col2:
                date = st.date_input("Date", datetime.now().date())
            
            
            col1, col2, col3 = st.columns(3)
            with col1:
                sales = st.number_input("Total Sales (LKR)", min_value=0.0, step=100.0, format="%.2f")
            with col2:
                cost = st.number_input("Total Cost (LKR)", min_value=0.0, step=100.0, format="%.2f")
            with col3:
                cash_out = st.number_input("Cash Out (LKR)", min_value=0.0, step=100.0, format="%.2f")

            # Calculate gross profit
            gross_profit = sales - cost
            
            st.markdown("<h3 class='sub-header'>Expenses</h3>", unsafe_allow_html=True)
            
            # Organize expenses in columns
            col1, col2 = st.columns(2)
            expenses = {}
            
            with col1:
                expenses['salary'] = st.number_input("Salary", min_value=0.0, step=100.0, format="%.2f")
                expenses['rent'] = st.number_input("Rent", min_value=0.0, step=100.0, format="%.2f")
                expenses['light_bill'] = st.number_input("Light Bill", min_value=0.0, step=100.0, format="%.2f")
                expenses['phone_bill'] = st.number_input("Phone Bill", min_value=0.0, step=100.0, format="%.2f")
            
            with col2:
                expenses['water_bill'] = st.number_input("Water Bill", min_value=0.0, step=100.0, format="%.2f")
                expenses['petty_cash'] = st.number_input("Petty Cash", min_value=0.0, step=100.0, format="%.2f")
                expenses['home'] = st.number_input("Home", min_value=0.0, step=100.0, format="%.2f")
                expenses['other_expenses'] = st.number_input("Other Expenses", min_value=0.0, step=100.0, format="%.2f")
            
            expenses['description'] = st.text_area("Description/Notes", height=100)
            
            bank_deposit = st.number_input("Bank Deposit (Current Account)", min_value=0.0, step=100.0, format="%.2f")
            
            # Calculate remaining cash
            total_expenses = sum(v for k, v in expenses.items() if k != 'description')
            remaining_cash = sales - cash_out - total_expenses - bank_deposit
            
            # Visual indicator for remaining cash
            if remaining_cash >= 0:
                bg_color = "linear-gradient(120deg, #E0FFE4 0%, #F9FFF9 100%)"
                text_color = "#00D09C"
            else:
                bg_color = "linear-gradient(120deg, #FFE0E0 0%, #FFF9F9 100%)"
                text_color = "#FF5252"
                
            st.markdown(f"""
            <div style="padding: 15px; margin: 15px 0; background: {bg_color}; 
                        border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <h4 style="margin: 0; color: {text_color}; text-align: center;">Remaining Cash: LKR {remaining_cash:,.2f}</h4>
            </div>
            """, unsafe_allow_html=True)
            submitted = st.form_submit_button("Submit Transaction")
            if submitted:
                if sales < 0 or cost < 0 or cash_out < 0 or bank_deposit < 0:
                    st.error("Please enter valid positive values for sales, cost, cash out, and bank deposit.")
                else:
                    add_transaction(shop_name, date, sales, cost, cash_out, expenses, bank_deposit)

            
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        display_placeholder("💰", "Daily Sales Tracking")
        
        # Recent entries for quick reference
        st.markdown("<h3 class='sub-header'>Recent Entries</h3>", unsafe_allow_html=True)
        recent_entries = get_transactions(shop_filter=None, date_from=date - timedelta(days=7), date_to=date)
        
        if not recent_entries.empty:
            recent_entries = recent_entries.sort_values('date', ascending=False).head(5)
            
            for _, row in recent_entries.iterrows():
                st.markdown(f"""
                <div style="padding: 12px; margin-bottom: 12px; 
                            background: linear-gradient(145deg, #f8f9fa, #ffffff);
                            border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                            border-left: 4px solid #6C63FF;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <p style="margin: 0; font-weight: 600; color: #6C63FF;">{row['shop_name']}</p>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">{row['date']}</p>
                    </div>
                    <p style="margin: 5px 0 0 0; font-weight: 500;">Sales: <span style="color: #6C63FF;">LKR {row['sales']:,.2f}</span></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent entries found")

def bank_transactions_page():
    st.markdown("<h1 class='main-header'>Bank Transactions</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Bank Deposits", "Cheque Management"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>Bank Deposits History</h2>", unsafe_allow_html=True)
            
            # Date filter
            col_from, col_to = st.columns(2)
            with col_from:
                date_from = st.date_input("From Date", datetime.now().date() - timedelta(days=30))
            with col_to:
                date_to = st.date_input("To Date", datetime.now().date())
            
            # Shop filter
            shop_filter = st.selectbox("Shop Filter", ["All", "Gampaha", "Nittambuwa"], key="deposit_shop_filter")
            
            # Get filtered data
            df_deposits = get_transactions(shop_filter, date_from, date_to)
            
            if not df_deposits.empty:
                # Create deposits-only dataframe
                deposits_df = df_deposits[['date', 'shop_name', 'bank_deposit']].copy()
                deposits_df = deposits_df[deposits_df['bank_deposit'] > 0]
                
                if not deposits_df.empty:
                    # Calculate total
                    total_deposits = deposits_df['bank_deposit'].sum()
                    st.markdown(f"""
                    <div style="background: linear-gradient(120deg, #E0FFE4 0%, #F9FFF9 100%); 
                                 padding: 15px; border-radius: 10px; margin: 15px 0; text-align: center;">
                        <h4 style="margin: 0; color: #00D09C;">Total Deposits: LKR {total_deposits:,.2f}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show data
                    st.dataframe(deposits_df, hide_index=True, use_container_width=True)
                    
                    # Create deposit trend visualization
                    deposits_df['date'] = pd.to_datetime(deposits_df['date'])
                    deposits_by_date = deposits_df.groupby([pd.Grouper(key='date', freq='D'), 'shop_name'])['bank_deposit'].sum().reset_index()
                    
                    fig = px.line(deposits_by_date, 
                                 x='date', 
                                 y='bank_deposit', 
                                 color='shop_name',
                                 markers=True,
                                 labels={'bank_deposit': 'Deposit Amount (LKR)', 'date': 'Date'},
                                 title='Bank Deposits Over Time')
                    
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Deposit Amount (LKR)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Arial, sans-serif", size=12),
                        colorway=["#6C63FF", "#FF6584", "#00D09C", "#FFB800", "#FF5252"],
                        margin=dict(l=40, r=40, t=40, b=40),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No bank deposits found for the selected filters.")
            else:
                st.info("No transactions found for the selected filters.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            display_placeholder("🏦", "Bank Deposit Tracking")
            
            # Monthly summary
            st.markdown("<h3 class='sub-header'>Monthly Summary</h3>", unsafe_allow_html=True)
            
            if not df_deposits.empty:
                df_deposits['date'] = pd.to_datetime(df_deposits['date'])
                df_deposits['month'] = df_deposits['date'].dt.strftime('%b %Y')
                monthly_deposits = df_deposits.groupby('month')['bank_deposit'].sum().reset_index().sort_values('month', ascending=False)
                
                for _, row in monthly_deposits.head(6).iterrows():
                    st.markdown(f"""
                    <div style="padding: 15px; margin-bottom: 12px; 
                                background: linear-gradient(145deg, #f8f9fa, #ffffff);
                                border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <p style="margin: 0; font-weight: 600; color: #6C63FF;">{row['month']}</p>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; color: #00D09C;">LKR {row['bank_deposit']:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>Pass New Cheque</h2>", unsafe_allow_html=True)
            
            with st.form("cheque_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    date = st.date_input("Cheque Date", datetime.now().date(), key="cheque_date")
                with col_b:
                    shop_name = st.selectbox("Shop Name", ["Gampaha", "Nittambuwa"], key="cheque_shop")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    amount = st.number_input("Amount (LKR)", min_value=0.01, step=100.0, format="%.2f", key="cheque_amount")
                with col_b:
                    payee = st.text_input("Payee/Recipient", key="cheque_payee")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    cheque_number = st.text_input("Cheque Number", key="cheque_number")
                with col_b:
                    bank = st.selectbox("Bank", ["Commercial Bank", "People's Bank", "Bank of Ceylon", "HNB", "Sampath Bank", "Other"])
                
                submitted = st.form_submit_button("Pass Cheque")
                if submitted:
                    if not cheque_number or not payee:
                        st.error("Please enter both cheque number and payee name.")
                    else:
                        add_cheque(date, shop_name, amount, payee, cheque_number, bank)
            
            st.markdown("<h2 class='sub-header'>Cheque Registry</h2>", unsafe_allow_html=True)
            
            # Status filter
            status_filter = st.selectbox("Status Filter", ["All", "Pending", "Cleared", "Bounced"], key="cheque_status_filter")
            
            # Get filtered cheques
            df_cheques = get_cheques(status_filter)
            
            if not df_cheques.empty:
                # Add action buttons
                df_display = df_cheques.copy()
                
                # Show data
                st.dataframe(df_display, hide_index=True, use_container_width=True)
                
                # Cheque actions
                st.markdown("<h3>Cheque Actions</h3>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cheque_id = st.number_input("Cheque ID", min_value=1, step=1)
                
                with col2:
                    new_status = st.selectbox("New Status", ["Cleared", "Pending", "Bounced"])
                
                with col3:
                    if st.button("Update Status"):
                        # Check if the cheque ID exists
                        if cheque_id in df_cheques['id'].values:
                            update_cheque_status(cheque_id, new_status)
                            st.success(f"Cheque status updated to {new_status}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid cheque ID")
            else:
                st.info("No cheques found with the selected status.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Cheque Summary</h3>", unsafe_allow_html=True)
            
            # Get all cheques
            all_cheques = get_cheques()
            
            if not all_cheques.empty:
                # Status summary
                status_counts = all_cheques['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.pie(
                    status_counts, 
                    values='Count', 
                    names='Status',
                    title='Cheque Status Distribution',
                    color='Status',
                    color_discrete_map={
                        'Pending': '#FFB800',
                        'Cleared': '#00D09C',
                        'Bounced': '#FF5252'
                    },
                    hole=0.4
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Total amounts by status
                status_amounts = all_cheques.groupby('status')['amount'].sum().reset_index()
                
                for _, row in status_amounts.iterrows():
                    status_color = {
                        'Pending': '#FFB800',
                        'Cleared': '#00D09C',
                        'Bounced': '#FF5252'
                    }.get(row['status'], '#6C63FF')
                    
                    st.markdown(f"""
                    <div style="padding: 15px; margin-bottom: 12px; 
                                background: linear-gradient(145deg, #f8f9fa, #ffffff);
                                border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                                border-left: 5px solid {status_color};">
                        <p style="margin: 0; font-weight: 600; color: {status_color};">{row['status']}</p>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem;">LKR {row['amount']:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No cheque data available.")



def sales_visualization_page():
    st.markdown("<h1 class='main-header'>Sales Analytics</h1>", unsafe_allow_html=True)
    
    # Date and shop filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_from = st.date_input("From Date", datetime.now().date() - timedelta(days=365))
    with col2:
        date_to = st.date_input("To Date", datetime.now().date())
    with col3:
        shop_filter = st.selectbox("Shop Filter", ["All", "Gampaha", "Nittambuwa"])
    
    # Get filtered data
    df = get_transactions(shop_filter, date_from, date_to)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['expenses'] = df['expenses'].apply(json.loads)
        
        # Calculate profits
        df['cost'] = df['cost'].fillna(0)  # Handle any NULL values
        df['gross_profit'] = df['sales'] - df['cost']
        df['expense_total'] = df.apply(lambda row: sum(v for k, v in row['expenses'].items() 
                                                if k != 'description' and isinstance(v, (int, float))), axis=1)
        df['net_profit'] = df['gross_profit'] - df['expense_total']
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        total_sales = df['sales'].sum()
        avg_daily_sales = df.groupby('date')['sales'].sum().mean()
        max_sales_day = df.groupby('date')['sales'].sum().idxmax().strftime('%b %d, %Y')
        total_transactions = len(df)
        
        col1.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>Total Sales</p>
            <p class='metric-value'>LKR {total_sales:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col2.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>Avg Daily Sales</p>
            <p class='metric-value'>LKR {avg_daily_sales:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col3.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>Peak Sales Day</p>
            <p class='metric-value'>{max_sales_day}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col4.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>Total Entries</p>
            <p class='metric-value'>{total_transactions}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sales trends
        st.markdown("<h2 class='sub-header'>Sales Trends Over Time</h2>", unsafe_allow_html=True)
        sales_over_time = df.groupby([pd.Grouper(key='date', freq='W'), 'shop_name'])['sales'].sum().reset_index()
        
        fig = px.area(sales_over_time, 
                     x='date', 
                     y='sales', 
                     color='shop_name',
                     title='Weekly Sales Trend',
                     labels={'sales': 'Total Sales (LKR)', 'date': 'Date'},
                     line_shape='spline')
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Sales (LKR)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Arial, sans-serif", size=12),
            colorway=["#6C63FF", "#FF6584"],
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Shop comparison
        st.markdown("<h2 class='sub-header'>Shop Performance Comparison</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            shop_sales = df.groupby('shop_name')['sales'].sum().reset_index()
            fig = px.pie(shop_sales, 
                        values='sales', 
                        names='shop_name',
                        title='Total Sales Distribution',
                        color_discrete_sequence=["#6C63FF", "#FF6584"],
                        hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            avg_sales = df.groupby('shop_name')['sales'].mean().reset_index()
            fig = px.bar(avg_sales, 
                        x='shop_name', 
                        y='sales',
                        title='Average Daily Sales',
                        labels={'sales': 'Average Sales (LKR)', 'shop_name': ''},
                        color='shop_name',
                        color_discrete_map={
                            "Gampaha": "#6C63FF",
                            "Nittambuwa": "#FF6584"
                        })
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Expense analysis
        st.markdown("<h2 class='sub-header'>Expense Breakdown</h2>", unsafe_allow_html=True)
        
        # Aggregate expenses
        expense_categories = ['salary', 'rent', 'light_bill', 'water_bill', 
                             'phone_bill', 'petty_cash', 'home', 'other_expenses']
        expense_totals = {category: 0 for category in expense_categories}
        
        for expenses in df['expenses']:
            for category in expense_categories:
                expense_totals[category] += expenses.get(category, 0)
        
        expense_df = pd.DataFrame.from_dict(expense_totals, orient='index', columns=['amount']).reset_index()
        expense_df.columns = ['category', 'amount']
        expense_df = expense_df[expense_df['amount'] > 0]
        
        if not expense_df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.bar(expense_df, 
                            x='category', 
                            y='amount',
                            title='Expense Categories',
                            labels={'amount': 'Total Amount (LKR)', 'category': 'Expense Type'},
                            color='category',
                            color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(expense_df, 
                            values='amount', 
                            names='category',
                            title='Expense Distribution',
                            hole=0.4)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available for the selected period")
        
        # Sales distribution analysis
        st.markdown("<h2 class='sub-header'>Sales Distribution Analysis</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(df, 
                             x='sales', 
                             nbins=20,
                             title='Sales Distribution',
                             labels={'sales': 'Sales Amount (LKR)'},
                             color_discrete_sequence=["#6C63FF"])
            fig.update_layout(bargap=0.1)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.box(df, 
                        y='sales', 
                        x='shop_name',
                        title='Sales Distribution by Shop',
                        labels={'sales': 'Sales Amount (LKR)', 'shop_name': ''},
                        color='shop_name',
                        color_discrete_map={
                            "Gampaha": "#6C63FF",
                            "Nittambuwa": "#FF6584"
                        })
            st.plotly_chart(fig, use_container_width=True)
        
        # Profit analysis section (MOVED INSIDE THE FUNCTION)
        st.markdown("<h2 class='sub-header'>Profit Analysis</h2>", unsafe_allow_html=True)
        
        # Create profit trends chart
        profit_over_time = df.groupby([pd.Grouper(key='date', freq='W')]).\
            agg({'sales': 'sum', 'cost': 'sum', 'gross_profit': 'sum', 'net_profit': 'sum'}).\
            reset_index()
        
        # Long format for area chart
        profit_chart_data = pd.melt(
            profit_over_time, 
            id_vars=['date'],
            value_vars=['sales', 'cost', 'gross_profit', 'net_profit'],
            var_name='metric', 
            value_name='amount'
        )
        
        fig = px.area(profit_chart_data,
                     x='date',
                     y='amount',
                     color='metric',
                     labels={'amount': 'Amount (LKR)', 'date': 'Date'},
                     title='Weekly Profit Analysis',
                     color_discrete_map={
                        'sales': '#6C63FF',
                        'cost': '#FF5252',
                        'gross_profit': '#00D09C',
                        'net_profit': '#FFB800'
                    })
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Profit margins by shop
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate profit margins by shop
            shop_margins = df.groupby('shop_name').agg({
                'sales': 'sum',
                'gross_profit': 'sum',
                'net_profit': 'sum'
            }).reset_index()
            
            shop_margins['gross_margin'] = (shop_margins['gross_profit'] / shop_margins['sales'] * 100).round(2)
            shop_margins['net_margin'] = (shop_margins['net_profit'] / shop_margins['sales'] * 100).round(2)
            
            margin_data = pd.melt(
                shop_margins,
                id_vars=['shop_name'],
                value_vars=['gross_margin', 'net_margin'],
                var_name='margin_type',
                value_name='percentage'
            )
            
            fig = px.bar(margin_data,
                        x='shop_name',
                        y='percentage',
                        color='margin_type',
                        barmode='group',
                        title='Profit Margins by Shop (%)',
                        labels={'percentage': 'Margin %', 'shop_name': 'Shop', 'margin_type': 'Margin Type'},
                        color_discrete_map={
                            'gross_margin': '#00D09C',
                            'net_margin': '#FFB800'
                        })
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Profit contribution by shop
            shop_contrib = df.groupby('shop_name').agg({
                'gross_profit': 'sum',
                'net_profit': 'sum'
            }).reset_index()
            
            shop_contrib['gross_profit_pct'] = (shop_contrib['gross_profit'] / shop_contrib['gross_profit'].sum() * 100).round(2)
            shop_contrib['net_profit_pct'] = (shop_contrib['net_profit'] / shop_contrib['net_profit'].sum() * 100).round(2)
            
            contrib_data = pd.melt(
                shop_contrib,
                id_vars=['shop_name'],
                value_vars=['gross_profit', 'net_profit'],
                var_name='profit_type',
                value_name='amount'
            )
            
            fig = px.pie(contrib_data,
                        names='shop_name',
                        values='amount',
                        color='shop_name',
                        facet_col='profit_type',
                        title='Profit Contribution by Shop',
                        color_discrete_sequence=["#6C63FF", "#FF6584"])
            
            fig.update_layout(
                margin=dict(t=50, b=20),
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        display_placeholder("📈", "No data available for selected filters")

def prediction_page():
    st.markdown("<h1 class='main-header'>Sales Predictions</h1>", unsafe_allow_html=True)
    
    predictions = predict_next_month_sales()
    
    if predictions:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>Next Month Forecast</h2>", unsafe_allow_html=True)
            
            prediction_df = pd.DataFrame.from_dict(predictions, orient='index', columns=['predicted_sales']).reset_index()
            prediction_df.columns = ['shop_name', 'predicted_sales']
            
            fig = px.bar(prediction_df, 
                        x='shop_name', 
                        y='predicted_sales',
                        title='Predicted Sales for Next Month',
                        labels={'predicted_sales': 'Predicted Sales (LKR)', 'shop_name': ''},
                        color='shop_name',
                        color_discrete_map={
                            "Gampaha": "#6C63FF",
                            "Nittambuwa": "#FF6584"
                        })
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<h3 class='sub-header'>Prediction Details</h3>", unsafe_allow_html=True)
            st.dataframe(prediction_df, hide_index=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            display_placeholder("🔮", "AI-Powered Predictions")
            st.markdown("""
            <div class='card' style='margin-top: 20px;'>
                <h3>Prediction Methodology</h3>
                <p>Our predictions use a weighted average of:</p>
                <ul>
                    <li>Historical sales trends</li>
                    <li>Seasonal patterns</li>
                    <li>3-month moving average</li>
                    <li>Growth rate analysis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        display_placeholder("📊", "Not enough data for predictions yet")

def settings_page():
    st.markdown("<h1 class='main-header'>User Settings</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        display_placeholder("⚙️", "Account Settings")
        
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 class='sub-header'>Profile Information</h2>", unsafe_allow_html=True)
        
        conn = init_connection()
        try:
            c = conn.cursor()
            
            if conn.__class__.__module__.startswith('psycopg2'):
                c.execute("SELECT * FROM users WHERE username = %s", (st.session_state.user,))
            else:
                c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
            
            user_data = c.fetchone()
            
            if user_data:
                with st.form("profile_form"):
                    username = st.text_input("Username", value=user_data[0], disabled=True)
                    email = st.text_input("Email", value=user_data[4])
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    
                    if st.form_submit_button("Update Profile"):
                        update_data = {}
                        if email != user_data[4]:
                            update_data['email'] = email
                        if new_password:
                            if new_password == confirm_password:
                                update_data['password'] = hash_password(new_password)
                            else:
                                st.error("Passwords do not match")
                        
                        if update_data:
                            try:
                                set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
                                values = list(update_data.values()) + [st.session_state.user]
                                
                                if conn.__class__.__module__.startswith('psycopg2'):
                                    c.execute(f"UPDATE users SET {set_clause} WHERE username = %s", values)
                                else:
                                    set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                                    c.execute(f"UPDATE users SET {set_clause} WHERE username = ?", values)
                                
                                conn.commit()
                                st.success("Profile updated successfully!")
                            except Exception as e:
                                st.error(f"Update error: {e}")
            else:
                st.error("User not found")
        except Exception as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()
        st.markdown("</div>", unsafe_allow_html=True)

def logout():
    st.session_state.user = None
    st.success("Logged out successfully!")
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()