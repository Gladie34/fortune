# mpesa_extractor.py
import tabula
import pandas as pd

def parse_mpesa_pdf(pdf_path, password=None):
    try:
        # Extract tables from the MPESA PDF using Tabula
        tables = tabula.read_pdf(
            pdf_path,
            pages='all',
            password=password,
            multiple_tables=True,
            pandas_options={'header': None}
        )

        if not tables or len(tables) == 0:
            return None

        # Combine all tables into a single DataFrame
        combined_df = pd.concat(tables, ignore_index=True)

        # Define standard column names expected for proper processing
        expected_columns = [
            "TransactionDate",
            "TransactionTime",
            "Description",
            "TransactionID",
            "Amount",
            "Balance"
        ]

        # Try setting column headers directly if columns match expected length
        if combined_df.shape[1] == len(expected_columns):
            combined_df.columns = expected_columns
        else:
            # Attempt to detect a header row if structure doesn't match
            for i, row in combined_df.iterrows():
                if all(isinstance(val, str) for val in row):
                    try:
                        combined_df.columns = row
                        combined_df = combined_df.iloc[i + 1:].reset_index(drop=True)
                        break
                    except Exception:
                        continue

        # Clean column names by stripping whitespace and normalizing
        cleaned_columns = []
        for col in combined_df.columns:
            if isinstance(col, str):
                cleaned_columns.append(col.strip().replace(" ", "").replace("\n", ""))
            else:
                cleaned_columns.append(str(col))
        combined_df.columns = cleaned_columns

        # Map various possible column names to readable, consistent names
        column_mapping = {
            "Date": "TransactionDate",
            "Time": "TransactionTime",
            "Details": "Description",
            "TransactionDetails": "Description",
            "Narration": "Description",
            "TransactionID": "TransactionID",
            "Receipt": "TransactionID",
            "PaidInorWithdrawan": "Amount",
            "Amount": "Amount",
            "TransAmount": "Amount",
            "Debit": "Amount",
            "Credit": "Amount",
            "Balance": "Balance"
        }

        # Only keep and rename columns that exist in the extracted DataFrame
        present_columns = [col for col in column_mapping if col in combined_df.columns]
        cleaned_df = combined_df[present_columns].copy()
        cleaned_df.rename(columns={col: column_mapping[col] for col in present_columns}, inplace=True)

        # Ensure numeric values are properly typed for Amount and Balance
        for col in ["Amount", "Balance"]:
            if col in cleaned_df.columns:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')

        return cleaned_df

    except Exception as e:
        print(f"Error parsing MPESA PDF: {e}")
        return None
