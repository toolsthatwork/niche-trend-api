"""
Mortgage & Loan Calculator API
Fully offline math
"""
from fastapi import APIRouter, HTTPException, Query
import math

router = APIRouter(prefix="/mortgage", tags=["Mortgage Calculator"])

@router.get("/", summary="API Info")
def mortgage_info():
    return {
        "name": "Mortgage and Loan Calculator API",
        "version": "1.0.0",
        "endpoints": ["/mortgage/calculate", "/mortgage/amortization", "/mortgage/affordability", "/mortgage/compare"],
        "powered_by": "Tools That Work"
    }

@router.get("/calculate", summary="Calculate monthly mortgage payment")
def calculate(
    principal: float = Query(..., gt=0, description="Loan amount"),
    annual_rate: float = Query(..., ge=0, le=100, description="Annual interest rate (%)"),
    years: int = Query(..., ge=1, le=50, description="Loan term in years"),
    down_payment: float = Query(0, ge=0, description="Down payment amount"),
):
    loan = principal - down_payment
    if loan <= 0:
        raise HTTPException(status_code=400, detail="Down payment must be less than principal")
    monthly_rate = annual_rate / 100 / 12
    n = years * 12

    if monthly_rate == 0:
        monthly_payment = loan / n
    else:
        monthly_payment = loan * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)

    total_payment = monthly_payment * n
    total_interest = total_payment - loan

    return {
        "principal": principal,
        "down_payment": down_payment,
        "loan_amount": round(loan, 2),
        "annual_rate_pct": annual_rate,
        "term_years": years,
        "term_months": n,
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "interest_ratio_pct": round(total_interest / total_payment * 100, 1),
    }

@router.get("/amortization", summary="Get full amortization schedule")
def amortization(
    principal: float = Query(..., gt=0),
    annual_rate: float = Query(..., ge=0, le=100),
    years: int = Query(..., ge=1, le=50),
    show_months: bool = Query(False, description="Show monthly detail (default: yearly summary)")
):
    loan = principal
    monthly_rate = annual_rate / 100 / 12
    n = years * 12
    if monthly_rate == 0:
        monthly_payment = loan / n
    else:
        monthly_payment = loan * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)

    balance = loan
    schedule = []
    year_interest = 0
    year_principal = 0

    for month in range(1, n + 1):
        interest = balance * monthly_rate
        principal_paid = monthly_payment - interest
        balance -= principal_paid
        year_interest += interest
        year_principal += principal_paid

        if show_months:
            schedule.append({
                "month": month,
                "payment": round(monthly_payment, 2),
                "principal": round(principal_paid, 2),
                "interest": round(interest, 2),
                "balance": round(max(balance, 0), 2),
            })
        elif month % 12 == 0:
            schedule.append({
                "year": month // 12,
                "annual_payment": round(monthly_payment * 12, 2),
                "principal_paid": round(year_principal, 2),
                "interest_paid": round(year_interest, 2),
                "balance": round(max(balance, 0), 2),
            })
            year_interest = year_principal = 0

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(monthly_payment * n, 2),
        "total_interest": round(monthly_payment * n - principal, 2),
        "schedule": schedule
    }

@router.get("/affordability", summary="How much can you afford?")
def affordability(
    monthly_income: float = Query(..., gt=0, description="Gross monthly income"),
    annual_rate: float = Query(..., ge=0, le=100),
    years: int = Query(30, ge=1, le=50),
    monthly_debts: float = Query(0, ge=0, description="Existing monthly debt payments"),
    dti_limit: float = Query(43, ge=20, le=60, description="Debt-to-income ratio limit % (default 43%)"),
):
    max_monthly_payment = (monthly_income * dti_limit / 100) - monthly_debts
    if max_monthly_payment <= 0:
        raise HTTPException(status_code=400, detail="Existing debts exceed DTI limit")
    monthly_rate = annual_rate / 100 / 12
    n = years * 12
    if monthly_rate == 0:
        max_loan = max_monthly_payment * n
    else:
        max_loan = max_monthly_payment * ((1 + monthly_rate)**n - 1) / (monthly_rate * (1 + monthly_rate)**n)
    return {
        "monthly_income": monthly_income,
        "max_monthly_payment": round(max_monthly_payment, 2),
        "max_loan_amount": round(max_loan, 2),
        "annual_rate_pct": annual_rate,
        "term_years": years,
        "dti_limit_pct": dti_limit,
    }
