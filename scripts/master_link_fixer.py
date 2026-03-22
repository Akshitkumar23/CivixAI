import pandas as pd
import numpy as np
from pathlib import Path

MASTER_PATH = Path(r'data/master/schemes_master.csv')

def master_link_fixer():
    df = pd.read_csv(MASTER_PATH, dtype=str)
    count_app = 0
    count_src = 0
    
    # Generic or useless URLs that need replacement
    generic_domains = [
        "dbtbharat.gov.in", "india.gov.in/my-government/schemes", 
        "nan", "", "http://nan", "pmjay.gov.in", "sbi.co.in", 
        "myscheme.gov.in/search", "dge.gov.in", "mahaschemes.maharashtra.gov.in"
    ]
    
    # Define exact matching rules based on keywords
    RULES = [
        # EDUCATION / SCHOLARSHIPS
        {
            "keywords": ["scholarship", "fellowship", "education", "student"],
            "category": "education",
            "app_url": "https://scholarships.gov.in/",
            "src_url": "https://scholarships.gov.in/public/schemeGuidelines"
        },
        # EDUCATION LOANS
        {
            "keywords": ["education loan", "student loan", "study loan"],
            "category": "education",
            "app_url": "https://www.vidyalakshmi.co.in/Students/",
            "src_url": "https://www.vidyalakshmi.co.in/Students/"
        },
        # AGRICULTURE
        {
            "keywords": ["kisan", "krishi", "agriculture", "farmer", "fasal", "pradhan mantri kisan"],
            "category": "agriculture",
            "app_url": "https://pmkisan.gov.in/",
            "src_url": "https://agricoop.gov.in/"
        },
        # HOUSING
        {
            "keywords": ["awas", "housing", "awass", "pmay"],
            "category": "housing",
            "app_url": "https://pmaymis.gov.in/",
            "src_url": "https://pmaymis.gov.in/"
        },
        # BUSINESS / MSME LOANS
        {
            "keywords": ["mudra", "msme", "credit", "business loan", "startup", "stand-up", "stand up", "standup"],
            "category": "business",
            "app_url": "https://www.jansamarth.in/apply-loan",
            "src_url": "https://www.jansamarth.in/home"
        },
        {
            "keywords": ["pmegp"],
            "category": "business",
            "app_url": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
            "src_url": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp"
        },
        # HEALTH / AYUSHMAN
        {
            "keywords": ["ayushman", "pmjay", "health", "chikitsa", "medical"],
            "category": "health",
            "app_url": "https://beneficiary.nha.gov.in/",
            "src_url": "https://nha.gov.in/PM-JAY"
        },
        # INSURANCE
        {
            "keywords": ["bima", "insurance", "suraksha", "jeevan jyoti"],
            "category": "insurance",
            "app_url": "https://nationalinsurance.nic.co.in/",
            "src_url": "https://financialservices.gov.in/"
        },
        # PENSION / PROVIDENT
        {
            "keywords": ["pension", "provident", "ppf", "nps", "vayandana", "vayo", "sr citizen"],
            "category": "pension",
            "app_url": "https://enps.nsdl.com/eNPS/NationalPensionSystem.html",
            "src_url": "https://enps.nsdl.com/"
        },
        # WOMEN / GIRL CHILD
        {
            "keywords": ["sukanya", "samriddhi", "girl child", "mahila", "beti"],
            "category": "women",
            "app_url": "https://www.indiapost.gov.in/",
            "src_url": "https://wcd.nic.in/"
        },
        # EMPLOYMENT / SKILLING
        {
            "keywords": ["employment", "skill", "kaushal", "rozgar", "shramik"],
            "category": "employment",
            "app_url": "https://www.skillindiadigital.gov.in/",
            "src_url": "https://msde.gov.in/"
        }
    ]

    def is_generic(url):
        url_str = str(url).lower()
        if pd.isna(url) or url_str == "" or url_str == "nan": return True
        return any(g in url_str for g in generic_domains)

    for idx, row in df.iterrows():
        name = str(row['scheme_name']).lower()
        category = str(row['scheme_category']).lower()
        app_url = str(row['application_url'])
        src_url = str(row['source_url'])
        
        target_app = app_url
        target_src = src_url
        
        # Determine the best match rule
        matched_rule = None
        for rule in RULES:
            if any(k in name for k in rule['keywords']) or rule['category'] == category:
                matched_rule = rule
                break
                
        if matched_rule:
            if is_generic(app_url) or ('404' in app_url):
                target_app = matched_rule['app_url']
            if is_generic(src_url) or ('404' in src_url) or ('india.gov.in' in src_url):
                target_src = matched_rule['src_url']
        else:
            # Absolute fallback if no rule matches and it's completely dead
            if is_generic(app_url):
                target_app = "https://www.myscheme.gov.in/"
            if is_generic(src_url):
                target_src = "https://www.myscheme.gov.in/"
                
        if target_app != app_url:
            df.at[idx, 'application_url'] = target_app
            count_app += 1
            
        if target_src != src_url:
            df.at[idx, 'source_url'] = target_src
            count_src += 1

    df.to_csv(MASTER_PATH, index=False, encoding='utf-8')
    print(f"✅ Repaired {count_app} Application URLs and {count_src} Source URLs with targeted official portals.")

if __name__ == "__main__":
    master_link_fixer()
