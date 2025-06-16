import streamlit as st
import pandas as pd
import tabula
import os
import tempfile
import plotly.graph_objects as go
from datetime import datetime
from src.scoring import score_customer

st.set_page_config(page_title="Mama_Mboga Scoring App", layout="wide")
st.title("📊 Mama_Mboga Scoring App")
st.markdown("This app processes and scores MPESA statements to evaluate creditworthiness.")

st.header("1️⃣ Upload MPESA PDF Statement")
uploaded_file = st.file_uploader("Upload your MPESA PDF statement", type=["pdf"])
password = st.text_input("Enter PDF Password (if required)", type="password")

if uploaded_file:
    with st.spinner("Reading PDF..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            dfs = tabula.read_pdf(tmp_path, pages="all", multiple_tables=True, password=password or None)
            os.remove(tmp_path)

            if not dfs:
                st.error("No tables found in the PDF.")
            else:
                df = pd.concat(dfs, ignore_index=True)
                df.columns = df.columns.str.strip()

                def identify_columns(df):
                    col_mapping = {}
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'paid in' in col_lower:
                            col_mapping['paid_in'] = col
                        elif 'paid out' in col_lower or 'withdrawn' in col_lower:
                            col_mapping['paid_out'] = col
                        elif 'balance' in col_lower:
                            col_mapping['balance'] = col
                        elif 'completion' in col_lower or 'date' in col_lower or 'time' in col_lower:
                            col_mapping['date'] = col
                        elif 'details' in col_lower or 'description' in col_lower:
                            col_mapping['details'] = col
                        elif 'transaction type' in col_lower or 'type' in col_lower:
                            col_mapping['transaction_type'] = col
                    return col_mapping

                col_map = identify_columns(df)

                df['PAID_IN'] = pd.to_numeric(df[col_map['paid_in']].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                df['PAID_OUT'] = pd.to_numeric(df[col_map['paid_out']].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                df['BALANCE'] = pd.to_numeric(df[col_map['balance']].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                df['DATE'] = pd.to_datetime(df[col_map['date']], errors='coerce')
                df['DETAILS'] = df[col_map['details']].astype(str)
                df['TRANSACTION_TYPE'] = df[col_map['transaction_type']].astype(str)

                def classify(row):
                    combined = f"{row['DETAILS']} {row['TRANSACTION_TYPE']}".lower()
                    if 'loan' in combined or 'fuliza' in combined:
                        return 'Loan'
                    elif 'received' in combined or 'deposit' in combined or 'reversal' in combined:
                        return 'Income'
                    elif 'withdraw' in combined or 'atm' in combined:
                        return 'Withdrawal'
                    elif 'paybill' in combined or 'buy goods' in combined:
                        return 'PayBill'
                    elif 'transfer' in combined or 'send money' in combined:
                        return 'Transfer'
                    elif 'airtime' in combined or 'bundle' in combined:
                        return 'Airtime/Data'
                    elif row['PAID_OUT'] > 0:
                        return 'Expense'
                    elif row['PAID_IN'] > 0:
                        return 'Income'
                    return 'Other'

                df['CATEGORY'] = df.apply(classify, axis=1)
                df_txn = df[~df['TRANSACTION_TYPE'].str.lower().str.contains('total|summary', na=False)]

                total_in = df_txn['PAID_IN'].sum()
                total_out = df_txn['PAID_OUT'].sum()
                cashflow = total_in + total_out
                net_cashflow = total_in - total_out
                balance_avg = df_txn['BALANCE'].max()
                last_date = df_txn['DATE'].max()
                days_since_last = (datetime.now() - last_date).days if pd.notnull(last_date) else None

                def compute_mpesa_scores(cashflow, balance_avg, days_since_last):
                    cashflow_score = 5 if cashflow <= 100_000 else 10 if cashflow <= 200_000 else 16
                    balance_score = 4 if balance_avg <= 2000 else 8 if balance_avg <= 5000 else 16
                    recent_score = 4 if days_since_last is not None and days_since_last <= 6 else 2 if days_since_last and days_since_last <= 13 else 0
                    return {
                        "mpesa_cashflow": cashflow_score,
                        "mpesa_balance_avg": balance_score,
                        "mpesa_recent_days": recent_score,
                    }

                scores = compute_mpesa_scores(cashflow, balance_avg, days_since_last)

                st.header("2️⃣ Manual Input")
                with st.form("manual_inputs"):
                    st.subheader("📟 Business Profile")
                    business_age = st.number_input("Age of Business (months)", min_value=0.0)
                    stock_value = st.number_input("Average Daily Stock Value (KES)", min_value=0.0)

                    st.subheader("🡭 Neighbour Referrals")
                    neighbor_ability = st.selectbox("Neighbor's Ability to Repay (1–10)", list(range(1, 11)))
                    neighbor_willingness = st.selectbox("Neighbor's Willingness to Repay (1–10)", list(range(1, 11)))
                    familiarity = st.selectbox("Familiarity Level", ["Barely", "Somewhat", "Neutral", "Well", "Very Well"])
                    familiarity_score = {"Barely": 1, "Somewhat": 2, "Neutral": 3, "Well": 4, "Very Well": 5}[familiarity]

                    st.subheader("🧑‍💼 Loan Officer Review")
                    officer_ability = st.selectbox("Officer's Ability to Repay (1–10)", list(range(1, 11)))
                    officer_willingness = st.selectbox("Officer's Willingness to Repay (1–10)", list(range(1, 11)))

                    submit_btn = st.form_submit_button("✅ Get Final Score")

                if submit_btn:
                    business_age_score = 1.25 if business_age <= 11 else 2.5 if business_age <= 23 else 3.75 if business_age <= 35 else 5
                    avg_stock_score = 2 if stock_value < 2000 else 4 if stock_value < 4000 else 6 if stock_value < 6000 else 8 if stock_value < 8000 else 10

                    metrics = {
                        "business_age_score": business_age_score,
                        "avg_stock_score": avg_stock_score,
                        "neighbor_ability": neighbor_ability,
                        "neighbor_willingness": neighbor_willingness,
                        "neighbor_familiarity": familiarity_score,
                        "officer_ability": officer_ability,
                        "officer_willingness": officer_willingness,
                        "mpesa_cashflow": scores['mpesa_cashflow'],
                        "mpesa_balance_avg": scores['mpesa_balance_avg'],
                        "mpesa_recent_days": scores['mpesa_recent_days'],
                    }

                    result = score_customer(metrics)
                    final_score = result['score']
                    decision = result['decision']
                    risk = "Low Risk" if final_score >= 60 else "Moderate Risk" if final_score >= 50 else "High Risk"

                    st.header("3️⃣ Credit Score Result")
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=final_score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Credit Score (0–100)"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "black"},
                            'steps': [
                                {'range': [0, 40], 'color': "#e60000"},
                                {'range': [40, 50], 'color': "#ff6600"},
                                {'range': [50, 60], 'color': "#ffcc00"},
                                {'range': [60, 100], 'color': "#66cc66"},
                            ],
                        }
                    ))
                    st.plotly_chart(fig)

                    st.metric("Decision", decision)
                    st.metric("Risk Classification", risk)

                    st.subheader("📋 MPESA Summary Metrics")
                    mpesa_summary = pd.DataFrame({
                        "Metric": ["Total Paid In", "Total Withdrawn", "Cashflow Volume", "Net Cashflow", "Avg Weekly Balance", "Days Since Last Txn"],
                        "Value (KES)": [
                            f"{total_in:,.0f}",
                            f"{total_out:,.0f}",
                            f"{cashflow:,.0f}",
                            f"{net_cashflow:,.0f}",
                            f"{balance_avg:,.0f}",
                            f"{days_since_last} days"
                        ]
                    })
                    st.table(mpesa_summary)

        except Exception as e:
            st.error(f"❌ Error: {e}")
