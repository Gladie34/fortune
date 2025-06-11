import streamlit as st
import tempfile
import os
import pandas as pd
from datetime import datetime
from plotly import graph_objects as go

from src.extraction import extract_text_from_pdf, save_text_to_excel
from src.classification import classify_transactions
from src.scoring import score_customer

# --- Streamlit Setup ---
st.set_page_config(page_title="Mama_Mboga Scoring", layout="wide")
st.title("📊 Mama_Mboga Scoring App")

# --- Upload PDF ---
st.header("Upload MPESA PDF Statement")
pdf_file = st.file_uploader("Choose PDF File", type=["pdf"])
pdf_password = st.text_input("PDF Password (if any)", type="password")

if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(pdf_file.read())
        pdf_path = tmp_pdf.name

    try:
        # Step 1: Extract text from PDF
        text = extract_text_from_pdf(pdf_path, pdf_password or None)

        # Step 2: Save text to Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
            excel_path = tmp_xlsx.name
            save_text_to_excel(text, excel_path)

        # Step 3: Classify structured transactions
        df = classify_transactions(excel_path)
        st.success("✅ MPESA statement parsed successfully.")

        # --- Manual Inputs ---
        with st.form("manual_inputs"):
            st.subheader("🧾 Business Profile")
            business_age = st.number_input("Age of Business (months)", min_value=0.0)
            stock_value = st.number_input("Average Daily Stock Value (KES)", min_value=0.0)

            st.subheader("🧍 Neighbour Referrals")
            neighbor_ability = st.selectbox("Neighbor's Ability to Repay (1–10)", list(range(1, 11)))
            neighbor_willingness = st.selectbox("Neighbor's Willingness to Repay (1–10)", list(range(1, 11)))
            familiarity = st.selectbox("Familiarity Level", ["Barely", "Somewhat", "Neutral", "Well", "Very Well"])
            familiarity_score = {"Barely": 1, "Somewhat": 2, "Neutral": 3, "Well": 4, "Very Well": 5}[familiarity]

            st.subheader("🧑‍💼 Loan Officer Review")
            officer_ability = st.selectbox("Officer's Ability to Repay (1–10)", list(range(1, 11)))
            officer_willingness = st.selectbox("Officer's Willingness to Repay (1–10)", list(range(1, 11)))

            submit_btn = st.form_submit_button("✅ Compute Score")

        if submit_btn:
            # Step 4: Compute MPESA Metrics
            cashflow = df["PAID IN"].sum() + df["WITHDRAWN"].sum()
            balance_avg = df.set_index("Completion Time")["BALANCE"].resample("W").mean().tail(4).mean()
            days_since_last = (datetime.today() - df["Completion Time"].max()).days

            # Step 5: Convert to Scores
            cashflow_score = 5 if cashflow <= 100_000 else 10 if cashflow <= 200_000 else 16
            balance_score = 4 if balance_avg <= 2000 else 8 if balance_avg <= 5000 else 16
            recent_score = 4 if days_since_last <= 6 else 2 if days_since_last <= 13 else 0

            metrics = {
                "business_age_score": 1.25 if business_age <= 11 else 2.5 if business_age <= 23 else 3.75 if business_age <= 35 else 5,
                "avg_stock_score": 2 if stock_value < 2000 else 4 if stock_value < 4000 else 6 if stock_value < 6000 else 8 if stock_value < 8000 else 10,
                "neighbor_ability": neighbor_ability,
                "neighbor_willingness": neighbor_willingness,
                "neighbor_familiarity": familiarity_score,
                "officer_ability": officer_ability,
                "officer_willingness": officer_willingness,
                "mpesa_cashflow": cashflow_score,
                "mpesa_balance_avg": balance_score,
                "mpesa_recent_days": recent_score
            }

            # Step 6: Final Score + Decision
            result = score_customer(metrics)
            score = result["score"]
            decision = result["decision"]
            risk = "Low Risk" if score >= 60 else "Moderate Risk" if score >= 50 else "High Risk"

            st.subheader("📈 Final Scorecard")
            st.metric("Credit Score", round(score, 2))
            st.metric("Decision", decision)
            st.metric("Risk Classification", risk)

            # Step 7: Score Gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
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

        os.remove(pdf_path)
        os.remove(excel_path)

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("Please upload a PDF statement to begin.")
