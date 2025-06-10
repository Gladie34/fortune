import streamlit as st
import pandas as pd
import tabula
import os
import tempfile
import base64
import io
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

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
                elif "pay bill" in desc or "paybill" in desc:
                    return "PayBill"
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

        # Step 4: Enhanced Score Calculation with MPESA Metrics
        st.header("4️⃣ Enhanced Score Calculation")

        # Clean up data for calculations
        columns_to_keep = ['TRANSACTION TYPE', 'PAID IN', 'PAID OUT', 'Receipt No.',
                           'Completion Time', 'Details', 'Transaction Status', 'Balance', 'Category']

        edited_df_clean = edited_df[columns_to_keep].copy()

        print("Debug: Cleaned DataFrame Columns:", edited_df_clean.columns.tolist())

        # Fill NaN values in amount columns
        edited_df_clean['PAID IN'] = pd.to_numeric(edited_df_clean['PAID IN'], errors='coerce').fillna(0)
        edited_df_clean['PAID OUT'] = pd.to_numeric(edited_df_clean['PAID OUT'], errors='coerce').fillna(0)
        edited_df_clean['Balance'] = pd.to_numeric(edited_df_clean['Balance'], errors='coerce').fillna(0)

        # Create Amount column (total transaction value)
        edited_df_clean['Amount'] = edited_df_clean['PAID IN'] + edited_df_clean['PAID OUT']

        # Parse dates from Completion Time
        try:
            edited_df_clean['Date'] = pd.to_datetime(edited_df_clean['Completion Time'], errors='coerce')
            edited_df_clean = edited_df_clean.dropna(subset=['Date'])
            edited_df_clean = edited_df_clean.sort_values('Date')
        except:
            st.warning("Could not parse dates properly. Using current date for calculations.")
            edited_df_clean['Date'] = datetime.now()

        # Calculate MPESA Metrics
        st.subheader("📊 MPESA Financial Metrics")

        # Debug: Show the dataframe structure to understand the data
        st.write("**Debug: Data Structure**")
        st.write("Available columns:", edited_df_clean.columns.tolist())
        st.write("Transaction Types found:", edited_df_clean['TRANSACTION TYPE'].unique()[:10])

        # Try multiple ways to find the TOTAL row
        total_row = None

        # Method 1: Look for exact "TOTAL:" match
        total_mask1 = edited_df_clean['TRANSACTION TYPE'].str.strip().str.upper() == 'TOTAL:'
        if total_mask1.any():
            total_row = edited_df_clean[total_mask1]
            st.success("✅ Found TOTAL row using Method 1")

        # Method 2: Look for rows containing "TOTAL"
        if total_row is None or total_row.empty:
            total_mask2 = edited_df_clean['TRANSACTION TYPE'].str.contains('TOTAL', case=False, na=False)
            if total_mask2.any():
                total_row = edited_df_clean[total_mask2]
                st.success("✅ Found TOTAL row using Method 2")

        # Method 3: Look at the summary rows (rows with category info but no transaction details)
        if total_row is None or total_row.empty:
            # Find rows that have PAID IN or PAID OUT values but no receipt numbers
            summary_mask = (
                                   (edited_df_clean['PAID IN'] > 0) | (edited_df_clean['PAID OUT'] > 0)
                           ) & (
                                   edited_df_clean['Receipt No.'].isna() |
                                   edited_df_clean['Receipt No.'].str.strip().isin(['None', '', 'nan'])
                           )
            summary_rows = edited_df_clean[summary_mask]

            if not summary_rows.empty:
                st.write("**Summary rows found:**")
                st.dataframe(summary_rows[['TRANSACTION TYPE', 'PAID IN', 'PAID OUT']])

                # Get the TOTAL row specifically
                total_candidates = summary_rows[
                    summary_rows['TRANSACTION TYPE'].str.contains('TOTAL', case=False, na=False)]
                if not total_candidates.empty:
                    total_row = total_candidates
                    st.success("✅ Found TOTAL row using Method 3")

        # Extract totals
        if total_row is not None and not total_row.empty:
            total_money_in = float(total_row['PAID IN'].iloc[0])
            total_money_out = float(total_row['PAID OUT'].iloc[0])
            st.info(f"Extracted - PAID IN: {total_money_in:,.2f}, PAID OUT: {total_money_out:,.2f}")
        else:
            # Manual calculation from individual categories
            st.warning("⚠️ TOTAL row not found, calculating from category summary rows")

            # Get all summary rows (category totals)
            category_summary = edited_df_clean[
                (edited_df_clean['Receipt No.'].isna() |
                 edited_df_clean['Receipt No.'].str.strip().isin(['None', '', 'nan'])) &
                (~edited_df_clean['TRANSACTION TYPE'].str.contains('TOTAL', case=False, na=False))
                ]

            total_money_in = category_summary['PAID IN'].sum()
            total_money_out = category_summary['PAID OUT'].sum()

            st.write("**Category breakdown:**")
            for _, row in category_summary.iterrows():
                if row['PAID IN'] > 0 or row['PAID OUT'] > 0:
                    st.write(f"- {row['TRANSACTION TYPE']}: IN={row['PAID IN']:,.2f}, OUT={row['PAID OUT']:,.2f}")

        # Calculate different cashflow metrics
        total_transaction_volume = total_money_in + total_money_out  # Total money moved
        net_cashflow = total_money_in - total_money_out  # Net gain/loss

        # Display the metrics
        cashflow_col1, cashflow_col2 = st.columns(2)
        with cashflow_col1:
            st.metric("Total Money IN", f"KSh {total_money_in:,.2f}")
            st.metric("Total Transaction Volume", f"KSh {total_transaction_volume:,.2f}")
        with cashflow_col2:
            st.metric("Total Money OUT", f"KSh {total_money_out:,.2f}")
            st.metric("Net Cashflow", f"KSh {net_cashflow:,.2f}")

        # Use total transaction volume for scoring (as per your original logic)
        cashflow = total_transaction_volume

        # 2. Weekly Average Balance
        if len(edited_df_clean) > 0 and not edited_df_clean['Date'].isna().all():
            # Set Date as index for resampling
            df_with_date_index = edited_df_clean.set_index('Date')
            try:
                weekly_balances = df_with_date_index['Balance'].resample('W').mean()
                balance_avg = weekly_balances.tail(4).mean()  # Last 4 weeks average
                if pd.isna(balance_avg):
                    balance_avg = edited_df_clean['Balance'].mean()
            except:
                balance_avg = edited_df_clean['Balance'].mean()
        else:
            balance_avg = edited_df_clean['Balance'].mean()

        # 3. Days Since Last Transaction
        try:
            last_transaction_date = edited_df_clean['Date'].max()
            days_since_last = (datetime.now() - last_transaction_date).days
        except:
            days_since_last = 0

        # 4. PayBill Value (P2P transactions)
        paybill_transactions = edited_df_clean[edited_df_clean['Category'] == 'PayBill']
        p2p_value = paybill_transactions['Amount'].sum()

        # Display Raw MPESA Metrics
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Cashflow", f"KSh {cashflow:,.0f}")
            st.metric("Average Weekly Balance", f"KSh {balance_avg:,.0f}")

        with col2:
            st.metric("Days Since Last Transaction", f"{days_since_last} days")
            st.metric("Total PayBill Transactions", f"KSh {p2p_value:,.0f}")

        # Convert to Scores (using your original scoring logic)
        st.subheader("🎯 MPESA Score Calculations")

        # Cashflow Score
        if cashflow <= 100_000:
            cashflow_score = 5
        elif cashflow <= 200_000:
            cashflow_score = 10
        else:
            cashflow_score = 16

        # Balance Score
        if balance_avg <= 2000:
            balance_score = 4
        elif balance_avg <= 5000:
            balance_score = 8
        else:
            balance_score = 16

        # Recency Score
        if days_since_last <= 6:
            recent_score = 4
        elif days_since_last <= 13:
            recent_score = 2
        else:
            recent_score = 0

        # P2P Score
        if p2p_value <= 50000:
            p2p_score = 1
        elif p2p_value <= 150000:
            p2p_score = 2.5
        else:
            p2p_score = 4

        # Display Scores
        score_col1, score_col2 = st.columns(2)

        with score_col1:
            st.info(f"Cashflow Score: **{cashflow_score}/16**")
            st.info(f"Balance Score: **{balance_score}/16**")

        with score_col2:
            st.info(f"Recency Score: **{recent_score}/4**")
            st.info(f"P2P Score: **{p2p_score}/4**")

        # Calculate Auto Score (combining original and new metrics)
        income_total = edited_df_clean[edited_df_clean["Category"] == "Income"]["PAID IN"].sum()
        expense_total = edited_df_clean[edited_df_clean["Category"] == "Expense"]["PAID OUT"].sum()

        if expense_total > 0:
            ratio = income_total / expense_total
            basic_auto_score = min(10, ratio * 2)
        else:
            basic_auto_score = 5

        # Enhanced Auto Score (incorporating MPESA metrics)
        mpesa_total_score = cashflow_score + balance_score + recent_score + p2p_score
        mpesa_max_score = 16 + 16 + 4 + 4  # 40
        mpesa_normalized_score = (mpesa_total_score / mpesa_max_score) * 10

        enhanced_auto_score = (basic_auto_score + mpesa_normalized_score) / 2

        st.info(f"Basic Auto Score: **{basic_auto_score:.2f}/10**")
        st.info(f"MPESA Enhanced Score: **{mpesa_normalized_score:.2f}/10**")
        st.success(f"Enhanced Auto Score: **{enhanced_auto_score:.2f}/10**")

        # Final Score
        final_score = (manual_score + enhanced_auto_score) / 2
        st.subheader(f"🏁 Final Score: **{final_score:.2f}/10**")

        # Risk Classification
        if final_score >= 7.5:
            risk_level = "Low Risk"
            risk_color = "success"
        elif final_score >= 5.0:
            risk_level = "Moderate Risk"
            risk_color = "warning"
        else:
            risk_level = "High Risk"
            risk_color = "error"

        if risk_color == "success":
            st.success(f"Risk Classification: **{risk_level}**")
        elif risk_color == "warning":
            st.warning(f"Risk Classification: **{risk_level}**")
        else:
            st.error(f"Risk Classification: **{risk_level}**")

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

        # Enhanced Financial Summary Table
        st.markdown("### Financial Summary")
        financial_summary = []
        for category in edited_df_clean["Category"].unique():
            category_data = edited_df_clean[edited_df_clean["Category"] == category]
            paid_in = category_data["PAID IN"].sum()
            paid_out = category_data["PAID OUT"].sum()
            net_amount = paid_in - paid_out
            transaction_count = len(category_data)

            financial_summary.append({
                "Category": category,
                "Count": transaction_count,
                "Total Paid In": f"KSh {paid_in:,.2f}",
                "Total Paid Out": f"KSh {paid_out:,.2f}",
                "Net Amount": f"KSh {net_amount:,.2f}"
            })

        financial_df = pd.DataFrame(financial_summary)
        st.dataframe(financial_df, use_container_width=True)

        # MPESA Metrics Summary Table
        st.markdown("### MPESA Metrics Summary")
        metrics_summary = {
            "Metric": [
                "Total Cashflow (IN + OUT)",
                "Average Weekly Balance (Last 4 weeks)",
                "Days Since Last Transaction",
                "Total PayBill Transactions",
                "Income to Expense Ratio"
            ],
            "Value": [
                f"KSh {cashflow:,.0f}",
                f"KSh {balance_avg:,.0f}",
                f"{days_since_last} days",
                f"KSh {p2p_value:,.0f}",
                f"{ratio:.2f}" if expense_total > 0 else "N/A"
            ],
            "Score": [
                f"{cashflow_score}/16",
                f"{balance_score}/16",
                f"{recent_score}/4",
                f"{p2p_score}/4",
                f"{basic_auto_score:.1f}/10"
            ]
        }
        metrics_df = pd.DataFrame(metrics_summary)
        st.dataframe(metrics_df, use_container_width=True)

        # Download
        st.markdown("### ⬇️ Download Classified Data")
        csv_buffer = io.StringIO()
        edited_df_clean.to_csv(csv_buffer, index=False)
        b64 = base64.b64encode(csv_buffer.getvalue().encode()).decode()
        st.markdown(
            f'<a href="data:file/csv;base64,{b64}" download="classified_transactions.csv">Download CSV File</a>',
            unsafe_allow_html=True)

else:
    st.info("Please upload an MPESA PDF statement to get started.")
