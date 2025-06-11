def score_customer(metrics: dict) -> dict:
    """
    Computes a credit score and decision based on business, referral, officer, and MPESA metrics.
    P2P component is removed.

    Args:
        metrics (dict): Dictionary containing:
            - business_age_score (0–5)
            - avg_stock_score (0–10)
            - neighbor_ability (0–10)
            - neighbor_willingness (0–10)
            - neighbor_familiarity (0–5)
            - officer_ability (0–10)
            - officer_willingness (0–10)
            - mpesa_cashflow (0–16)
            - mpesa_balance_avg (0–16)
            - mpesa_recent_days (0–4)

    Returns:
        dict: { 'score': float, 'decision': str }
    """
    score = 0

    # Business Profile (Max 15)
    score += metrics.get('business_age_score', 0)
    score += metrics.get('avg_stock_score', 0)

    # Neighbor Referrals (Max 25)
    score += (metrics.get('neighbor_ability', 0) / 10) * 10
    score += (metrics.get('neighbor_willingness', 0) / 10) * 10
    score += metrics.get('neighbor_familiarity', 0)

    # Loan Officer Review (Max 20)
    score += (metrics.get('officer_ability', 0) / 10) * 10
    score += (metrics.get('officer_willingness', 0) / 10) * 10

    # MPESA Statement (Max 36)
    score += metrics.get('mpesa_cashflow', 0)
    score += metrics.get('mpesa_balance_avg', 0)
    score += metrics.get('mpesa_recent_days', 0)

    # Final decision
    decision = "Approved (KES 5000)" if score >= 50 else "Denied (KES 0)"

    return {
        "score": round(score, 2),
        "decision": decision
    }
