

### 🧾 1. **Project Title**

* A concise name like:
  `Mama_mboga scoring

---

### 📄 2. **Project Overview**



> This app extracts MPESA statements from PDFs, analyzes financial activity, combines it with business and social profile data, and produces a credit score to determine microloan eligibility.

---

### 🧠 3. **Key Features**

List out what the tool can do:

* Extract encrypted MPESA PDFs
* Parse and classify transactions
* Calculate metrics: cashflow, balance, activity
* Accept manual inputs (business profile, referrals)
* Generate a credit score
* Make loan decisions (Approved or Denied)

---

### 🗂️ 4. **Project Structure**

Example:

```bash
src/
├── extraction.py       # Extracts text from PDF to Excel
├── classification.py   # Parses MPESA transactions
├── scoring.py          # Computes final weighted credit score
streamlit_app.py        # User interface
requirements.txt        # Dependencies
README.md               # This file
```

---

### ⚙️ 5. **How to Run It**

setup and execution steps:

```bash
# 1. Clone project
git clone //github.com/Gladie34/mama_mboga_scoring.git
cd credit-scoring

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Streamlit app
streamlit run streamlit_app.py
```

---

### 🧮 6. **Scoring Criteria**

Summarize the score components:

| Category            | Weight |
| ------------------- | ------ |
| Business Profile    | 15%    |
| Neighbour Referrals | 25%    |
| Loan Officer Review | 20%    |
| MPESA Statement     | 40%    |

Decision: Score ≥ 60 → **Approved** (Ksh 5,000), else → **Denied** (Ksh 0)

---

### 📥 7. **Input Requirements**

* Encrypted MPESA PDF (with password)
* Business start date
* Daily stock value
* Neighbour and loan officer ratings (1–10)

---

### 📤 8. **Output**

* Excel file with parsed transactions
* Financial metrics (cashflow, balance, etc.)
* A detailed score breakdown
* Final credit decision

---

### 🧾 9. **Dependencies**

Add this if you're using `requirements.txt`:

```
streamlit
PyPDF2
pandas
openpyxl
```
