import pandas as pd
import re
from datetime import datetime

def classify_transactions(excel_file_path: str) -> pd.DataFrame:
    """
    Cleans and classifies transactions from extracted MPESA Excel data.

    Args:
        excel_file_path (str): Path to the extracted Excel file with raw text in column A.

    Returns:
        pd.DataFrame: Cleaned DataFrame with columns:
                      ['Completion Time', 'Description', 'PAID IN', 'WITHDRAWN', 'BALANCE']
    """
    # Step 1: Load raw lines
    df_raw = pd.read_excel(excel_file_path, header=None, names=['Raw'])

    transactions = []

    # Step 2: Loop through lines and parse valid transaction entries
    for line in df_raw['Raw'].astype(str):
        match = re.search(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.*?)\s+Completed\s+(-?\d+\.\d+)\s+(\d+\.\d+)?',
            line
        )
        if match:
            date_str, desc, amount_str, balance_str = match.groups()
            date = pd.to_datetime(date_str)
            amount = float(amount_str)
            balance = float(balance_str) if balance_str else None

            transactions.append({
                'Completion Time': date,
                'Description': desc.strip(),
                'PAID IN': amount if amount > 0 else 0,
                'WITHDRAWN': abs(amount) if amount < 0 else 0,
                'BALANCE': balance
            })

    # Step 3: Validate results
    if not transactions:
        raise ValueError("❌ No valid transaction lines found in the Excel file.")

    # Step 4: Return cleaned DataFrame
    df_clean = pd.DataFrame(transactions)
    return df_clean
