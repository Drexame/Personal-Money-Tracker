#!/usr/bin/env python
# coding: utf-8

# # Import Libraries & Declare Variables

# In[2]:


import pandas as pd
import requests
import streamlit as st
import datetime


# In[3]:


url = "https://script.google.com/macros/s/AKfycbyJ48KDFZTHM1mjGFWHkjhWar4-3OPLreGeWsq81beUuoN6DlrYx9roN_ofdvwXUpG9/exec"


# # Test Data Fetch

# # Fetch Categories from Google API

# In[12]:


# Create function for data gathering
@st.cache_data
def get_categories(url):
    url = url
    response = requests.get(url)

    if response.status_code == 200: # If data fetch is successful
        data = response.json()
        df = pd.DataFrame(data)
        return df
    else:
        st.error("Failed to fetch categories") # If data fetch is unsucessful
        return pd.DataFrame()


# In[15]:


# Fetch data using endpoint url
categories_df = get_categories(url)


# In[17]:


categories_df.head()


# # Cutting up Data for Different Categories

# # Coding Streamlit App

# In[19]:


# --- Streamlit App Layout ---
st.title("Personal Finance Tracker")

# Date and Amount
date = st.date_input("Date:")
amount = st.number_input("Input amount here:", min_value=0.0, format="%.2f")

# Classification Buttons
# Initialize session state
if "classification" not in st.session_state:
    st.session_state.classification = None

# Classification Buttons
st.subheader("Classify the amount:")
col1, col2, col3 = st.columns(3)

if col1.button("Income"):
    st.session_state.classification = "Income"

if col2.button("Expense"):
    st.session_state.classification = "Expense"

if col3.button("Movement"):
    st.session_state.classification = "Movement"

classification = st.session_state.classification

# Transaction Fee for Movement
with_fee = None
if classification == "Movement":
    st.subheader("With Transaction Fee?")
    col1, col2 = st.columns(2)
    if col1.button("Yes"):
        st.session_state.with_fee = True
    if col2.button("No"):
        st.session_state.with_fee = False
    with_fee = st.session_state.get("with_fee", False)

    # Fee input area
    if with_fee:
        fee_amount = st.number_input("Input Transaction Amount (Fee)", min_value=0.0, format="%.2f")
    else:
        fee_amount = 0.0  # Not editable


# Specific Category dropdown (reacts to classification)
st.subheader("Choose the specific category")

if classification:
    filtered_categories = categories_df[
        categories_df["Classification"] == classification
    ]

    specific_category = st.selectbox(
        "Specific Category",
        filtered_categories["Specific Category"].unique()
    )

    subcategory = st.selectbox(
        "Sub-category",
        filtered_categories[
            filtered_categories["Specific Category"] == specific_category
        ]["Subcategory"].unique()
    )
else:
    st.info("Select a classification to see categories")

# Description
description = st.text_area("Description of the Amount")

# Wallets
## Create a dataframe for wallets
wallet_options = categories_df[categories_df["Classification"] == "Wallet"]["Subcategory"].unique().tolist()

## Code source and end wallets
st.subheader("Choose the source wallet")
if classification in ["Expense", "Movement"] and wallet_options:
    source_wallet = st.selectbox("Source Wallet", wallet_options)
else:
    st.selectbox("Source Wallet", ["Not editable"], disabled=True)
    source_wallet = None

st.subheader("Choose the end wallet")
if classification in ["Income", "Movement"] and wallet_options:
    end_wallet = st.selectbox("End Wallet", wallet_options)
else:
    st.selectbox("End Wallet", ["Not editable"], disabled=True)
    end_wallet = None

# Prepare to submit the transaction (store in JSON format)
# --- Submit Transaction ---
if st.button("Submit Transaction"):
    # Adjust amount sign
    adj_amount = float(amount)
    if classification == "Expense":
        adj_amount = -abs(adj_amount)
    elif classification == "Income":
        adj_amount = abs(adj_amount)

    transactions_to_post = []

    if classification == "Movement":
        # Source wallet transaction (negative)
        transactions_to_post.append({
            "Date": date.isoformat(),
            "Amount": -abs(adj_amount),
            "Classification": classification,
            "Specific Category": specific_category,
            "Subcategory": subcategory,
            "Description": description,
            "Source Wallet": source_wallet,
            "End Wallet": None
        })
        # End wallet transaction (positive)
        transactions_to_post.append({
            "Date": date.isoformat(),
            "Amount": abs(adj_amount),
            "Classification": classification,
            "Specific Category": specific_category,
            "Subcategory": subcategory,
            "Description": description,
            "Source Wallet": None,
            "End Wallet": end_wallet
        })
        # Fee transaction if applicable
        if with_fee and fee_amount > 0:
            transactions_to_post.append({
                "Date": date.isoformat(),
                "Amount": fee_amount,
                "Classification": classification,
                "Specific Category": specific_category,
                "Subcategory": subcategory,
                "Description": "Transaction Fee)",
                "Source Wallet": source_wallet,
                "End Wallet": None
            })
    else:
        # Normal single transaction
        transactions_to_post.append({
            "Date": date.isoformat(),
            "Amount": adj_amount,
            "Classification": classification,
            "Specific Category": specific_category if classification else None,
            "Subcategory": subcategory if classification else None,
            "Description": description,
            "Source Wallet": source_wallet,
            "End Wallet": end_wallet
        })

    # Post each transaction to Google Sheets
    for txn in transactions_to_post:
        try:
            response = requests.post(url, json=txn)
            if response.status_code != 200:
                st.error(f"Failed to submit transaction: {response.status_code}")
        except Exception as e:
            st.error(f"Error submitting transaction: {e}")

    st.success("Transaction(s) submitted successfully!")

    # Optional: clear session state to reset form automatically after submission
    for key in ["classification", "with_fee"]:
        if key in st.session_state:
            del st.session_state[key]

# --- Log Another Transaction button ---
if st.button("Log Another Transaction"):
    # Clear session state for all relevant form fields
    for key in ["classification", "with_fee", "date", "amount", "description"]:
        if key in st.session_state:
            del st.session_state[key]

    # Stop current script execution to trigger a clean rerun
    st.stop()


# In[ ]:





# 
