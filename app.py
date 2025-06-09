import streamlit as st
from src.extraction import extract_pdf_text, write_to_excel
from src.classification import classify_transactions
from src.scoring import score_customer
import tempfile
from datetime import datetime
import plotly.graph_objects as go
import traceback

st.set_page_config(page_title="Mama_Mboga Scoring", layout="centered")
st.title("📊 Mama_Mboga Scoring App")

# Upload PDF & password
pdf_file = st.file_uploader("Upload MPESA PDF Statement", type=["pdf"])
pdf_password = st.text_input("Enter PDF Password (if any)", type="password")

if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    try:
        # Step 1: Extract & Save
        text = extract_pdf_text(tmp_path, password=pdf_password)
        excel_path = tmp_path.replace(".pdf", ".xlsx")
        write_to_excel(text, excel_path)
        st.success("✅ PDF extracted and saved.")

        # Step 2: Parse Transactions
        parsed_df = classify_transactions(excel_path)[0]
        if parsed_df.empty:
            st.warning("⚠️ No valid transactions found.")
            st.stop()

        # Step 3: Manual Inputs
        with st.form("manual_inputs"):
            st.subheader("📦 Business Profile")
            business_age = st.selectbox("Age of Business (months)", [6, 12, 24, 36])
            stock_value = st.number_input("Average Daily Stock Value (KES)", min_value=0.0)

            st.subheader("👥 Neighbour Referrals")
            neighbor_ability = st.selectbox("Neighbor's Ability to Repay (1–10)", list(range(1, 11)))
            neighbor_willingness = st.selectbox("Neighbor's Willingness to Repay (1–10)", list(range(1, 11)))
            familiarity = st.selectbox("Familiarity Level", ["Barely", "Somewhat", "Neutral", "Well", "Very Well"])
            familiarity_score = {"Barely": 1, "Somewhat": 2, "Neutral": 3, "Well": 4, "Very Well": 5}[familiarity]

            st.subheader("🧑‍💼 Loan Officer Review")
            officer_ability = st.selectbox("Officer's Ability to Repay (1–10)", list(range(1, 11)))
            officer_willingness = st.selectbox("Officer's Willingness to Repay (1–10)", list(range(1, 11)))

            submit_btn = st.form_submit_button("🧮 Compute Score")

        if submit_btn:
            # Step 4: Compute MPESA Metrics
            cashflow = parsed_df["Amount"].abs().sum()
            balance_avg = parsed_df.set_index("Date")["Balance"].resample("W").mean().tail(4).mean()
            days_since_last = (datetime.today() - parsed_df["Date"].max()).days
            p2p_value = parsed_df[
                parsed_df["Description"].str.contains("Pay Bill", case=False, na=False)
            ]["Amount"].abs().sum()

            # Step 5: Convert to Scores
            cashflow_score = 5 if cashflow <= 100_000 else 10 if cashflow <= 200_000 else 16
            balance_score = 4 if balance_avg <= 2000 else 8 if balance_avg <= 5000 else 16
            recent_score = 4 if days_since_last <= 6 else 2 if days_since_last <= 13 else 0
            p2p_score = 1 if p2p_value <= 50000 else 2.5 if p2p_value <= 150000 else 4

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
                "mpesa_recent_days": recent_score,
                "mpesa_p2p": p2p_score
            }

            # Step 6: Final Score + Decision
            result = score_customer(metrics)
            score = result["score"]
            decision = result["decision"]
            risk = "Low Risk" if score >= 60 else "Moderate Risk" if score >= 50 else "High Risk"

            st.subheader("✅ Final Scorecard")
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
                        {'range': [60, 75], 'color': "#66cc66"},
                        {'range': [75, 100], 'color': "#009933"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': score
                    }
                }
            ))
            st.plotly_chart(fig)

            # Step 8: Show MPESA Summary with Raw Values
            st.subheader("📄 MPESA Statement Summary (Raw Values)")
            summary_data = {
                "Metric": [
                    "Total Cashflow (IN + OUT)",
                    "Average Weekly Balance",
                    "Days Since Last Transaction",
                    "Total Paybill (IN + OUT)"
                ],
                "Value": [
                    f"{cashflow:,.0f} KES",
                    f"{balance_avg:,.0f} KES",
                    f"{days_since_last} days",
                    f"{p2p_value:,.0f} KES"
                ]
            }
            st.table(summary_data)

    except Exception as e:
        st.error("❌ An error occurred.")
        st.code(traceback.format_exc())
