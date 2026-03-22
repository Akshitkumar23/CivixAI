import pandas as pd
from pathlib import Path

MASTER_PATH = Path(r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv')

def fix_broken_financial_links():
    if not MASTER_PATH.exists():
        print("CSV not found.")
        return

    df = pd.read_csv(MASTER_PATH, dtype=str)
    count = 0

    # Specifically fix SBI Education Loan
    sbi_mask = df['scheme_id'] == 'sbi_education_loan_v2'
    if sbi_mask.any():
        print("Fixing SBI Education Loan...")
        # Direct apply link -> Vidya Lakshmi Portal (standard for govt banking edu loans)
        # OR SBI's direct retail landing page
        df.loc[sbi_mask, 'application_url'] = "https://www.vidyalakshmi.co.in/Students/"
        df.loc[sbi_mask, 'source_url'] = "https://sbi.co.in/web/personal-banking/loans/education-loans/student-loan-scheme"
        count += 1
        
    sbi_another = df['scheme_id'] == 'sbi_education_loan'
    if sbi_another.any():
        df.loc[sbi_another, 'application_url'] = "https://www.vidyalakshmi.co.in/Students/"
        df.loc[sbi_another, 'source_url'] = "https://sbi.co.in/web/personal-banking/loans/education-loans/student-loan-scheme"
        count += 1

    for idx, row in df.iterrows():
        app_url = str(row['application_url'])
        src_url = str(row['source_url'])
        
        # Generic SBI fixes
        if 'sbi.co.in' in src_url and 'student' in src_url and '404' not in src_url:
            if src_url == 'https://sbi.co.in/web/student-loans' or src_url == 'https://sbi.co.in/web/student-loans/':
                df.at[idx, 'source_url'] = "https://sbi.co.in/web/personal-banking/loans/education-loans/student-loan-scheme"
                count += 1
        if 'sbi.co.in' in app_url and len(app_url) < 25:
            if 'education' in str(row['scheme_category']).lower() or 'education' in str(row['scheme_name']).lower():
                df.at[idx, 'application_url'] = "https://www.vidyalakshmi.co.in/Students/"
                count += 1
                
        # Fix HDFC/Credila
        if 'hdfccredila' in src_url or 'hdfccredila' in app_url:
             df.at[idx, 'application_url'] = "https://www.hdfccredila.com/apply-for-education-loan"
             df.at[idx, 'source_url'] = "https://www.hdfccredila.com/"
             count += 1

    df.to_csv(MASTER_PATH, index=False, encoding='utf-8')
    print(f"Fixed {count} specific financial URLs.")

if __name__ == "__main__":
    fix_broken_financial_links()
