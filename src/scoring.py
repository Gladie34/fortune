def score_customer(metrics: dict) -> dict:
    score = 0

    # Business Profile
    score += metrics['business_age_score']  # out of 5
    score += metrics['avg_stock_score']     # out of 10

    # Neighbor Referrals
    score += (metrics['neighbor_ability'] / 10) * 10
    score += (metrics['neighbor_willingness'] / 10) * 10
    score += metrics['neighbor_familiarity']

    # Loan Officer
    score += (metrics['officer_ability'] / 10) * 10
    score += (metrics['officer_willingness'] / 10) * 10

    # MPESA Statement
    score += metrics['mpesa_cashflow']
    score += metrics['mpesa_balance_avg']
    score += metrics['mpesa_recent_days']


    decision = "Approved (KES 5000)" if score >=50 else "Denied (KES 0)"

    return {"score": round(score, 2), "decision": decision}