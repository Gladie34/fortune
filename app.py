import streamlit as st
import pandas as pd
import tabula
import os
import tempfile
import base64
import io
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="Mama_Mboga Scoring App", layout="wide")

# Title
st.title("📊 Mama_Mboga Scoring App")
st.markdown("This app helps process and score MPESA statements to evaluate financial behavior and creditworthiness.")

# Step 1: Upload MPESA PDF Statement
st.header("1️⃣ Upload MPESA PDF Statement")
uploaded_file = st.file_uploader("Upload your MPESA PDF statement", type=["pdf"])
password = st.text_input("Enter PDF Password (if required)", type="password")

if uploaded_file:
    with st.spinner("Reading PDF..."):
        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Extract tables using tabula with password support
        try:
            dfs = tabula.read_pdf(tmp_path, pages="all", multiple_tables=True, password=password if password else None)
            os.remove(tmp_path)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                st.success("PDF successfully read and transactions extracted!")
                st.write("### Extracted Transactions (Preview)")
                st.dataframe(df.head())
            else:
                st.error("No tables found in the PDF.")
                df = None
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            df = None

    # Proceed only if DataFrame is valid
    if df is not None:
        # Step 2: Classify transactions
        st.header("2️⃣ Classify Transactions")

        def classify(row):
            description = row["Details"] if "Details" in row else row.get("Transaction Details", "")
            if isinstance(description, str):
                desc = description.lower()
                if "loan" in desc or "fuliza" in desc:
                    return "Loan"
                elif "received" in desc or "customer" in desc:
                    return "Income"
                elif "paid" in desc or "buy" in desc:
                    return "Expense"
                elif "withdraw" in desc:
                    return "Withdraw"
                elif "deposit" in desc:
                    return "Deposit"
            return "Unclassified"

        df["Category"] = df.apply(classify, axis=1)

        st.write("### Review and Edit Classifications")
        edited_df = st.data_editor(df, num_rows="dynamic")
        st.session_state["classified_df"] = edited_df

        # Step 3: Manual Scoring
        st.header("3️⃣ Manual Scoring")
        st.markdown("Enter manual scores for each metric below (0 - 10):")
        income_stability = st.slider("Income Stability", 0, 10, 5)
        repayment_behavior = st.slider("Repayment Behavior", 0, 10, 5)
        savings_behavior = st.slider("Savings Behavior", 0, 10, 5)
        manual_score = (income_stability + repayment_behavior + savings_behavior) / 3
        st.success(f"Manual Score: **{manual_score:.2f}/10**")

        # Step 4: Auto Score + Final Score
        st.header("4️⃣ Final Score Calculation")
        # Remove unnecessary columns and clean up
        columns_to_keep = ['TRANSACTION TYPE', 'PAID IN', 'PAID OUT', 'Receipt No.',
                           'Completion Time', 'Details', 'Transaction Status', 'Balance', 'Category']

        # Filter to only keep useful columns
        edited_df_clean = edited_df[columns_to_keep].copy()

        # Fill NaN values in amount columns
        edited_df_clean['PAID IN'] = edited_df_clean['PAID IN'].fillna(0)
        edited_df_clean['PAID OUT'] = edited_df_clean['PAID OUT'].fillna(0)

        # Now calculate your totals
        income_total = edited_df_clean[edited_df_clean["Category"] == "Income"]["PAID IN"].sum()
        expense_total = edited_df_clean[edited_df_clean["Category"] == "Expense"]["PAID OUT"].sum()

        if expense_total > 0:
            ratio = income_total / expense_total
            auto_score = min(10, ratio * 2)
        else:
            auto_score = 5

        st.info(f"Auto Score: **{auto_score:.2f}/10**")
        final_score = (manual_score + auto_score) / 2
        st.subheader(f"🏁 Final Score: **{final_score:.2f}/10**")

        # Step 5: Visualization
        st.header("5️⃣ Results Visualization")
        st.markdown("### Category Distribution")
        category_counts = edited_df_clean["Category"].value_counts()

        # Create summary table
        summary_data = {
            "Category": category_counts.index,
            "Number of Transactions": category_counts.values,
            "Percentage": (category_counts.values / category_counts.sum() * 100).round(2)
        }
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

        # Financial Summary Table
        st.markdown("### Financial Summary")
        financial_summary = []
        for category in edited_df_clean["Category"].unique():
            category_data = edited_df_clean[edited_df_clean["Category"] == category]
            # Convert to numeric, coerce errors to NaN, then fill NaN with 0
            paid_in = pd.to_numeric(category_data["PAID IN"], errors='coerce').fillna(0).sum()
            paid_out = pd.to_numeric(category_data["PAID OUT"], errors='coerce').fillna(0).sum()
            net_amount = paid_in - paid_out

            financial_summary.append({
                "Category": category,
                "Total Paid In": f"KSh {paid_in:,.2f}",
                "Total Paid Out": f"KSh {paid_out:,.2f}",
                "Net Amount": f"KSh {net_amount:,.2f}"
            })

        financial_df = pd.DataFrame(financial_summary)
        st.dataframe(financial_df, use_container_width=True)

        # Download
        st.markdown("### ⬇️ Download Classified Data")
        csv_buffer = io.StringIO()
        edited_df_clean.to_csv(csv_buffer, index=False)
        b64 = base64.b64encode(csv_buffer.getvalue().encode()).decode()
        st.markdown(f'<a href="data:file/csv;base64,{b64}" download="classified_transactions.csv">Download CSV File</a>', unsafe_allow_html=True)

else:
    st.info("Please upload an MPESA PDF statement to get started.")

