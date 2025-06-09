import pandas as pd
from datetime import datetime, timedelta
import re

def classify_transactions(excel_file):
    df = pd.read_excel(excel_file, header=None)
    today = datetime.today()

    detailed_rows = df[df[0].astype(str).str.match(r"^TF|^07|^\d{2}/\d{2}/\d{4}", na=False)].copy()
    detailed_rows.columns = ["Raw"]

    records = []
    for line in detailed_rows["Raw"]:
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+?)Completed ([-\d.]+) (\d+\.\d+)?$', line)
        if match:
            time_str = match.group(1)
            desc = match.group(2).strip()
            amount = float(match.group(3))
            balance = float(match.group(4)) if match.group(4) else None
            records.append({
                "Date": pd.to_datetime(time_str),
                "Description": desc,
                "Amount": amount,
                "Balance": balance
            })

    parsed_df = pd.DataFrame(records)
    return parsed_df, df  # ✅ MUST return a tuple
