import csv
import random
import os

# Set seed for reproducibility
random.seed(42)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "indian_bank_profiles.csv")
NUM_PROFILES = 10000

SEGMENTS = ["Student", "Jan Dhan", "Salaried", "MSME", "HNI"]
SEGMENT_WEIGHTS = [0.15, 0.25, 0.40, 0.15, 0.05]

# Mappings for categorical features
MARITAL_STATUS = ["single", "married", "divorced"]
EDUCATION = ["primary", "secondary", "tertiary", "unknown"]
CONTACT = ["cellular", "telephone", "unknown"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
POUTCOME = ["unknown", "other", "failure", "success"]

def generate_profile(row_id):
    segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
    
    # Defaults and segment-specific generation
    age = 30
    job = "unknown"
    balance = 0.0
    credit_card_count = 0
    avg_monthly_balance = 0.0
    loan_interest_rate = 0.0
    upi_frequency_drop = 0.0
    app_login_decay = 0.0
    default = "no"
    housing = "no"
    loan = "no"

    if segment == "Student":
        age = random.randint(18, 25)
        job = "student"
        balance = round(random.uniform(100, 5000), 2)
        credit_card_count = random.choices([0, 1], weights=[0.9, 0.1])[0]
        avg_monthly_balance = round(random.uniform(500, 2000), 2)
        app_login_decay = round(random.uniform(0.3, 0.9), 2)  # High decay
        upi_frequency_drop = round(random.uniform(0.2, 0.8), 2) # High drop
        housing = "no"
        loan = random.choices(["no", "yes"], weights=[0.8, 0.2])[0] # Education loan

    elif segment == "Jan Dhan":
        age = random.randint(18, 65)
        job = random.choice(["blue-collar", "unemployed", "housemaid", "services"])
        balance = round(random.uniform(0, 10000), 2)
        credit_card_count = 0
        avg_monthly_balance = round(random.uniform(0, 5000), 2)
        app_login_decay = round(random.uniform(0.0, 0.3), 2) # Low app usage
        upi_frequency_drop = round(random.uniform(0.4, 0.9), 2) # Heavy UPI users, prone to drop
        housing = random.choices(["no", "yes"], weights=[0.9, 0.1])[0]
        loan = "no"

    elif segment == "Salaried":
        age = random.randint(22, 60)
        job = random.choice(["admin.", "management", "technician"])
        balance = round(random.uniform(10000, 500000), 2)
        credit_card_count = random.randint(0, 3)
        avg_monthly_balance = round(random.uniform(15000, 100000), 2)
        app_login_decay = round(random.uniform(0.0, 0.5), 2)
        upi_frequency_drop = round(random.uniform(0.0, 0.4), 2)
        housing = random.choices(["no", "yes"], weights=[0.4, 0.6])[0]
        loan = random.choices(["no", "yes"], weights=[0.6, 0.4])[0]

    elif segment == "MSME":
        age = random.randint(25, 65)
        job = "entrepreneur"
        balance = round(random.uniform(50000, 2000000), 2)
        credit_card_count = random.randint(1, 5)
        avg_monthly_balance = round(random.uniform(50000, 500000), 2)
        loan_interest_rate = round(random.uniform(8.0, 14.0), 2)
        app_login_decay = round(random.uniform(0.1, 0.6), 2)
        upi_frequency_drop = round(random.uniform(0.1, 0.7), 2)
        housing = random.choices(["no", "yes"], weights=[0.3, 0.7])[0]
        loan = random.choices(["no", "yes"], weights=[0.2, 0.8])[0]

    elif segment == "HNI":
        age = random.randint(35, 75)
        job = random.choice(["management", "self-employed", "retired"])
        balance = round(random.uniform(2000000, 50000000), 2)
        credit_card_count = random.randint(2, 10)
        avg_monthly_balance = round(random.uniform(1000000, 10000000), 2)
        app_login_decay = round(random.uniform(0.0, 0.2), 2) # RM handled, low decay importance
        upi_frequency_drop = round(random.uniform(0.0, 0.2), 2)
        housing = random.choices(["no", "yes"], weights=[0.5, 0.5])[0]
        loan = random.choices(["no", "yes"], weights=[0.7, 0.3])[0]
        
    marital = random.choice(MARITAL_STATUS)
    education = random.choice(EDUCATION)
    contact = random.choices(CONTACT, weights=[0.6, 0.1, 0.3])[0]
    day = random.randint(1, 31)
    month = random.choice(MONTHS)
    duration = random.randint(10, 3000)
    campaign = random.randint(1, 10)
    pdays = random.choice([-1, random.randint(1, 300)])
    previous = random.randint(0, 5) if pdays != -1 else 0
    poutcome = random.choice(POUTCOME) if previous > 0 else "unknown"
    
    # Additional features
    job_change = random.choices([0, 1], weights=[0.9, 0.1])[0]
    relocation = random.choices([0, 1], weights=[0.95, 0.05])[0]
    competitor_pricing_gap = round(random.uniform(-2.0, +1.0), 2)
    
    # Churn proxy
    churn_risk = 0.0
    if job_change == 1: churn_risk += 0.2
    if relocation == 1: churn_risk += 0.3
    if competitor_pricing_gap < -1.0: churn_risk += 0.2
    if upi_frequency_drop > 0.4: churn_risk += 0.2
    if app_login_decay > 0.5: churn_risk += 0.2
    if balance < 1000: churn_risk += 0.1
    if segment == "HNI": churn_risk -= 0.3 # HNIs less likely to churn suddenly
    
    prob_churn = min(0.95, max(0.05, 0.3 + churn_risk))
    deposit = "no" if random.random() < prob_churn else "yes"
    
    return {
        "age": age,
        "job": job,
        "marital": marital,
        "education": education,
        "default": default,
        "balance": balance,
        "housing": housing,
        "loan": loan,
        "contact": contact,
        "day": day,
        "month": month,
        "duration": duration,
        "campaign": campaign,
        "pdays": pdays,
        "previous": previous,
        "poutcome": poutcome,
        "deposit": deposit,
        "segment": segment,
        "job_change": job_change,
        "relocation": relocation,
        "competitor_pricing_gap": competitor_pricing_gap,
        "upi_frequency_drop": upi_frequency_drop,
        "app_login_decay": app_login_decay,
        "credit_card_count": credit_card_count,
        "avg_monthly_balance": avg_monthly_balance,
        "loan_interest_rate": loan_interest_rate
    }

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    fieldnames = [
        "age", "job", "marital", "education", "default", "balance", 
        "housing", "loan", "contact", "day", "month", "duration", 
        "campaign", "pdays", "previous", "poutcome", "deposit",
        "segment", "job_change", "relocation", "competitor_pricing_gap", 
        "upi_frequency_drop", "app_login_decay", "credit_card_count",
        "avg_monthly_balance", "loan_interest_rate"
    ]
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(NUM_PROFILES):
            writer.writerow(generate_profile(i))
            
    print(f"Generated {NUM_PROFILES} profiles at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
