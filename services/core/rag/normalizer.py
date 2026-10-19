"""
Multilingual Query Normalizer
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Normalizes queries across English, Devanagari Hindi, and Latin-script Hinglish.
Handles financial numbers, acronyms, and concept mapping for high-precision retrieval.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple


# Devanagari Unicode block
DEVANAGARI_REGEX = re.compile(r'[\u0900-\u097F]')

# Devanagari numerals to ASCII digits
DEVANAGARI_DIGITS_MAP = str.maketrans('०१२३४५६७८९', '0123456789')

# Fractional and multiplier words (Hindi and Romanized Hinglish)
FRACTION_TERMS: Dict[str, float] = {
    "डेढ़": 1.5, "derh": 1.5, "dedh": 1.5, "dhedh": 1.5,
    "ढाई": 2.5, "dhai": 2.5, "dhaai": 2.5,
    "सवा": 1.25, "sawa": 1.25, "savaa": 1.25,
    "पौने": 0.75, "paune": 0.75, "pone": 0.75,
    "आधा": 0.5, "adha": 0.5, "aadha": 0.5
}

HINDI_NUM_WORDS: Dict[str, int] = {
    "एक": 1, "ek": 1, "दो": 2, "do": 2, "तीन": 3, "teen": 3, "tin": 3,
    "चार": 4, "chaar": 4, "char": 4, "पांच": 5, "पाँच": 5, "paanch": 5, "panch": 5,
    "छह": 6, "छः": 6, "chhah": 6, "cheh": 6, "chhe": 6,
    "सात": 7, "saat": 7, "आठ": 8, "aath": 8, "नौ": 9, "nau": 9, "दस": 10, "das": 10,
    "ग्यारह": 11, "gyarah": 11, "बारह": 12, "barah": 12, "तेरह": 13, "terah": 13,
    "चौदह": 14, "chaudah": 14, "पंद्रह": 15, "पन्द्रह": 15, "pandrah": 15, "pandra": 15,
    "सोलह": 16, "solah": 16, "सत्रह": 17, "satrah": 17, "अठारह": 18, "atharah": 18,
    "उन्नीस": 19, "unnees": 19, "बीस": 20, "bees": 20,
    "पच्चीस": 25, "pachees": 25, "pachis": 25, "तीस": 30, "tees": 30,
    "पैंतीस": 35, "paintis": 35, "चालीस": 40, "chalis": 40,
    "पचास": 50, "pachaas": 50, "pachas": 50, "साठ": 60, "saath": 60,
    "सत्तर": 70, "sattar": 70, "अस्सी": 80, "assi": 80, "नब्बे": 90, "nabbe": 90,
    "सौ": 100, "sau": 100
}

# Common Hinglish stopwords and markers
HINGLISH_MARKERS: Set[str] = {
    "kya", "hai", "hain", "milega", "milegi", "milte", "milti", "kitna", "kitni", "kitne", "kaise",
    "hazar", "hazaar", "rupaye", "rupay", "yojana", "yojna", "nahi", "kisko", "kise", "chahiye",
    "patra", "patrata", "yogyata", "dastavez", "dastawez", "aavedan", "avedan", "bhi", "me", "mein", "ko", "se",
    "par", "aur", "hota", "hoti", "wale", "wali", "wala", "ke", "liye", "batao", "bataiye",
    "milenge", "milta", "sakte", "sakti", "loan", "paise", "paisa", "cylinder", "chulha", "chula",
    "karz", "karza", "karigar", "shilpkar", "thela", "thele", "feriwala", "kisan", "kisaan",
    "nidhi", "samman", "byaj", "byaaj", "chhoot", "chhut", "sahayata", "madad"
}

# Financial and numeric terms mapping
NUMERIC_EXPANSIONS: Dict[str, List[str]] = {
    "6000": ["6000", "6,000", "6k", "6 hazar", "६०००"],
    "2000": ["2000", "2,000", "2k", "2 hazar", "२०००"],
    "15000": ["15000", "15,000", "15k", "15 hazar", "१५०००"],
    "25000": ["25000", "25,000", "25k", "25 hazar", "२५०००"],
    "50000": ["50000", "50,000", "50k", "50 hazar", "५००००"],
    "100000": ["100000", "1,00,000", "1 lakh", "1L", "100k"],
    "150000": ["150000", "1,50,000", "1.5 lakh", "1.5 lac", "1.5L", "150k", "derh lakh"],
    "200000": ["200000", "2,00,000", "2 lakh", "2L", "200k"],
    "250000": ["250000", "2,50,000", "2.5 lakh", "2.5 lac", "2.5L", "250k", "dhai lakh"],
    "300000": ["300000", "3,00,000", "3 lakh", "3 lac", "3L"],
    "350000": ["350000", "3,50,000", "3.5 lakh", "3.5 lac", "sadhe 3 lakh"],
    "7%": ["7%", "7 percent", "7 pratishat", "7% interest subsidy"],
    "5%": ["5%", "5 percent", "5 pratishat", "5% concessional interest"],
}

# Scheme acronyms and canonical mappings
SCHEME_KEYWORDS: Dict[str, Tuple[str, str, List[str]]] = {
    "pm_kisan": (
        "dbtbharat_central_schemes_pm_kisan",
        "PM KISAN",
        [
            "pm kisan", "pm-kisan", "pmkisan", "kisan samman nidhi", "किसान सम्मान", "किसान",
            "farmer 6000", "kisan 6000", "kisan 2000", "kisaan 6000", "kisaan 2000",
            # Nicknames & acronyms
            "kisan nidhi", "kisaan nidhi", "kissan nidhi", "kisannidhi",
            "kisan samman", "kisaan samman", "samman nidhi", "sammannidhi",
            "pmksny", "pm-ksny", "pm kisan yojana", "kisan yojana", "kisaan yojana", "kisan yojna",
            "kisan sahayata", "kisan paisa", "kisan scheme",
            # Hindi word order & code-switching
            "nidhi kisan", "samman kisan", "kisan ki nidhi", "kisan ka paisa", "kisan ko 6000",
            # Devanagari Hindi
            "किसान सम्मान निधि", "किसान निधि", "किसान योजना", "पीएम किसान सम्मान निधि", "पीएम किसान"
        ]
    ),
    "pm_svanidhi": (
        "dbtbharat_central_schemes_pm_street_vendor_atmanirbhar_nidhi_pm_svanidhi",
        "PM SVANidhi",
        [
            "svanidhi", "pm svanidhi", "pmsvanidhi", "swanidhi", "pm swanidhi", "pmswanidhi",
            "street vendor", "रेहड़ी पटरी", "स्वनिधि", "vendor loan", "15000 loan", "urban vendor",
            "street vendor loan", "urban street vendor", "svanidhi loan", "swanidhi loan",
            # Nicknames & acronyms
            "rehri patri karz", "rehri patri loan", "rehri patri yojana", "rehri patri yojna",
            "rehdi patri karz", "rehdi patri loan", "rehdi patri yojana", "rehdi patri", "rehri patri",
            "thela wala loan", "thele wale ka loan", "thela loan", "patri vendor", "feriwala loan", "feriwale loan",
            # Hindi word order & code-switching
            "karz rehri patri", "loan rehri patri", "karz rehdi patri", "yojana rehri patri",
            "rehri walon ka karz", "rehri patri ka loan", "vendor svanidhi",
            # Devanagari Hindi
            "रेहड़ी पटरी कर्ज", "रेहड़ी पटरी लोन", "रेहड़ी पटरी योजना", "स्वनिधि योजना", "पीएम स्वनिधि", "रेहड़ी पटरी कर्ज"
        ]
    ),
    "pm_ujjwala": (
        "dbtbharat_central_schemes_pradhan_mantri_ujjwala_yojana",
        "Pradhan Mantri Ujjwala Yojana",
        [
            "ujjwala", "pmuy", "pm ujjwala", "pm-ujjwala", "ujjwala 2.0", "lpg connection", "गैस सिलेंडर",
            "उज्ज्वला", "free gas", "chulha", "first refill",
            # Nicknames & acronyms
            "chulha yojana", "chula yojana", "chulha yojna", "chula yojna",
            "gas chulha", "gas chula", "gas cylinder yojana", "lpg chulha", "free cylinder",
            "deposit-free lpg", "muft gas", "muft cylinder", "free gas cylinder",
            "pmuy 2.0", "pmuy yojana", "ujjwala gas", "ujwala", "ujwla", "ujjawala", "pm ujwala",
            "ujjwala yojana", "ujwala yojana",
            # Hindi word order & code-switching
            "yojana chulha", "gas ka chulha", "chulha gas", "chulha wali yojana", "cylinder ujjwala", "yojana ujjwala",
            # Devanagari Hindi
            "चूल्हा योजना", "गैस चूल्हा योजना", "उज्ज्वला 2.0", "मुफ्त गैस कनेक्शन", "एलपीजी चूल्हा", "उज्ज्वला योजना", "गैस चूल्हा"
        ]
    ),
    "pm_vishwakarma": (
        "dbtbharat_central_schemes_pm_vishwakarma",
        "PM Vishwakarma",
        [
            "vishwakarma", "pm vishwakarma", "pmvishwakarma", "artisan", "traditional craft",
            "विश्वकर्मा", "artisan loan", "18 trades", "toolkit incentive", "stipend 500",
            # Nicknames & acronyms
            "vishwakarma karigar", "vishwakarma karigar yojana", "vishwakarma karigar yojna",
            "vishwakarma shilpkar", "karigar yojana", "karigar loan", "karigar karz", "karigar sahayata",
            "shilpkar yojana", "shilpkar loan", "vishwakarma toolkit", "toolkit yojana",
            "vishwkarma", "vishwakrma", "viswakarma", "pm viswakarma", "pm vishwkarma",
            "vishwakarma scheme", "vishwakarma yojana", "pm vishwakarma yojana",
            # Hindi word order & code-switching
            "karigar vishwakarma", "shilpkar vishwakarma", "loan vishwakarma", "karz vishwakarma",
            "vishwakarma ke karigar", "vishwakarma ka karigar",
            # Devanagari Hindi
            "विश्वकर्मा कारीगर", "विश्वकर्मा कारीगर योजना", "विश्वकर्मा योजना", "कारीगर योजना", "कारीगर लोन",
            "शिल्पकार योजना", "पीएम विश्वकर्मा"
        , "18 पारंपरिक शिल्प", "पारंपरिक शिल्प", "टूलकिट वाउचर", "बढ़ई", "लोहार", "कुम्हार", "दर्जी"]
    ),
    "ayushman_bharat": (
        "dbtbharat_central_schemes_ayushman_bharat_pradhan_mantri_jan_arogya_yojana_ab_pmjay",
        "Ayushman Bharat PM-JAY",
        ["ayushman", "ayushman bharat", "pmjay", "pm-jay", "pm jay", "golden card", "आयुष्मान", "5 lakh health cover", "ayushman card", "5 लाख तक का कैशलेस", "कैशलेस अस्पताल इलाज", "5 lakh hospital", "कैशलेस इलाज", "आयुष्मान भारत"]
    ),
    "pmay_g": (
        "dbtbharat_central_schemes_pradhan_mantri_awas_yojna_grameen",
        "PMAY-Gramin (PMAY-G)",
        ["pmay-g", "pmay gramin", "pmayg", "awas gramin", "आवास ग्रामीण", "pradhan mantri awas yojana gramin", "गांव में पक्का घर", "गांव में मकान", "पक्का मकान", "पक्का घर", "ग्रामीण आवास", "pm awas gramin", "1 lakh 20 thousand", "1.20 lakh"]
    ),
    "pmay_u": (
        "pmay_home_loan",
        "PMAY-Urban (PMAY-U / CLSS)",
        ["pmay-u", "pmay urban", "pmayu", "awas urban", "आवास शहरी", "clss", "pradhan mantri awas yojana urban", "शहर में घर", "होम लोन ब्याज सब्सिडी", "ब्याज सब्सिडी", "शहरी आवास", "credit linked subsidy"]
    ),
    "pm_mudra": (
        "js_mudra_all",
        "Pradhan Mantri Mudra Yojana (PMMY)",
        ["mudra", "pmmy", "mudra loan", "shishu loan", "kishore loan", "tarun loan", "मुद्रा", "मुद्रा योजना", "शिशु लोन", "किशोर लोन", "तरुण लोन"]
    ),
    "atal_pension": (
        "dbtbharat_central_schemes_atal_pension_yojana",
        "Atal Pension Yojana (APY)",
        ["atal pension", "apy", "atal pension yojana", "अटल पेंशन", "अटल पेंशन योजना"]
    ),
    "pm_jjby": (
        "pm_jeevan_jyoti_bima_v2",
        "PM Jeevan Jyoti Bima Yojana (PMJJBY)",
        ["pmjjby", "jeevan jyoti", "jeevan jyoti bima", "jeevan jyoti bima yojana",
         "जीवन ज्योति", "जीवन ज्योति बीमा", "पीएम जीवन ज्योति बीमा", "436 bima",
         "436", "₹436", "436 सालाना प्रीमियम", "436 प्रीमियम", "2 लाख जीवन बीमा", "जीवन बीमा 436"]
    ),
    "pm_sym": (
        "dbtbharat_central_schemes_pradhan_mantri_shram_yogi_maan_dhan_pm_sym",
        "PM Shram Yogi Maan-dhan (PM-SYM)",
        ["pm-sym", "pmsym", "shram yogi", "maan-dhan", "maandhan", "श्रम योगी", "मानधन"]
    ),
    "ignwps": (
        "dbtbharat_central_schemes_indira_gandhi_national_widow_pension_scheme_ignwps",
        "Indira Gandhi National Widow Pension Scheme (IGNWPS)",
        ["ignwps", "widow pension", "vidhwa pension", "विधवा पेंशन"]
    ),
    "ignoaps": (
        "dbtbharat_central_schemes_indira_gandhi_national_old_age_pension_scheme_ignoaps",
        "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
        ["ignoaps", "old age pension", "vridha pension", "वृद्धावस्था पेंशन", "80 वर्ष से अधिक आयु", "वृद्धजन", "वृद्धा पेंशन"]
    ),
    "igndps": (
        "dbtbharat_central_schemes_indira_gandhi_national_disability_pension_scheme_igndps",
        "Indira Gandhi National Disability Pension Scheme (IGNDPS)",
        ["igndps", "disability pension", "divyang pension", "दिव्यांग पेंशन"]
    ),
    "pmvvy": (
        "dbtbharat_central_schemes_pradhan_mantri_vaya_vandana_yojana",
        "Pradhan Mantri Vaya Vandana Yojana (PMVVY)",
        ["pmvvy", "vaya vandana", "वय वंदना"]
    ),
    "eps95": (
        "dbtbharat_central_schemes_employees_pension_scheme_for_epf_members",
        "Employees Pension Scheme 1995 (EPS-95)",
        ["eps 95", "eps-95", "employees pension scheme", "ईपीएस-95"]
    ),
    "nmmss": (
        "dbtbharat_central_schemes_national_means_cum_merit_scholarship_scheme",
        "National Means-cum-Merit Scholarship Scheme (NMMSS)",
        ["nmmss", "means cum merit", "means-cum-merit", "एनएमएमएसएस", "कक्षा 8 परीक्षा पास", "साधन-सह-योग्यता"]
    ),
    "begum_hazrat_mahal": (
        "dbtbharat_central_schemes_begum_hazrat_mahal_national_scholarship_scheme",
        "Begum Hazrat Mahal National Scholarship",
        ["begum hazrat mahal", "hazrat mahal", "bhm scholarship", "बेगम हज़रत महल", "बेगम हज़रत महल छात्रवृत्ति"]
    ),
    "pragati": (
        "dbtbharat_central_schemes_pragati_scholarship_for_girls_in_degree_colleges",
        "Pragati Scholarship for Girls in Degree Colleges",
        ["pragati scholarship", "aicte pragati", "प्रगति छात्रवृत्ति", "छात्रा को डिग्री"]
    ),
    "saksham": (
        "dbtbharat_central_schemes_saksham_scholarship_for_differently_abled_students_of_degree",
        "Saksham Scholarship for Differently Abled Students",
        ["saksham scholarship", "aicte saksham", "सक्षम छात्रवृत्ति", "तकनीकी डिग्री"]
    ),
    "ishan_uday": (
        "dbtbharat_central_schemes_ishan_uday_special_scholarship_scheme_for_north_eastern_regi",
        "Ishan Uday Special Scholarship Scheme for NER",
        ["ishan uday", "ner scholarship", "ईशान उदय"]
    ),
    "pre_matric_minority": (
        "dbtbharat_central_schemes_pre_matric_scholarship_for_minorities",
        "Pre-Matric Scholarship for Minorities",
        ["pre-matric minority", "pre matric minority"]
    ),
    "post_matric_minority": (
        "dbtbharat_central_schemes_post_matric_scholarship_for_minorities",
        "Post-Matric Scholarship for Minorities",
        ["post-matric minority", "post matric minority"]
    ),
    "sbmu_ihhl": (
        "dbtbharat_central_schemes_swachh_bharat_mission_urban",
        "Swachh Bharat Mission Urban (IHHL)",
        ["swachh bharat urban", "sbmu", "ihhl", "shauchalay 12000", "शौचालय", "पारिवारिक शौचालय", "व्यक्तिगत शौचालय", "12,000 की प्रोत्साहन राशि", "12000 की प्रोत्साहन राशि", "latrine", "व्यक्तिगत पारिवारिक शौचालय", "शौचालय बनवाने", "स्वच्छ भारत अर्बन", "स्वच्छ भारत मिशन अर्बन", "स्वच्छ भारत", "स्वच्छ भारत मिशन"]
    ),
    "pmmsy": (
        "dbtbharat_central_schemes_pradhan_mantri_matsya_sampada_yojana",
        "Pradhan Mantri Matsya Sampada Yojana (PMMSY)",
        ["pmmsy", "matsya sampada", "fisheries scheme", "मत्स्य संपदा", "मत्स्य संपदा योजना", "मछली पालन"]
    ),
    "smam": (
        "dbtbharat_central_schemes_sub_mission_on_agriculture_mechanization_central_sector",
        "Sub-Mission on Agricultural Mechanization (SMAM)",
        ["smam", "agricultural mechanization", "farm machinery", "custom hiring centre", "कस्टम हायरिंग", "कृषि यंत्रीकरण", "ट्रैक्टर पर सब्सिडी"]
    ),
    "pm_daksh": (
        "dbtbharat_central_schemes_pm_daksh_scheme",
        "PM-DAKSH Scheme",
        ["pm daksh", "pm-daksh", "पीएम दक्ष", "पीएम दक्ष योजना", "दक्ष योजना"]
    ),
    "ddu_gky": (
        "dbtbharat_central_schemes_deen_dayal_upadhyay_grameen_kaushalya_yojna",
        "Deen Dayal Upadhyay Grameen Kaushalya Yojna (DDU-GKY)",
        ["ddu gky", "ddu-gky", "grameen kaushalya", "दीन दयाल उपाध्याय ग्रामीण कौशल्या योजना", "ग्रामीण कौशल्या"]
    ),
    "post_graduate_single_girl": (
        "dbtbharat_central_schemes_p_g_indira_gandhi_scholarship_for_single_girl_child",
        "PG Indira Gandhi Scholarship for Single Girl Child",
        ["single girl child scholarship", "pg indira gandhi", "एकल बालिका"]
    ),
    "mission_vatsalya": (
        "central_mwcd_mission_vatsalya",
        "Mission Vatsalya",
        ["mission vatsalya", "vatsalya ngo grant", "child care institution grant", "वात्सल्य"]
    ),
    # Institutional gated scheme detection
    "ddrs": (
        "central_depwd_ddrs",
        "Deen Dayal Disabled Rehabilitation Scheme",
        ["ddrs", "deen dayal disabled", "disability ngo grant", "deen dayal divyang", "दीनदयाल"]
    )
}

# Regex patterns for flexible Hindi word order and code-switching detection
SCHEME_REGEXES: List[Tuple[str, re.Pattern]] = [
    ("pm_kisan", re.compile(r'\b(?:kisa?an|kissan)\s+(?:samman\s+)?(?:ki\s+|ka\s+|ke\s+)?(?:nidhi|yojan?a|sahayata)\b', re.IGNORECASE)),
    ("pm_kisan", re.compile(r'\b(?:nidhi|samman)\s+(?:ki\s+|ka\s+|ke\s+)?(?:kisa?an|kissan)\b', re.IGNORECASE)),
    ("pm_ujjwala", re.compile(r'\bchulh?a\s+(?:wali\s+|wala\s+|ka\s+|ki\s+|ke\s+)?(?:yojan?a|scheme)\b', re.IGNORECASE)),
    ("pm_ujjwala", re.compile(r'\b(?:gas|cylinder)\s+(?:ka\s+|ki\s+|ke\s+)?chulh?a\b', re.IGNORECASE)),
    ("pm_ujjwala", re.compile(r'\byojan?a\s+(?:chulh?a|ujj?wala)\b', re.IGNORECASE)),
    ("pm_svanidhi", re.compile(r'\breh[rd]i\s*patri\s*(?:ka\s+|ki\s+|ke\s+|ko\s+)?(?:karz|karza|loan|rin|yojan?a|sahayata)\b', re.IGNORECASE)),
    ("pm_svanidhi", re.compile(r'\b(?:karz|karza|loan)\s+(?:reh[rd]i\s*patri|thele?\s*wale?)\b', re.IGNORECASE)),
    ("pm_svanidhi", re.compile(r'\bthele?\s*wale?\s*(?:ka\s+|ki\s+|ke\s+|ko\s+)?(?:karz|loan)\b', re.IGNORECASE)),
    ("pm_vishwakarma", re.compile(r'\bvishwa?k[a-z]*\s+(?:ke\s+|ka\s+|ki\s+)?(?:karigar|shilpkar|artisan|loan|karz|yojan?a|toolkit)\b', re.IGNORECASE)),
    ("pm_vishwakarma", re.compile(r'\b(?:karigar|shilpkar)\s+(?:ke\s+|ka\s+|ki\s+)?(?:vishwa?k[a-z]*|yojan?a|loan)\b', re.IGNORECASE))
]

# Hinglish to English translation dictionary for key queries
HINGLISH_TRANSLATION_MAP: Dict[str, str] = {
    "paise": "money benefit financial assistance",
    "paisa": "money amount",
    "kitna": "how much amount financial installment benefit",
    "kitne": "how many amount financial installment benefit",
    "kitni": "how much amount installment benefit",
    "milega": "eligible receive get benefit",
    "milegi": "eligible receive get benefit",
    "milte": "given paid released",
    "milenge": "receive disbursed credited",
    "milta": "receive eligible get benefit",
    "milti": "receive eligible get benefit",
    "kaise": "how application process steps",
    "patra": "eligible eligibility criteria qualified",
    "patrata": "eligibility criteria conditions rules",
    "yogyata": "eligibility qualification criteria",
    "dastavez": "documents required paperwork proof",
    "dastawez": "documents required paperwork proof",
    "kagaz": "documents paperwork aadhaar",
    "kaagaz": "documents paperwork aadhaar",
    "aavedan": "apply application registration online",
    "avedan": "apply application registration",
    "byaj": "interest rate subsidy",
    "byaaj": "interest rate subsidy",
    "biyaj": "interest rate subsidy",
    "chhoot": "subsidy concession waiver rebate",
    "chhut": "subsidy concession waiver rebate",
    "nahi": "not excluded exclusion",
    "kisko": "whom beneficiary target eligible",
    "kise": "whom beneficiary target eligible",
    "loan": "credit loan tranche borrowing",
    "karz": "credit loan tranche borrowing",
    "karza": "credit loan tranche borrowing",
    "karigar": "artisan craftsman trade traditional worker",
    "kaareegar": "artisan craftsman trade traditional worker",
    "shilpkar": "artisan craftsman trade traditional worker",
    "chulha": "stove hotplate lpg gas connection cylinder",
    "chula": "stove hotplate lpg gas connection cylinder",
    "kisan": "farmer agricultural landholding cultivable",
    "kisaan": "farmer agricultural landholding cultivable",
    "nidhi": "fund financial assistance honorarium",
    "samman": "honorarium benefit respect",
    "rehri": "street vendor urban vendor",
    "rehdi": "street vendor urban vendor",
    "patri": "street vendor pavement urban",
    "thela": "street vendor urban vendor pushcart",
    "feriwala": "street vendor urban vendor mobile vendor",
    "sahayata": "assistance grant subsidy relief",
    "madad": "assistance grant subsidy relief",
    "aujar": "toolkit equipment tools incentive",
    "aujaar": "toolkit equipment tools incentive",
    "toolkit": "toolkit equipment tools incentive",
    "jankari": "information details guidelines rules",
    "jaankari": "information details guidelines rules",
    "suchna": "information notice guidelines",
    "shart": "condition rule criteria",
    "sharten": "conditions rules criteria",
    "niyam": "rules guidelines criteria",
    "kab": "when timeline date schedule",
    "hazar": "thousand",
    "hazaar": "thousand",
    "lakh": "hundred thousand",
    "yojana": "scheme program policy",
    "yojna": "scheme program policy"
}


class MultilingualQueryNormalizer:
    """
    Normalizes user queries across languages, expands synonyms,
    and extracts candidate schemes and entity filters.
    """

    @classmethod
    def detect_language(cls, query: str) -> str:
        """
        Detects language: 'hi' (Devanagari), 'hi-Latn' (Hinglish), or 'en' (English).
        """
        if DEVANAGARI_REGEX.search(query):
            return "hi"

        lower = query.lower()
        words = set(re.findall(r'\b\w+\b', lower))
        matching_hinglish = words.intersection(HINGLISH_MARKERS)
        if len(matching_hinglish) >= 1:
            return "hi-Latn"

        return "en"

    @classmethod
    def detect_candidate_schemes(cls, query: str) -> List[Tuple[str, str]]:
        """
        Detects explicit or implicit scheme references in the query, handling
        canonical IDs, nicknames, acronyms, code-switching, and Hindi word order variations.
        Returns List of (canonical_scheme_id, canonical_name).
        """
        lower = query.lower()
        candidates = []
        seen_ids = set()

        # 1. Regex patterns for flexible code-switching and Hindi word order
        for scheme_key, pattern in SCHEME_REGEXES:
            if pattern.search(lower):
                scheme_id, name, _ = SCHEME_KEYWORDS[scheme_key]
                if scheme_id not in seen_ids:
                    candidates.append((scheme_id, name))
                    seen_ids.add(scheme_id)

        # 2. Literal alias & nickname checks
        for key, (scheme_id, name, aliases) in SCHEME_KEYWORDS.items():
            if scheme_id in seen_ids:
                continue
            for alias in aliases:
                if alias in lower:
                    candidates.append((scheme_id, name))
                    seen_ids.add(scheme_id)
                    break
        return candidates

    @classmethod
    def normalize_numbers(cls, query: str) -> str:
        """
        Comprehensive Indian number expression parsing.
        Normalizes:
        - "1.5 lakh", "1.5 lac", "डेढ़ लाख", "derh lakh" -> "150000"
        - "6 हजार", "6 hazar" -> "6000"
        - "50 hazar", "50k" -> "50000"
        - "3 lakh" -> "300000"
        - "15k" -> "15000", "25k" -> "25000"
        - "₹50,000", "₹ 50,000", "50,000" -> "50000"
        Converts them cleanly to standard numeric digits without altering legal or numeric meaning.
        """
        text = query

        # 1. Translate Devanagari numerals to ASCII digits
        text = text.translate(DEVANAGARI_DIGITS_MAP)

        # 2. Currency symbol + comma numbers: e.g. ₹50,000 -> 50000, ₹ 50,000 -> 50000, Rs. 50,000 -> 50000
        text = re.sub(
            r'(?:₹|rs\.?|inr)\s*(\d{1,3}(?:,\d{2,3})+|\d+)',
            lambda m: m.group(1).replace(',', ''),
            text,
            flags=re.IGNORECASE
        )

        # 3. Comma-separated numbers without currency symbol: e.g. 50,000 -> 50000, 1,00,000 -> 100000
        text = re.sub(r'\b(\d{1,3}(?:,\d{2,3})+)\b', lambda m: m.group(1).replace(',', ''), text)

        # 4. "साढ़े" / "sadhe" + (number word or digits) + (multiplier)
        def repl_sadhe(m):
            num_str = m.group(1).lower()
            mult_str = m.group(2).lower()
            base_val = HINDI_NUM_WORDS.get(num_str)
            if base_val is None:
                try:
                    base_val = float(num_str)
                except ValueError:
                    return m.group(0)
            total_val = base_val + 0.5
            if mult_str in ["लाख", "lakh", "lakhs", "lac", "lacs", "l"]:
                return str(int(round(total_val * 100000)))
            elif mult_str in ["हजार", "हज़ार", "hazar", "hazaar", "thousand", "thousands", "k"]:
                return str(int(round(total_val * 1000)))
            elif mult_str in ["करोड़", "करोड", "crore", "crores", "cr"]:
                return str(int(round(total_val * 10000000)))
            return m.group(0)

        sadhe_pattern = re.compile(
            r'\b(?:साढ़े|sadhe|saadhe)\s+([a-zA-Z\u0900-\u097F\d]+)\s*(लाख|हजार|हज़ार|करोड़|lakhs?|lacs?|haza?ar|thousands?|crores?|cr|l|k)\b',
            re.IGNORECASE
        )
        text = sadhe_pattern.sub(repl_sadhe, text)

        # 5. Fractional words + Multipliers: "डेढ़ लाख", "derh lakh", "dedh lakh", "ढाई लाख", "dhai lakh", "सवा लाख", "पौने दो लाख"
        def repl_fractional(m):
            frac_word = m.group(1).lower()
            mult_word = m.group(2).lower()
            val = FRACTION_TERMS.get(frac_word)
            if val is None:
                return m.group(0)
            if mult_word in ["लाख", "lakh", "lakhs", "lac", "lacs", "l"]:
                return str(int(round(val * 100000)))
            elif mult_word in ["हजार", "हज़ार", "hazar", "hazaar", "thousand", "thousands", "k"]:
                return str(int(round(val * 1000)))
            elif mult_word in ["करोड़", "करोड", "crore", "crores", "cr"]:
                return str(int(round(val * 10000000)))
            return m.group(0)

        frac_words_re = "|".join(re.escape(w) for w in FRACTION_TERMS.keys())
        frac_pattern = re.compile(
            rf'\b({frac_words_re})\s*(लाख|हजार|हज़ार|करोड़|lakhs?|lacs?|haza?ar|thousands?|crores?|cr|l|k)\b',
            re.IGNORECASE
        )
        text = frac_pattern.sub(repl_fractional, text)

        # 6. Hindi number words + Multipliers: "छह हजार", "दो हजार", "पंद्रह हजार", "पच्चीस हजार", "पचास हजार", "तीन लाख"
        def repl_hindi_words(m):
            w = m.group(1).lower()
            mult = m.group(2).lower()
            val = HINDI_NUM_WORDS.get(w)
            if val is None:
                return m.group(0)
            if mult in ["लाख", "lakh", "lakhs", "lac", "lacs", "l"]:
                return str(int(round(val * 100000)))
            elif mult in ["हजार", "हज़ार", "hazar", "hazaar", "thousand", "thousands", "k"]:
                return str(int(round(val * 1000)))
            elif mult in ["करोड़", "करोड", "crore", "crores", "cr"]:
                return str(int(round(val * 10000000)))
            return m.group(0)

        hindi_words_re = "|".join(re.escape(w) for w in HINDI_NUM_WORDS.keys())
        hindi_num_pattern = re.compile(
            rf'\b({hindi_words_re})\s*(लाख|हजार|हज़ार|करोड़|lakhs?|lacs?|haza?ar|thousands?|crores?|cr)\b',
            re.IGNORECASE
        )
        text = hindi_num_pattern.sub(repl_hindi_words, text)

        # 7. Numeric digits with Lakh/Lac: "1.5 lakh", "1.5 lac", "3 lakh", "1 lakh", "2 lakh"
        text = re.sub(
            r'\b(\d+(?:\.\d+)?)\s*(?:लाख|lakhs?|lacs?)\b',
            lambda m: str(int(round(float(m.group(1)) * 100000))),
            text,
            flags=re.IGNORECASE
        )

        # Short "1L", "2L", "3L", "1.5L"
        text = re.sub(
            r'\b([1-9](?:\.\d+)?)\s*l\b',
            lambda m: str(int(round(float(m.group(1)) * 100000))),
            text,
            flags=re.IGNORECASE
        )

        # 8. Numeric digits with Thousand / Hazar / k: "6 हजार", "6 hazar", "50 hazar", "50k", "15k", "25k"
        text = re.sub(
            r'\b(\d+(?:\.\d+)?)\s*(?:हजार|हज़ार|haza?ar|thousands?)\b',
            lambda m: str(int(round(float(m.group(1)) * 1000))),
            text,
            flags=re.IGNORECASE
        )

        # Suffix 'k' / 'K': e.g. 50k, 15k, 25k, 6k, 2k, 100k
        text = re.sub(
            r'\b(\d+(?:\.\d+)?)\s*k\b',
            lambda m: str(int(round(float(m.group(1)) * 1000))),
            text,
            flags=re.IGNORECASE
        )

        # 9. Numeric digits with Crore: "1 crore", "2 cr"
        text = re.sub(
            r'\b(\d+(?:\.\d+)?)\s*(?:करोड़|करोड|crores?|cr)\b',
            lambda m: str(int(round(float(m.group(1)) * 10000000))),
            text,
            flags=re.IGNORECASE
        )

        # 10. Clean up any remaining currency symbols
        text = text.replace('₹', ' rs ').replace('Rs.', ' rs ').replace('Rs', ' rs ')

        # Normalize multiple whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @classmethod
    def expand_numeric_search_terms(cls, query: str) -> str:
        """
        Expands normalized digits with common textual and formatted variants (e.g. 50,000)
        to ensure high recall across both unformatted and formatted corpus text in BM25 search.
        """
        tokens = query.split()
        expansions = []
        token_set = {tok.lower() for tok in tokens}
        for t in tokens:
            clean_t = re.sub(r'[^\w%]', '', t.strip())
            if clean_t in NUMERIC_EXPANSIONS:
                for variant in NUMERIC_EXPANSIONS[clean_t]:
                    if variant.lower() not in token_set:
                        expansions.append(variant)
                        token_set.add(variant.lower())
        if expansions:
            return query + " " + " ".join(expansions)
        return query

    @classmethod
    def expand_hinglish_terms(cls, query: str) -> str:
        """
        Expands Hinglish vocabulary with English domain synonyms for BM25 matching.
        """
        words = query.split()
        expanded_tokens = list(words)
        for w in words:
            clean_w = re.sub(r'[^\w]', '', w.lower())
            if clean_w in HINGLISH_TRANSLATION_MAP:
                expanded_tokens.append(HINGLISH_TRANSLATION_MAP[clean_w])
        return " ".join(expanded_tokens)

    @classmethod
    def normalize_query(cls, raw_query: str) -> Dict[str, Any]:
        """
        Produces fully normalized query payload including detected language,
        scheme candidates, numeric normalization, and expanded search terms.
        """
        lang = cls.detect_language(raw_query)
        clean_query = raw_query.strip()

        # Numeric normalization
        num_normalized = cls.normalize_numbers(clean_query)

        # Candidate scheme detection
        candidate_schemes = cls.detect_candidate_schemes(num_normalized)

        # Hinglish expansion if applicable
        if lang == "hi-Latn":
            search_query = cls.expand_hinglish_terms(num_normalized)
        else:
            search_query = num_normalized

        # Expand numeric search terms for BM25 / FTS recall
        search_query = cls.expand_numeric_search_terms(search_query)

        return {
            "raw_query": raw_query,
            "cleaned_query": clean_query,
            "normalized_query": num_normalized,
            "search_query": search_query,
            "detected_language": lang,
            "candidate_schemes": candidate_schemes,
            "primary_scheme_id": candidate_schemes[0][0] if candidate_schemes else None
        }
