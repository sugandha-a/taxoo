import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Initialize database
conn = sqlite3.connect("taxo.db", check_same_thread=False)
cursor = conn.cursor()

# Database Setup
def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        username TEXT UNIQUE NOT NULL, 
                        password TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER NOT NULL, 
                        property_id TEXT UNIQUE NOT NULL, 
                        address TEXT NOT NULL, 
                        size INTEGER NOT NULL, 
                        type TEXT NOT NULL, 
                        ownership_details TEXT NOT NULL, 
                        FOREIGN KEY(user_id) REFERENCES users(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        property_id TEXT NOT NULL, 
                        amount REAL NOT NULL, 
                        payment_date TEXT NOT NULL,
                        FOREIGN KEY(property_id) REFERENCES properties(property_id))''')
    conn.commit()

# Call create_tables() to ensure tables exist
create_tables()

# Database Functions
def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    return cursor.fetchone()

def add_property(user_id, property_id, address, size, property_type, ownership_details):
    cursor.execute('''INSERT INTO properties 
                      (user_id, property_id, address, size, type, ownership_details) 
                      VALUES (?, ?, ?, ?, ?, ?)''', 
                   (user_id, property_id, address, size, property_type, ownership_details))
    conn.commit()

def get_properties(user_id):
    cursor.execute("SELECT id, property_id, address, size, type, ownership_details FROM properties WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

def record_payment(property_id, amount):
    cursor.execute("INSERT INTO payments (property_id, amount, payment_date) VALUES (?, ?, ?)",
                   (property_id, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_payment_history(property_id):
    cursor.execute("SELECT * FROM payments WHERE property_id = ?", (property_id,))
    return cursor.fetchall()

# UI Customizations
st.markdown(
    """
    <style>
    .main {background-color: #121212; color: #00ff00;}
    .stButton > button {background-color: #00ff00; color: black; font-weight: bold;}
    .stTitle {font-size: 40px; font-weight: bold; color: #00ff00;}
    .stHeader {color: #00ff00;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ **Taxo: Online Property Tax Management System** 🛡️")

# User Registration
st.subheader("👤 User Registration")
username = st.text_input("Enter Username")
password = st.text_input("Enter Password", type="password")
if st.button("Register"):
    if register_user(username, password):
        st.success("Registration successful! 🎉")
    else:
        st.error("❌ Username already exists.")

# User Login
st.subheader("🔐 User Login")
login_username = st.text_input("Login Username")
login_password = st.text_input("Login Password", type="password")
if st.button("Login"):
    user = login_user(login_username, login_password)
    if user:
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = user[0]
        st.success("Login successful! Welcome back! 🎉")
    else:
        st.error("❌ Invalid credentials.")

# Property Registration
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.subheader("🏠 Register Property")
    property_id = st.text_input("Property ID")
    address = st.text_input("Address")
    size = st.text_input("Size (sq. ft)")
    property_type = st.selectbox("Property Type", ["Residential", "Commercial", "Industrial"])
    ownership_details = st.text_area("Ownership Details")

    if st.button("Register Property"):
        add_property(st.session_state["user_id"], property_id, address, size, property_type, ownership_details)
        st.success("Property registered successfully! 🎉")

    # Show Registered Properties
    st.subheader("📋 My Properties")
    properties = pd.DataFrame(get_properties(st.session_state["user_id"]), 
                              columns=["ID", "Property ID", "Address", "Size", "Type", "Ownership Details"])
    if not properties.empty:
        st.write(properties)

# Tax Calculation and Payment
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.subheader("💸 Calculate Tax and Pay")
    TAX_RATES = {"Residential": 0.01, "Commercial": 0.015, "Industrial": 0.02}
    
    if not properties.empty:
        selected_property_id = st.selectbox("Select Property ID", properties["Property ID"])
        property_value = st.number_input("Enter Property Value")
        property_type = properties[properties["Property ID"] == selected_property_id]["Type"].values[0]
        tax_amount = property_value * TAX_RATES[property_type]
        st.write(f"💰 Calculated Tax: {tax_amount}")

        if st.button("Pay Tax"):
            record_payment(selected_property_id, tax_amount)
            st.success(f"🎉 Payment of {tax_amount} successful!")
    else:
        st.info("No properties found. Please register a property first.")

# Payment History
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.subheader("📜 Payment History")
    if not properties.empty:
        selected_property_id = st.selectbox("Select a Property ID to View Payment History", properties["Property ID"])
        payment_history = get_payment_history(selected_property_id)
        if payment_history:
            payment_df = pd.DataFrame(payment_history, columns=["ID", "Property ID", "Amount", "Payment Date"])
            st.write(payment_df)
        else:
            st.info("No payments made for this property yet.")
    else:
        st.info("No properties found. Please register a property first.")
