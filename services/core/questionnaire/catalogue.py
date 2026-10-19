"""
Questionnaire Catalogue
Extends canonical fact registry with rich bilingual presentation metadata,
input component types, and explainable privacy justifications.
Zero scheme-specific logic or scheme names.
"""
from typing import Dict, Optional
from services.core.facts.registry import FACT_CATALOGUE
from .models import QuestionMetadata

QUESTION_METADATA_CATALOGUE: Dict[str, QuestionMetadata] = {
    # ── Personal ─────────────────────────────────────────────────────────────
    "person.age": QuestionMetadata(
        fact_key="person.age",
        component_type="number",
        label_en="What is your current age?",
        label_hi="आपकी वर्तमान आयु कितनी है?",
        help_text_en="Enter your age in completed years as per official ID.",
        help_text_hi="सरकारी पहचान पत्र के अनुसार पूरे वर्षों में अपनी आयु दर्ज करें।",
        why_asked_en="Most government programmes have designated age eligibility brackets.",
        why_asked_hi="अधिकांश सरकारी कार्यक्रमों में आयु सीमा निर्धारित होती है।",
        unit="years",
        min_value=0,
        max_value=120,
        sensitivity="normal",
        can_skip=False
    ),
    "person.gender": QuestionMetadata(
        fact_key="person.gender",
        component_type="radio",
        label_en="What is your gender?",
        label_hi="आपका लिंग क्या है?",
        why_asked_en="Certain welfare initiatives provide targeted assistance for women and transgender individuals.",
        why_asked_hi="कुछ कल्याणकारी योजनाएं महिलाओं और ट्रांसजेंडर व्यक्तियों के लिए विशेष सहायता प्रदान करती हैं।",
        allowed_values=[
            {"value": "female", "label_en": "Female", "label_hi": "महिला"},
            {"value": "male", "label_en": "Male", "label_hi": "पुरुष"},
            {"value": "other", "label_en": "Other / Transgender", "label_hi": "अन्य / ट्रांसजेंडर"}
        ],
        sensitivity="sensitive",
        can_skip=True
    ),
    "person.marital_status": QuestionMetadata(
        fact_key="person.marital_status",
        component_type="select",
        label_en="What is your marital status?",
        label_hi="आपकी वैवाहिक स्थिति क्या है?",
        why_asked_en="Special support is available for widows, single mothers, and married beneficiaries.",
        why_asked_hi="विधवाओं, एकल माताओं और विवाहित लाभार्थियों के लिए विशेष सहायता उपलब्ध है।",
        allowed_values=[
            {"value": "single", "label_en": "Single / Unmarried", "label_hi": "अविवाहित"},
            {"value": "married", "label_en": "Married", "label_hi": "विवाहित"},
            {"value": "widowed", "label_en": "Widowed", "label_hi": "विधवा / विधुर"},
            {"value": "divorced", "label_en": "Divorced / Separated", "label_hi": "तलाकशुदा / अलग"}
        ],
        sensitivity="normal",
        can_skip=True
    ),
    "person.is_widow_or_senior": QuestionMetadata(
        fact_key="person.is_widow_or_senior",
        component_type="boolean",
        label_en="Are you a widow or a senior citizen (60+)?",
        label_hi="क्या आप विधवा या वरिष्ठ नागरिक (60+) हैं?",
        why_asked_en="Enables qualification for social security pensions and senior care benefits.",
        why_asked_hi="सामाजिक सुरक्षा पेंशन और वरिष्ठ नागरिक देखभाल योजनाओं की पात्रता निर्धारित करता है।",
        sensitivity="normal",
        can_skip=True
    ),
    "person.is_single_girl_child": QuestionMetadata(
        fact_key="person.is_single_girl_child",
        component_type="boolean",
        label_en="Is the applicant a single girl child in the family?",
        label_hi="क्या आवेदिका परिवार में इकलौती बालिका है?",
        why_asked_en="Special scholarships and development grants support single girl children.",
        why_asked_hi="इकलौती बालिका के लिए विशेष छात्रवृत्तियां और विकास अनुदान उपलब्ध हैं।",
        sensitivity="normal",
        can_skip=True
    ),

    # ── Location ─────────────────────────────────────────────────────────────
    "location.state": QuestionMetadata(
        fact_key="location.state",
        component_type="select",
        label_en="Which State or Union Territory do you reside in?",
        label_hi="आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?",
        why_asked_en="Determines whether state-sponsored benefits and regional quotas apply to you.",
        why_asked_hi="यह निर्धारित करता है कि राज्य प्रायोजित योजनाएं और क्षेत्रीय कोटे आप पर लागू होते हैं या नहीं।",
        allowed_values=[
            {"value": s, "label_en": s, "label_hi": s} for s in [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
                "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
                "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
                "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
                "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh"
            ]
        ],
        sensitivity="normal",
        can_skip=False
    ),
    "location.district": QuestionMetadata(
        fact_key="location.district",
        component_type="text",
        label_en="What is your district of residence?",
        label_hi="आपका निवास जिला क्या है?",
        why_asked_en="Certain pilot and aspirational district schemes operate at the district level.",
        why_asked_hi="कुछ आकांक्षी जिला योजनाएं जिला स्तर पर लागू होती हैं।",
        sensitivity="normal",
        can_skip=True
    ),
    "location.urban_rural": QuestionMetadata(
        fact_key="location.urban_rural",
        component_type="radio",
        label_en="Do you live in an urban or rural area?",
        label_hi="क्या आप शहरी या ग्रामीण क्षेत्र में रहते हैं?",
        why_asked_en="Many programmes have distinct guidelines for rural villages vs. municipal urban centers.",
        why_asked_hi="ग्रामीण गांवों और शहरी नगर पालिकाओं के लिए अलग-अलग दिशा-निर्देश होते हैं।",
        allowed_values=[
            {"value": "rural", "label_en": "Rural (Village / Gram Panchayat)", "label_hi": "ग्रामीण (गांव / ग्राम पंचायत)"},
            {"value": "urban", "label_en": "Urban (Town / City / Municipality)", "label_hi": "शहरी (कस्बा / शहर / नगर पालिका)"}
        ],
        sensitivity="normal",
        can_skip=True
    ),
    "location.area_type": QuestionMetadata(
        fact_key="location.area_type",
        component_type="radio",
        label_en="Do you reside in an urban or rural area?",
        label_hi="क्या आप शहरी या ग्रामीण क्षेत्र में रहते हैं?",
        why_asked_en="Determines whether you qualify for urban local body or rural panchayat development schemes.",
        why_asked_hi="यह तय करता है कि क्या आप शहरी निकाय या ग्रामीण पंचायत योजनाओं के पात्र हैं।",
        allowed_values=[
            {"value": "urban", "label_en": "Urban (Town / City / Municipality)", "label_hi": "शहरी (कस्बा / शहर / नगर पालिका)"},
            {"value": "rural", "label_en": "Rural (Village / Gram Panchayat)", "label_hi": "ग्रामीण (गांव / ग्राम पंचायत)"},
            {"value": "peri_urban", "label_en": "Semi-Urban / Peri-Urban", "label_hi": "अर्ध-शहरी"}
        ],
        sensitivity="normal",
        can_skip=True
    ),

    # ── Social & Demographic ─────────────────────────────────────────────────
    "social.caste": QuestionMetadata(
        fact_key="social.caste",
        component_type="select",
        label_en="Which social category / caste group do you belong to?",
        label_hi="आप किस सामाजिक वर्ग / जाति समूह से संबंधित हैं?",
        why_asked_en="Affirmative action programmes provide targeted welfare and financial subsidies for specific communities.",
        why_asked_hi="सकारात्मक कार्रवाई योजनाएं विशिष्ट समुदायों के लिए लक्षित कल्याण और सब्सिडी प्रदान करती हैं।",
        allowed_values=[
            {"value": "general", "label_en": "General", "label_hi": "सामान्य"},
            {"value": "obc", "label_en": "Other Backward Class (OBC)", "label_hi": "अन्य पिछड़ा वर्ग (OBC)"},
            {"value": "sc", "label_en": "Scheduled Caste (SC)", "label_hi": "अनुसूचित जाति (SC)"},
            {"value": "st", "label_en": "Scheduled Tribe (ST)", "label_hi": "अनुसूचित जनजाति (ST)"}
        ],
        sensitivity="sensitive",
        can_skip=True
    ),
    "social.is_minority": QuestionMetadata(
        fact_key="social.is_minority",
        component_type="boolean",
        label_en="Do you belong to a notified religious or linguistic minority community?",
        label_hi="क्या आप किसी अधिसूचित धार्मिक या भाषाई अल्पसंख्यक समुदाय से संबंधित हैं?",
        why_asked_en="Qualifies for Ministry of Minority Affairs educational and livelihood grants.",
        why_asked_hi="अल्पसंख्यक कार्य मंत्रालय की शैक्षिक और आजीविका योजनाओं के लिए पात्रता तय करता है।",
        sensitivity="sensitive",
        can_skip=True
    ),
    "social.is_bpl": QuestionMetadata(
        fact_key="social.is_bpl",
        component_type="boolean",
        label_en="Does your household hold a Below Poverty Line (BPL) or Antyodaya ration card?",
        label_hi="क्या आपके परिवार के पास गरीबी रेखा से नीचे (BPL) या अंत्योदय राशन कार्ड है?",
        why_asked_en="Essential criterion for subsidized housing, nutrition, and essential grain distributions.",
        why_asked_hi="सब्सिडी वाले आवास, पोषण और खाद्यान्न वितरण के लिए महत्वपूर्ण मानदंड।",
        sensitivity="sensitive",
        can_skip=True
    ),

    # ── Health & Disability ──────────────────────────────────────────────────
    "health.has_disability": QuestionMetadata(
        fact_key="health.has_disability",
        component_type="boolean",
        label_en="Do you have a benchmark disability (40% or more)?",
        label_hi="क्या आपको 40% या उससे अधिक की बेंचमार्क दिव्यांगता है?",
        why_asked_en="Unlocks Divyangjan assistive devices, specialized pensions, and job quotas.",
        why_asked_hi="दिव्यांगजन सहायक उपकरण, विशेष पेंशन और आरक्षण लाभ उपलब्ध कराता है।",
        sensitivity="sensitive",
        can_skip=True
    ),
    "health.disability_pct": QuestionMetadata(
        fact_key="health.disability_pct",
        component_type="number",
        label_en="What is your certified percentage of disability?",
        label_hi="आपका प्रमाणित दिव्यांगता प्रतिशत कितना है?",
        why_asked_en="Specific schemes require minimum benchmark disability percentages (e.g. 40% or 80%).",
        why_asked_hi="कुछ योजनाओं में न्यूनतम दिव्यांगता प्रतिशत (जैसे 40% या 80%) अनिवार्य होता है।",
        unit="%",
        min_value=0,
        max_value=100,
        sensitivity="sensitive",
        can_skip=True
    ),

    # ── Household & Financial ────────────────────────────────────────────────
    "household.annual_income": QuestionMetadata(
        fact_key="household.annual_income",
        component_type="number",
        label_en="What is your total annual household income (in INR)?",
        label_hi="आपके परिवार की कुल वार्षिक आय (रुपये में) कितनी है?",
        help_text_en="Include gross income of all earning family members before taxes.",
        help_text_hi="परिवार के सभी कमाने वाले सदस्यों की कुल आय शामिल करें।",
        why_asked_en="Income ceilings determine subsidized interest, cash transfers, and poverty relief.",
        why_asked_hi="आय सीमा रियायती ब्याज, प्रत्यक्ष नकद हस्तांतरण और सहायता की पात्रता तय करती है।",
        unit="INR",
        min_value=0,
        sensitivity="financial",
        can_skip=True
    ),
    "household.family_size": QuestionMetadata(
        fact_key="household.family_size",
        component_type="number",
        label_en="How many members live in your household?",
        label_hi="आपके परिवार में कितने सदस्य रहते हैं?",
        why_asked_en="Determines per-capita benefits, food rations, and household welfare quotas.",
        why_asked_hi="प्रति व्यक्ति लाभ, राशन और पारिवारिक कल्याण कोटे का निर्धारण करता है।",
        unit="members",
        min_value=1,
        max_value=30,
        sensitivity="normal",
        can_skip=True
    ),
    "finance.is_tax_payer": QuestionMetadata(
        fact_key="finance.is_tax_payer",
        component_type="boolean",
        label_en="Does anyone in your family pay income tax or file ITR?",
        label_hi="क्या आपके परिवार में कोई आयकर देता है या ITR दाखिल करता है?",
        why_asked_en="Many rural and poverty alleviation schemes exclude income-tax paying households.",
        why_asked_hi="कई ग्रामीण और गरीबी उन्मूलन योजनाएं आयकर दाता परिवारों को बाहर रखती हैं।",
        sensitivity="financial",
        can_skip=True
    ),
    "finance.is_bank_linked": QuestionMetadata(
        fact_key="finance.is_bank_linked",
        component_type="boolean",
        label_en="Do you have an active bank account linked with Aadhaar (DBT enabled)?",
        label_hi="क्या आपके पास आधार से जुड़ा (DBT सक्षम) बैंक खाता है?",
        why_asked_en="Required for direct benefit transfers (DBT) directly into beneficiary accounts.",
        why_asked_hi="सीधे बैंक खाते में लाभ हस्तांतरण (DBT) प्राप्त करने के लिए आवश्यक है।",
        sensitivity="normal",
        can_skip=True
    ),

    # ── Livelihood & Occupation ──────────────────────────────────────────────
    "occupation.type": QuestionMetadata(
        fact_key="occupation.type",
        component_type="select",
        label_en="What is your primary occupation / employment status?",
        label_hi="आपका मुख्य व्यवसाय / रोजगार की स्थिति क्या है?",
        why_asked_en="Tailors schemes to farmers, students, artisans, gig workers, and job seekers.",
        why_asked_hi="किसानों, छात्रों, कारीगरों और नौकरी चाहने वालों के लिए उपयुक्त योजनाओं की पहचान करता है।",
        allowed_values=[
            {"value": "farmer", "label_en": "Farmer / Cultivator", "label_hi": "किसान / काश्तकार"},
            {"value": "student", "label_en": "Student", "label_hi": "छात्र"},
            {"value": "employed", "label_en": "Employed (Salaried)", "label_hi": "नौकरीपेशा (वेतनभोगी)"},
            {"value": "self_employed", "label_en": "Self Employed / Micro Entrepreneur", "label_hi": "स्व-नियोजित / लघु उद्यमी"},
            {"value": "artisan", "label_en": "Artisan / Craftsperson", "label_hi": "कारीगर / शिल्पकार"},
            {"value": "daily_wage", "label_en": "Daily Wage Labourer", "label_hi": "दैनिक वेतनभोगी श्रमिक"},
            {"value": "unemployed", "label_en": "Unemployed / Seeking Work", "label_hi": "बेरोजगार / कार्य तलाश रहे"},
            {"value": "retired", "label_en": "Retired / Senior", "label_hi": "सेवानिवृत्त / वरिष्ठ"}
        ],
        sensitivity="normal",
        can_skip=False
    ),

    # ── Agriculture ──────────────────────────────────────────────────────────
    "agriculture.has_land": QuestionMetadata(
        fact_key="agriculture.has_land",
        component_type="boolean",
        label_en="Do you or your family own cultivable agricultural land?",
        label_hi="क्या आपके या आपके परिवार के पास कृषि योग्य भूमि है?",
        why_asked_en="Prerequisite for PM-Kisan, crop insurance, and agricultural equipment subsidies.",
        why_asked_hi="पीएम-किसान, फसल बीमा और कृषि उपकरण सब्सिडी के लिए आवश्यक शर्त।",
        sensitivity="normal",
        scope="landholding",
        can_skip=True
    ),
    "agriculture.land_size": QuestionMetadata(
        fact_key="agriculture.land_size",
        component_type="number",
        label_en="What is your total cultivable land holding (in acres)?",
        label_hi="आपकी कुल कृषि भूमि कितनी है (एकड़ में)?",
        why_asked_en="Classifies small and marginal farmers (<= 2 hectares) for subsidized support.",
        why_asked_hi="छोटे और सीमांत किसानों (<= 2 हेक्टेयर) को रियायती सहायता के लिए वर्गीकृत करता है।",
        unit="acres",
        min_value=0,
        sensitivity="normal",
        scope="landholding",
        can_skip=True
    ),

    # ── Education ────────────────────────────────────────────────────────────
    "education.level": QuestionMetadata(
        fact_key="education.level",
        component_type="select",
        label_en="What is your highest level of completed education?",
        label_hi="आपकी उच्चतम शिक्षा क्या है?",
        why_asked_en="Determines eligibility for skill development programs and higher education fellowships.",
        why_asked_hi="कौशल विकास कार्यक्रमों और उच्च शिक्षा फैलोशिप के लिए पात्रता तय करता है।",
        allowed_values=[
            {"value": "primary", "label_en": "Primary (Class 1-5)", "label_hi": "प्राथमिक (कक्षा 1-5)"},
            {"value": "secondary", "label_en": "Secondary (Class 6-10)", "label_hi": "माध्यमिक (कक्षा 6-10)"},
            {"value": "higher_secondary", "label_en": "Higher Secondary (Class 11-12)", "label_hi": "उच्च माध्यमिक (11-12)"},
            {"value": "graduate", "label_en": "Graduate (Bachelors)", "label_hi": "स्नातक (ग्रेजुएट)"},
            {"value": "postgraduate", "label_en": "Postgraduate (Masters/PhD)", "label_hi": "स्नातकोत्तर (पोस्ट ग्रेजुएट)"}
        ],
        sensitivity="normal",
        can_skip=True
    ),

    # ── Agriculture & Farming ────────────────────────────────────────────────
    "applicant.is_farmer_family": QuestionMetadata(
        fact_key="applicant.is_farmer_family",
        component_type="boolean",
        label_en="Do you or does your household belong to a farming / agricultural family?",
        label_hi="क्या आप या आपका परिवार किसी कृषक / किसान परिवार से संबंधित है?",
        why_asked_en="Essential qualification for PM-KISAN, crop insurance, and agricultural welfare transfers.",
        why_asked_hi="पीएम-किसान, फसल बीमा और कृषि कल्याण योजनाओं की पात्रता के लिए आवश्यक।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "applicant.owns_cultivable_land": QuestionMetadata(
        fact_key="applicant.owns_cultivable_land",
        component_type="boolean",
        label_en="Do you or any family member own cultivable agricultural land in your name?",
        label_hi="क्या आपके या परिवार के किसी सदस्य के नाम पर कृषि योग्य भूमि है?",
        why_asked_en="Required for direct landholding farmer income support and machinery subsidies.",
        why_asked_hi="भूमिधारक किसान आय सहायता और कृषि यंत्र सब्सिडी के लिए अनिवार्य।",
        sensitivity="normal",
        scope="landholding",
        can_skip=True
    ),
    "applicant.is_institutional_landholder": QuestionMetadata(
        fact_key="applicant.is_institutional_landholder",
        component_type="boolean",
        label_en="Is the agricultural land held by an institution, trust, or corporate body?",
        label_hi="क्या कृषि भूमि किसी संस्था, ट्रस्ट या कॉर्पोरेट निकाय के नाम पर है?",
        why_asked_en="Statutory exclusion: institutional landholders are disqualified from individual farmer income support.",
        why_asked_hi="वैधानिक अपवर्जन: संस्थागत भूमिधारक व्यक्तिगत किसान सहायता के लिए पात्र नहीं हैं।",
        sensitivity="normal",
        scope="landholding",
        can_skip=True
    ),
    "applicant.is_fish_farmer_or_fisher": QuestionMetadata(
        fact_key="applicant.is_fish_farmer_or_fisher",
        component_type="boolean",
        label_en="Are you engaged in fish farming, inland fishing, coastal fishing, or aquaculture?",
        label_hi="क्या आप मछली पालन, अंतर्देशीय या तटीय मछली पकड़ने या मत्स्य पालन से जुड़े हैं?",
        why_asked_en="Prerequisite for Pradhan Mantri Matsya Sampada Yojana (PMMSY) and fisheries grants.",
        why_asked_hi="प्रधानमंत्री मत्स्य संपदा योजना (PMMSY) और मत्स्य अनुदानों की पात्रता के लिए आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.has_requisite_land_or_water_body": QuestionMetadata(
        fact_key="applicant.has_requisite_land_or_water_body",
        component_type="boolean",
        label_en="Do you possess required ownership or a minimum 10-year registered lease for the project land/water body?",
        label_hi="क्या आपके पास परियोजना भूमि या जल निकाय का स्वामित्व या न्यूनतम 10 वर्षीय पंजीकृत पट्टा है?",
        why_asked_en="Required for capital subsidy approval under fisheries infrastructure programmes.",
        why_asked_hi="मत्स्य अवसंरचना कार्यक्रमों के तहत पूंजीगत सब्सिडी स्वीकृति के लिए आवश्यक।",
        sensitivity="normal",
        scope="landholding",
        can_skip=True
    ),

    # ── Housing & Household Assets ───────────────────────────────────────────
    "household.owns_pucca_house": QuestionMetadata(
        fact_key="household.owns_pucca_house",
        component_type="boolean",
        label_en="Does any member of your household own a pucca (permanent concrete/brick) house anywhere in India?",
        label_hi="क्या आपके परिवार के किसी सदस्य के पास भारत में कहीं भी पक्का (कंक्रीट/ईंट का) मकान है?",
        why_asked_en="Statutory exclusion: families with existing pucca houses cannot receive housing subsidies under PMAY.",
        why_asked_hi="वैधानिक अपवर्जन: पक्के मकान वाले परिवार PMAY के तहत आवास सब्सिडी के लिए अपात्र हैं।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "household.owns_pucca_house_anywhere_in_india": QuestionMetadata(
        fact_key="household.owns_pucca_house_anywhere_in_india",
        component_type="boolean",
        label_en="Does any family member own a pucca house anywhere in India?",
        label_hi="क्या परिवार के किसी सदस्य के पास पूरे भारत में कहीं भी कोई पक्का मकान है?",
        why_asked_en="Statutory eligibility condition for Pradhan Mantri Awas Yojana (Urban and Gramin).",
        why_asked_hi="प्रधानमंत्री आवास योजना (शहरी एवं ग्रामीण) के लिए वैधानिक पात्रता शर्त।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),
    "household.is_homeless_or_kutcha_house": QuestionMetadata(
        fact_key="household.is_homeless_or_kutcha_house",
        component_type="boolean",
        label_en="Is your household currently homeless or residing in a kutcha (thatched/mud/temporary) dwelling?",
        label_hi="क्या आपका परिवार वर्तमान में बेघर है या कच्चे (मिट्टी/घास-फूस/अस्थायी) मकान में रह रहा है?",
        why_asked_en="Primary inclusion criterion for PMAY-Gramin and PMAY-Urban affordable housing allotments.",
        why_asked_hi="PMAY-ग्रामीण और PMAY-शहरी किफायती आवास आवंटन के लिए प्राथमिक समावेशन मानदंड।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),
    "household.has_lpg_connection": QuestionMetadata(
        fact_key="household.has_lpg_connection",
        component_type="boolean",
        label_en="Does any member of your household already have an active LPG (cooking gas) cylinder connection?",
        label_hi="क्या आपके परिवार के किसी सदस्य के पास पहले से कोई एलपीजी (रसोई गैस) कनेक्शन है?",
        why_asked_en="Statutory exclusion: PM Ujjwala Yojana (PMUY) provides free LPG connections only to households with no prior connection.",
        why_asked_hi="वैधानिक अपवर्जन: पीएम उज्ज्वला योजना केवल उन परिवारों को मुफ्त एलपीजी कनेक्शन देती है जिनके पास पहले से कनेक्शन नहीं है।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "household.has_insanitary_or_no_latrine": QuestionMetadata(
        fact_key="household.has_insanitary_or_no_latrine",
        component_type="boolean",
        label_en="Does your household lack an individual functional sanitary toilet / latrine?",
        label_hi="क्या आपके घर में कार्यात्मक व्यक्तिगत शौचालय / लैट्रिन नहीं है?",
        why_asked_en="Qualifies for Swachh Bharat Mission (SBM) individual household latrine construction incentive (INR 12,000).",
        why_asked_hi="स्वच्छ भारत मिशन (SBM) के तहत शौचालय निर्माण प्रोत्साहन राशि (रु. 12,000) के लिए आवश्यक।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),
    "household.owns_functional_sanitary_latrine": QuestionMetadata(
        fact_key="household.owns_functional_sanitary_latrine",
        component_type="boolean",
        label_en="Does your household already own a functional sanitary latrine?",
        label_hi="क्या आपके घर में पहले से एक कार्यात्मक स्वच्छ शौचालय बना हुआ है?",
        why_asked_en="Beneficiaries already possessing a functional toilet cannot receive fresh SBM construction grants.",
        why_asked_hi="जिन लाभार्थियों के पास पहले से शौचालय है, वे स्वच्छ भारत निर्माण अनुदान के पात्र नहीं हैं।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),

    # ── Statutory Exclusions & Governance Criteria ───────────────────────────
    "applicant.is_constitutional_post_holder": QuestionMetadata(
        fact_key="applicant.is_constitutional_post_holder",
        component_type="boolean",
        label_en="Does any family member hold or have held a constitutional post (e.g. Minister, MP, MLA, Mayor, Judge)?",
        label_hi="क्या परिवार का कोई सदस्य किसी संवैधानिक पद (जैसे मंत्री, सांसद, विधायक, मेयर, न्यायाधीश) पर है या रहा है?",
        why_asked_en="Statutory exclusion: constitutional post-holders are barred from poverty alleviation and farmer cash transfers.",
        why_asked_hi="वैधानिक अपवर्जन: संवैधानिक पदों पर रहे व्यक्ति किसान नकद हस्तांतरण और गरीबी उन्मूलन योजनाओं से बाहर हैं।",
        sensitivity="sensitive",
        scope="household",
        can_skip=True
    ),
    "applicant.pays_income_tax": QuestionMetadata(
        fact_key="applicant.pays_income_tax",
        component_type="boolean",
        label_en="Did you pay income tax or file an Income Tax Return (ITR) in the last assessment year?",
        label_hi="क्या आपने पिछले मूल्यांकन वर्ष में आयकर का भुगतान किया या ITR दाखिल किया?",
        why_asked_en="Statutory exclusion across PM-KISAN, PM-SYM, PMUY, and social pensions.",
        why_asked_hi="पीएम-किसान, पीएम-श्रम योगी मानधन, उज्ज्वला और सामाजिक पेंशन में वैधानिक अपवर्जन।",
        sensitivity="financial",
        scope="applicant",
        can_skip=True
    ),
    "household.member_pays_income_tax": QuestionMetadata(
        fact_key="household.member_pays_income_tax",
        component_type="boolean",
        label_en="Does any member of your household pay income tax or file an ITR?",
        label_hi="क्या आपके परिवार का कोई भी सदस्य आयकर देता है या ITR भरता है?",
        why_asked_en="Statutory exclusion for subsidized food rations, welfare cards, and welfare housing.",
        why_asked_hi="राशन कार्ड, कल्याणकारी आवास और गरीबी सहायता योजनाओं में पारिवारिक स्तर पर अपवर्जन।",
        sensitivity="financial",
        scope="household",
        can_skip=True
    ),
    "applicant.covered_under_epfo_esic_nps": QuestionMetadata(
        fact_key="applicant.covered_under_epfo_esic_nps",
        component_type="boolean",
        label_en="Are you formally covered under EPFO (Provident Fund), ESIC, or Government NPS?",
        label_hi="क्या आप ईपीएफओ (PF), ईएसआईसी या सरकारी एनपीएस के तहत औपचारिक रूप से कवर हैं?",
        why_asked_en="Statutory exclusion: PM-SYM and unorganised worker welfare schemes target workers outside formal social security.",
        why_asked_hi="वैधानिक अपवर्जन: पीएम-एसवाईएम जैसी असंगठित श्रमिक योजनाएं केवल औपचारिक सुरक्षा से बाहर के श्रमिकों के लिए हैं।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "household.is_covered_under_other_govt_healthcare": QuestionMetadata(
        fact_key="household.is_covered_under_other_govt_healthcare",
        component_type="boolean",
        label_en="Is your family covered under other government health schemes like CGHS, ESIC, or armed forces health benefits?",
        label_hi="क्या आपका परिवार सीजीएचएस, ईएसआईसी या रक्षा स्वास्थ्य योजनाओं जैसी अन्य सरकारी स्वास्थ्य योजनाओं में कवर है?",
        why_asked_en="Statutory check for Ayushman Bharat (AB-PMJAY) primary health entitlement coverage.",
        why_asked_hi="आयुष्मान भारत (AB-PMJAY) स्वास्थ्य पात्रता के लिए जांच।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),
    "applicant.is_bank_defaulter": QuestionMetadata(
        fact_key="applicant.is_bank_defaulter",
        component_type="boolean",
        label_en="Do you currently have an overdue default or Non-Performing Asset (NPA) record with any commercial bank?",
        label_hi="क्या किसी वाणिज्यिक बैंक में आपका कोई बकाया डिफॉल्ट या गैर-निष्पादित परिसंपत्ति (NPA) रिकॉर्ड है?",
        why_asked_en="Statutory condition: default-free banking status is required for MUDRA, PM SVANidhi, and credit guarantees.",
        why_asked_hi="वैधानिक शर्त: मुद्रा, पीएम स्वनिधि और क्रेडिट गारंटी ऋणों के लिए बैंक डिफॉल्ट-मुक्त होना आवश्यक है।",
        sensitivity="financial",
        scope="applicant",
        can_skip=True
    ),
    "applicant.has_unpaid_pmegp_mudra_svanidhi_credit_scheme_loan_last_5yr": QuestionMetadata(
        fact_key="applicant.has_unpaid_pmegp_mudra_svanidhi_credit_scheme_loan_last_5yr",
        component_type="boolean",
        label_en="Have you defaulted on any previous PMEGP, MUDRA, or PM SVANidhi subsidized loan in the past 5 years?",
        label_hi="क्या आपने पिछले 5 वर्षों में किसी PMEGP, MUDRA या PM स्वनिधि रियायती ऋण में डिफॉल्ट किया है?",
        why_asked_en="Statutory exclusion for subsequent credit-linked subsidy approvals.",
        why_asked_hi="अनुवर्ती ऋण सब्सिडी अनुमोदन के लिए वैधानिक अपवर्जन।",
        sensitivity="financial",
        scope="applicant",
        can_skip=True
    ),
    "applicant.family_member_already_availed_pm_vishwakarma": QuestionMetadata(
        fact_key="applicant.family_member_already_availed_pm_vishwakarma",
        component_type="boolean",
        label_en="Has any family member in your household already received toolkit / financial benefits under PM Vishwakarma?",
        label_hi="क्या आपके परिवार के किसी सदस्य ने पीएम विश्वकर्मा के तहत पहले ही टूलकिट या वित्तीय लाभ प्राप्त किया है?",
        why_asked_en="Statutory limit: PM Vishwakarma benefits are restricted to one artisan beneficiary per family.",
        why_asked_hi="वैधानिक सीमा: पीएम विश्वकर्मा लाभ प्रति परिवार केवल एक कारीगर लाभार्थी तक सीमित है।",
        sensitivity="normal",
        scope="family",
        can_skip=True
    ),
    "applicant.has_duplicate_claim_for_same_asset": QuestionMetadata(
        fact_key="applicant.has_duplicate_claim_for_same_asset",
        component_type="boolean",
        label_en="Have you claimed a capital subsidy for this same machinery, vehicle, or equipment under any other central/state scheme?",
        label_hi="क्या आपने किसी अन्य केंद्रीय/राज्य योजना के तहत इसी मशीनरी, वाहन या उपकरण के लिए पूंजीगत सब्सिडी का दावा किया है?",
        why_asked_en="Statutory prohibition: double-dipping subsidies for the same physical asset is barred under public financial rules.",
        why_asked_hi="वैधानिक रोक: सार्वजनिक वित्तीय नियमों के तहत एक ही संपत्ति के लिए दोहरा सब्सिडी दावा वर्जित है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.has_received_prior_subsidy_for_same_implement_last_5yr": QuestionMetadata(
        fact_key="applicant.has_received_prior_subsidy_for_same_implement_last_5yr",
        component_type="boolean",
        label_en="Have you received a government subsidy for the same farm implement/machinery in the last 5 years?",
        label_hi="क्या आपने पिछले 5 वर्षों में उसी कृषि उपकरण/मशीनरी के लिए सरकारी सब्सिडी प्राप्त की है?",
        why_asked_en="Cooling-off statutory rule: agricultural mechanization subsidies have a 5-year repeat claim bar.",
        why_asked_hi="कृषि यंत्रीकरण योजनाओं में एक ही उपकरण पर 5 वर्ष का कूलिंग-ऑफ नियम लागू होता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "family.exceeds_family_limit_girl_children": QuestionMetadata(
        fact_key="family.exceeds_family_limit_girl_children",
        component_type="boolean",
        label_en="Are there more than two girl children in your family applying for this benefit?",
        label_hi="क्या आपके परिवार में दो से अधिक बालिकाएं इस लाभ के लिए आवेदन कर रही हैं?",
        why_asked_en="Statutory limitation: girl child development schemes (like Sukanya Samriddhi / Pragati) cap benefits at two girls per family.",
        why_asked_hi="बालिका विकास योजनाएं अधिकतम दो बालिकाओं तक लाभ सीमित करती हैं।",
        sensitivity="normal",
        scope="family",
        can_skip=True
    ),
    "applicant.has_siblings_excluding_single_girl_status": QuestionMetadata(
        fact_key="applicant.has_siblings_excluding_single_girl_status",
        component_type="boolean",
        label_en="Does the student applicant have any surviving brothers or sisters?",
        label_hi="क्या छात्र आवेदक का कोई जीवित भाई या बहन है?",
        why_asked_en="Single Girl Child UGC/AICTE fellowships require zero siblings in the family.",
        why_asked_hi="एकल बालिका छात्रवृत्ति के लिए परिवार में कोई अन्य भाई-बहन नहीं होना चाहिए।",
        sensitivity="normal",
        scope="family",
        can_skip=True
    ),
    "applicant.remarriage_occurred": QuestionMetadata(
        fact_key="applicant.remarriage_occurred",
        component_type="boolean",
        label_en="Has remarriage occurred following the demise of the former spouse?",
        label_hi="क्या पूर्व पति/पत्नी के निधन के पश्चात पुनर्विवाह हुआ है?",
        why_asked_en="Statutory condition: Indira Gandhi National Widow Pension terminates upon subsequent remarriage.",
        why_asked_hi="वैधानिक शर्त: पुनर्विवाह होने पर राष्ट्रीय विधवा पेंशन योजना की पात्रता समाप्त हो जाती है।",
        sensitivity="sensitive",
        scope="applicant",
        can_skip=True
    ),

    # ── Artisans, Micro Enterprises & Livelihood ──────────────────────────────
    "artisan.trade_type": QuestionMetadata(
        fact_key="artisan.trade_type",
        component_type="select",
        label_en="Which traditional trade or craft do you practice with your hands and tools?",
        label_hi="आप अपने हाथों और औजारों से कौन सा पारंपरिक शिल्प या व्यवसाय करते हैं?",
        why_asked_en="Direct eligibility for PM Vishwakarma artisan toolkit incentive, skill training, and 5% collateral-free credit.",
        why_asked_hi="पीएम विश्वकर्मा टूलकिट प्रोत्साहन, प्रशिक्षण और 5% संपार्श्विक-मुक्त ऋण की सीधी पात्रता।",
        allowed_values=[
            {"value": "carpenter", "label_en": "Carpenter (Suthar)", "label_hi": "बढ़ई (सुथार)"},
            {"value": "boat_maker", "label_en": "Boat Maker", "label_hi": "नाव बनाने वाले"},
            {"value": "armourer", "label_en": "Armourer", "label_hi": "अस्त्रकार"},
            {"value": "blacksmith", "label_en": "Blacksmith (Lohar)", "label_hi": "लोहार"},
            {"value": "hammer_tool_maker", "label_en": "Hammer & Tool Kit Maker", "label_hi": "हथौड़ा और औजार निर्माता"},
            {"value": "locksmith", "label_en": "Locksmith", "label_hi": "ताला बनाने वाले"},
            {"value": "sculptor", "label_en": "Sculptor / Stone Carver", "label_hi": "मूर्तिकार / पत्थर तराशने वाले"},
            {"value": "goldsmith", "label_en": "Goldsmith (Sonar)", "label_hi": "सुनार"},
            {"value": "potter", "label_en": "Potter (Kumhaar)", "label_hi": "कुम्हार"},
            {"value": "cobbler", "label_en": "Cobbler / Footwear Artisan", "label_hi": "मोची / चर्मकार"},
            {"value": "mason", "label_en": "Mason (Rajmistri)", "label_hi": "राजमिस्त्री"},
            {"value": "basket_mat_maker", "label_en": "Basket / Mat / Broom Maker", "label_hi": "टोकरी / चटाई / झाड़ू निर्माता"},
            {"value": "doll_toy_maker", "label_en": "Traditional Doll & Toy Maker", "label_hi": "पारंपरिक गुड़िया और खिलौना निर्माता"},
            {"value": "barber", "label_en": "Barber (Naai)", "label_hi": "नाई"},
            {"value": "garland_maker", "label_en": "Garland Maker (Malakaar)", "label_hi": "मालाकार"},
            {"value": "washerman", "label_en": "Washerman (Dhobi)", "label_hi": "धोबी"},
            {"value": "tailor", "label_en": "Tailor (Darzi)", "label_hi": "दर्जी"},
            {"value": "fishing_net_maker", "label_en": "Fishing Net Maker", "label_hi": "मछली का जाल बनाने वाले"},
            {"value": "other_craft", "label_en": "Other Traditional Craft", "label_hi": "अन्य पारंपरिक शिल्प"}
        ],
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.is_non_corporate_small_business": QuestionMetadata(
        fact_key="applicant.is_non_corporate_small_business",
        component_type="boolean",
        label_en="Are you operating a non-corporate, non-farm small/micro business or street vending activity?",
        label_hi="क्या आप गैर-कॉर्पोरेट, गैर-कृषि लघु/सूक्ष्म व्यवसाय या स्ट्रीट वेंडिंग गतिविधि संचालित कर रहे हैं?",
        why_asked_en="Qualifies for Pradhan Mantri MUDRA Yojana (Shishu/Kishore/Tarun) and PM SVANidhi working capital loans.",
        why_asked_hi="प्रधानमंत्री मुद्रा योजना और पीएम स्वनिधि कार्यशील पूंजी ऋण के लिए आवश्यक।",
        sensitivity="normal",
        scope="enterprise",
        can_skip=True
    ),
    "enterprise.is_farm_credit": QuestionMetadata(
        fact_key="enterprise.is_farm_credit",
        component_type="boolean",
        label_en="Is this credit facility intended exclusively for farm production / agricultural cultivation activities?",
        label_hi="क्या यह ऋण सुविधा विशेष रूप से कृषि उत्पादन / खेती की गतिविधियों के लिए है?",
        why_asked_en="Differentiates agricultural crop loans (KCC) from non-farm MSME business credit under MUDRA.",
        why_asked_hi="मुद्रा योजना के गैर-कृषि व्यवसाय ऋण को किसान क्रेडिट कार्ड फसल ऋण से अलग करता है।",
        sensitivity="normal",
        scope="enterprise",
        can_skip=True
    ),
    "applicant.has_minimum_epf_service_years": QuestionMetadata(
        fact_key="applicant.has_minimum_epf_service_years",
        component_type="boolean",
        label_en="Do you have at least 10 years of eligible contributory service under Employees' Pension Scheme (EPS)?",
        label_hi="क्या आपके पास कर्मचारी पेंशन योजना (EPS) के तहत न्यूनतम 10 वर्ष की अंशदायी सेवा है?",
        why_asked_en="Statutory vesting requirement for EPFO lifelong monthly pension entitlement at age 58.",
        why_asked_hi="58 वर्ष की आयु में ईपीएफओ मासिक पेंशन पात्रता के लिए 10 वर्ष की न्यूनतम सेवा अनिवार्य है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.received_prior_training_under_govt_scheme": QuestionMetadata(
        fact_key="applicant.received_prior_training_under_govt_scheme",
        component_type="boolean",
        label_en="Have you completed basic/advanced skill certification under an NSDC / Ministry skill training scheme?",
        label_hi="क्या आपने एनएसडीसी या मंत्रालय कौशल प्रशिक्षण योजना के तहत कौशल प्रमाणन पूरा किया है?",
        why_asked_en="Unlocks second-tranche concessional credit and modern toolkit grant under artisan schemes.",
        why_asked_hi="कारीगर योजनाओं में दूसरे चरण का रियायती ऋण और आधुनिक टूलकिट अनुदान अनलॉक करता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),

    # ── Students & Higher Education ──────────────────────────────────────────
    "student.class_level": QuestionMetadata(
        fact_key="student.class_level",
        component_type="select",
        label_en="Which educational stage or course are you currently enrolled in?",
        label_hi="आप वर्तमान में किस कक्षा या शैक्षणिक पाठ्यक्रम में नामांकित हैं?",
        why_asked_en="Matches pre-matric, post-matric, technical diploma, and collegiate scholarship programs.",
        why_asked_hi="प्री-मैट्रिक, पोस्ट-मैट्रिक, डिप्लोमा और कॉलेज छात्रवृत्ति कार्यक्रमों की पहचान करता है।",
        allowed_values=[
            {"value": "pre_matric", "label_en": "Pre-Matric (Class 1 to 10)", "label_hi": "प्री-मैट्रिक (कक्षा 1 से 10)"},
            {"value": "post_matric", "label_en": "Post-Matric (Class 11 & 12)", "label_hi": "पोस्ट-मैट्रिक (कक्षा 11 एवं 12)"},
            {"value": "diploma", "label_en": "Technical Diploma / ITI", "label_hi": "डिप्लोमा / आईटीआई"},
            {"value": "undergraduate", "label_en": "Undergraduate Degree (B.A., B.Sc., B.Tech, etc.)", "label_hi": "स्नातक (बी.ए., बी.एस.सी., बी.टेक आदि)"},
            {"value": "postgraduate", "label_en": "Postgraduate Degree (M.A., M.Sc., M.Tech, etc.)", "label_hi": "स्नातकोत्तर (एम.ए., एम.एस.सी. आदि)"},
            {"value": "doctoral", "label_en": "M.Phil / Ph.D. / Research Fellowship", "label_hi": "डॉक्टरेट / अनुसंधान फैलोशिप"}
        ],
        sensitivity="normal",
        scope="student",
        can_skip=True
    ),
    "student.enrolled_in_technical_course": QuestionMetadata(
        fact_key="student.enrolled_in_technical_course",
        component_type="boolean",
        label_en="Are you enrolled in an AICTE / UGC approved technical, engineering, architectural, or pharmacy degree program?",
        label_hi="क्या आप एआईसीटीई/यूजीसी द्वारा अनुमोदित तकनीकी, इंजीनियरिंग या फार्मेसी डिग्री में नामांकित हैं?",
        why_asked_en="Essential qualification for AICTE Pragati (Girl Child) and Saksham (Divyangjan) technical scholarships.",
        why_asked_hi="एआईसीटीई प्रगति (बालिका) और सक्षम (दिव्यांगजन) तकनीकी छात्रवृत्ति के लिए अनिवार्य।",
        sensitivity="normal",
        scope="student",
        can_skip=True
    ),
    "student.enrolled_in_distance_education_course": QuestionMetadata(
        fact_key="student.enrolled_in_distance_education_course",
        component_type="boolean",
        label_en="Are you pursuing this course through correspondence, distance education, or open university?",
        label_hi="क्या आप यह पाठ्यक्रम पत्राचार, दूरस्थ शिक्षा या मुक्त विश्वविद्यालय के माध्यम से कर रहे हैं?",
        why_asked_en="Statutory exclusion: several central residential scholarships exclude distance/correspondence mode students.",
        why_asked_hi="दूरस्थ या पत्राचार शिक्षा वाले छात्र कई आवासीय छात्रवृत्तियों से बाहर रहते हैं।",
        sensitivity="normal",
        scope="student",
        can_skip=True
    ),
    "student.enrolled_in_residential_school": QuestionMetadata(
        fact_key="student.enrolled_in_residential_school",
        component_type="boolean",
        label_en="Are you enrolled as a hosteller or residing in a government-recognized residential school?",
        label_hi="क्या आप किसी मान्यता प्राप्त आवासीय विद्यालय या छात्रावास में नामांकित हैं?",
        why_asked_en="Determines hosteller vs day-scholar maintenance allowances under Post-Matric schemes.",
        why_asked_hi="पोस्ट-मैट्रिक योजनाओं में छात्रावास और गैर-छात्रावास भत्ते की दर निर्धारित करता है।",
        sensitivity="normal",
        scope="student",
        can_skip=True
    ),
    "student.domicile_state": QuestionMetadata(
        fact_key="student.domicile_state",
        component_type="select",
        label_en="Which state is the student's permanent domicile state?",
        label_hi="छात्र का स्थायी मूल निवास राज्य कौन सा है?",
        why_asked_en="Required for state-administered Post-Matric SC/ST/OBC scholarship processing.",
        why_asked_hi="राज्य द्वारा संचालित पोस्ट-मैट्रिक छात्रवृत्तियों के लिए आवश्यक।",
        allowed_values=[
            {"value": s, "label_en": s, "label_hi": s} for s in [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
                "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
                "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
                "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
                "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh"
            ]
        ],
        sensitivity="normal",
        scope="student",
        can_skip=True
    ),

    # ── Administrative & Verification Primitives ─────────────────────────────
    "applicant.has_savings_bank_account": QuestionMetadata(
        fact_key="applicant.has_savings_bank_account",
        component_type="boolean",
        label_en="Do you have an active savings bank account in a scheduled commercial bank or post office?",
        label_hi="क्या आपके पास किसी अनुसूचित वाणिज्यिक बैंक या डाकघर में सक्रिय बचत बैंक खाता है?",
        why_asked_en="Mandatory for receiving Direct Benefit Transfer (DBT) subsidies and monthly pension payments.",
        why_asked_hi="प्रत्यक्ष लाभ अंतरण (DBT) सब्सिडी और मासिक पेंशन प्राप्त करने के लिए अनिवार्य।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.completed_ekyc": QuestionMetadata(
        fact_key="applicant.completed_ekyc",
        component_type="boolean",
        label_en="Have you completed Aadhaar-based electronic biometric or OTP eKYC verification?",
        label_hi="क्या आपने आधार आधारित इलेक्ट्रॉनिक बायोमेट्रिक या ओटीपी ई-केवाईसी पूरी कर ली है?",
        why_asked_en="Administrative prerequisite for disbursal of PM-KISAN instalments and subsidized LPG connections.",
        why_asked_hi="पीएम-किसान किस्तों और रियायती गैस कनेक्शन के वितरण के लिए प्रशासनिक आवश्यकता।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "household.bpl_status_verified": QuestionMetadata(
        fact_key="household.bpl_status_verified",
        component_type="boolean",
        label_en="Does your household have an officially verified BPL / Antyodaya / SECC deprivation record?",
        label_hi="क्या आपके परिवार का बीपीएल / अंत्योदय / एसईसीसी सत्यापन रिकॉर्ड आधिकारिक रूप से मान्य है?",
        why_asked_en="Verification requirement for priority issuance of PMUY gas connections and welfare ration allocations.",
        why_asked_hi="उज्ज्वला गैस कनेक्शन और कल्याणकारी राशन के प्राथमिकता आवंटन के लिए सत्यापन आवश्यकता।",
        sensitivity="sensitive",
        scope="household",
        can_skip=True
    ),
    "person.disability_percentage": QuestionMetadata(
        fact_key="person.disability_percentage",
        component_type="number",
        label_en="What is your certified percentage of benchmark disability (as per UDID card / Medical Board certificate)?",
        label_hi="यूडीआईडी कार्ड / मेडिकल बोर्ड प्रमाण पत्र के अनुसार आपका प्रमाणित दिव्यांगता प्रतिशत कितना है?",
        why_asked_en="Statutory eligibility: benchmark benefits require >= 40% disability; Indira Gandhi Disability Pension requires >= 80% severe disability.",
        why_asked_hi="40% या अधिक पर सामान्य दिव्यांग लाभ और 80% या अधिक पर गंभीर दिव्यांगता पेंशन देय होती है।",
        unit="%",
        min_value=0,
        max_value=100,
        sensitivity="sensitive",
        scope="applicant",
        can_skip=True
    ),
    "beneficiary.meets_severe_disability_threshold": QuestionMetadata(
        fact_key="beneficiary.meets_severe_disability_threshold",
        component_type="boolean",
        label_en="Does the beneficiary have severe or profound disability (80% or higher benchmark disability)?",
        label_hi="क्या लाभार्थी को गंभीर या अत्यधिक दिव्यांगता (80% या उससे अधिक) है?",
        why_asked_en="Qualifies for highest-slab disability social assistance pensions (IGNDPS).",
        why_asked_hi="राष्ट्रीय गंभीर दिव्यांगता पेंशन (IGNDPS) के लिए पात्रता तय करता है।",
        sensitivity="sensitive",
        scope="beneficiary",
        can_skip=True
    ),

    # ── Controlled Pilot & Corrected PMJJBY Facts ────────────────────────────
    "household.willing_to_do_unskilled_manual_work": QuestionMetadata(
        fact_key="household.willing_to_do_unskilled_manual_work",
        component_type="boolean",
        label_en="Is any adult member of your household willing to do unskilled manual work?",
        label_hi="क्या आपके परिवार का कोई वयस्क सदस्य अकुशल शारीरिक श्रम करने को तैयार है?",
        why_asked_en="Statutory entitlement under MGNREGA guarantees 100 days of wage employment for rural households willing to do unskilled manual work.",
        why_asked_hi="मनरेगा के तहत अकुशल शारीरिक श्रम करने के इच्छुक ग्रामीण परिवारों को 100 दिनों के रोजगार की गारंटी मिलती है।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "applicant.is_farmer": QuestionMetadata(
        fact_key="applicant.is_farmer",
        component_type="boolean",
        label_en="Are you an active farmer cultivating agricultural land?",
        label_hi="क्या आप कृषि भूमि पर खेती करने वाले सक्रिय किसान हैं?",
        why_asked_en="Identifies eligibility for central and state agricultural support schemes.",
        why_asked_hi="केंद्रीय और राज्य कृषि सहायता योजनाओं के लिए पात्रता की पहचान करता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.owns_or_leases_agricultural_land": QuestionMetadata(
        fact_key="applicant.owns_or_leases_agricultural_land",
        component_type="boolean",
        label_en="Do you own or lease cultivable agricultural land?",
        label_hi="क्या आपके पास कृषि योग्य भूमि का स्वामित्व या पट्टा है?",
        why_asked_en="Determines landholder qualification for crop insurance and agricultural credit.",
        why_asked_hi="फसल बीमा और कृषि ऋण के लिए भू-स्वामी या काश्तकार पात्रता तय करता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.growing_notified_crop_in_notified_area": QuestionMetadata(
        fact_key="applicant.growing_notified_crop_in_notified_area",
        component_type="boolean",
        label_en="Are you cultivating a notified crop in a notified area for the current season?",
        label_hi="क्या आप चालू मौसम में अधिसूचित क्षेत्र में अधिसूचित फसल उगा रहे हैं?",
        why_asked_en="Pradhan Mantri Fasal Bima Yojana covers crops notified by state governments in specific administrative areas.",
        why_asked_hi="प्रधानमंत्री फसल बीमा योजना के तहत राज्य सरकार द्वारा अधिसूचित फसलों पर बीमा कवर मिलता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.has_insurable_interest_in_crop": QuestionMetadata(
        fact_key="applicant.has_insurable_interest_in_crop",
        component_type="boolean",
        label_en="Do you have an insurable financial interest in the standing crop?",
        label_hi="क्या खड़ी फसल में आपका प्रत्यक्ष बीमा योग्य वित्तीय हित है?",
        why_asked_en="Insurance guidelines require growers to have a direct financial stake in the crop.",
        why_asked_hi="बीमा दिशानिर्देशों के अनुसार फसल में किसान का वित्तीय हित होना अनिवार्य है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_farmer_or_cultivator": QuestionMetadata(
        fact_key="applicant.is_farmer_or_cultivator",
        component_type="boolean",
        label_en="Are you an owner cultivator, tenant farmer, oral lessee, or sharecropper?",
        label_hi="क्या आप स्वयं-काश्तकार, बटाईदार या पट्टेदार किसान हैं?",
        why_asked_en="Kisan Credit Card (KCC) extends institutional credit to all categories of actual cultivators.",
        why_asked_hi="किसान क्रेडिट कार्ड (KCC) सभी श्रेणियों के वास्तविक कृषकों को संस्थागत ऋण प्रदान करता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "household.is_aay_or_priority_household": QuestionMetadata(
        fact_key="household.is_aay_or_priority_household",
        component_type="boolean",
        label_en="Is your household designated as Antyodaya Anna Yojana (AAY) or Priority Household (PHH)?",
        label_hi="क्या आपका परिवार अंत्योदय अन्न योजना (AAY) या प्राथमिकता परिवार (PHH) के रूप में चिह्नित है?",
        why_asked_en="Determines statutory entitlement to highly subsidised or free foodgrains under the National Food Security Act (NFSA).",
        why_asked_hi="राष्ट्रीय खाद्य सुरक्षा अधिनियम (NFSA) के तहत मुफ्त या रियायती खाद्यान्न की पात्रता तय करता है।",
        sensitivity="sensitive",
        scope="household",
        can_skip=False
    ),
    "household.covered_under_ration_card": QuestionMetadata(
        fact_key="household.covered_under_ration_card",
        component_type="boolean",
        label_en="Does your household hold a valid ration card issued by the Food & Civil Supplies Department?",
        label_hi="क्या आपके परिवार के पास खाद्य एवं नागरिक आपूर्ति विभाग द्वारा जारी वैध राशन कार्ड है?",
        why_asked_en="Ration card acts as the legal entitlement document for public distribution foodgrains.",
        why_asked_hi="राशन कार्ड सार्वजनिक वितरण प्रणाली के तहत खाद्यान्न प्राप्त करने का कानूनी दस्तावेज है।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "household.owns_four_wheeler": QuestionMetadata(
        fact_key="household.owns_four_wheeler",
        component_type="boolean",
        label_en="Does any member of your household own a four-wheeled motorized vehicle?",
        label_hi="क्या आपके परिवार के किसी सदस्य के पास चार पहिया मोटर वाहन है?",
        why_asked_en="Statutory exclusion criterion for several targeted welfare and subsidized foodgrain schemes.",
        why_asked_hi="कई लक्षित कल्याणकारी और रियायती खाद्यान्न योजनाओं के लिए यह एक वैधानिक अपवर्जन मानदंड है।",
        sensitivity="normal",
        scope="household",
        can_skip=True
    ),
    "beneficiary.is_girl_child": QuestionMetadata(
        fact_key="beneficiary.is_girl_child",
        component_type="boolean",
        label_en="Is the beneficiary a girl child?",
        label_hi="क्या लाभार्थी बालिका है?",
        why_asked_en="Determines eligibility for girl child development and financial security programmes.",
        why_asked_hi="बालिका विकास और वित्तीय सुरक्षा कार्यक्रमों के लिए पात्रता निर्धारित करता है।",
        sensitivity="normal",
        scope="beneficiary",
        can_skip=False
    ),
    "beneficiary.age": QuestionMetadata(
        fact_key="beneficiary.age",
        component_type="number",
        label_en="What is the age of the child beneficiary (in completed years)?",
        label_hi="बालक/बालिका लाभार्थी की आयु (पूर्ण वर्षों में) कितनी है?",
        why_asked_en="Programmes like Sukanya Samriddhi Yojana require account opening before the girl turns 10 years.",
        why_asked_hi="सुकन्या समृद्धि योजना जैसी योजनाओं में 10 वर्ष की आयु से पहले खाता खोलना आवश्यक है।",
        unit="years",
        min_value=0,
        max_value=25,
        sensitivity="normal",
        scope="beneficiary",
        can_skip=False
    ),
    "applicant.is_parent_or_legal_guardian": QuestionMetadata(
        fact_key="applicant.is_parent_or_legal_guardian",
        component_type="boolean",
        label_en="Are you the biological parent or legal court-appointed guardian of the child?",
        label_hi="क्या आप बच्चे के जैविक माता-पिता या कानूनी अभिभावक हैं?",
        why_asked_en="Statutory requirement to open and operate welfare accounts on behalf of minor children.",
        why_asked_hi="नाबालिग बच्चों की ओर से कल्याणकारी खाता खोलने और संचालित करने के लिए आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "family.existing_ssy_accounts_count": QuestionMetadata(
        fact_key="family.existing_ssy_accounts_count",
        component_type="number",
        label_en="How many Sukanya Samriddhi accounts have already been opened in your family?",
        label_hi="आपके परिवार में पहले से कितने सुकन्या समृद्धि खाते खोले जा चुके हैं?",
        why_asked_en="Statutory limit allows maximum 2 accounts per family (with exception for twins/triplets).",
        why_asked_hi="प्रति परिवार अधिकतम 2 खातों की कानूनी सीमा (जुड़वां बच्चों को छोड़कर) होती है।",
        min_value=0,
        max_value=5,
        sensitivity="normal",
        scope="family",
        can_skip=False
    ),
    "applicant.is_member_of_women_shg": QuestionMetadata(
        fact_key="applicant.is_member_of_women_shg",
        component_type="boolean",
        label_en="Are you an active member of a recognized Women Self Help Group (SHG)?",
        label_hi="क्या आप किसी मान्यता प्राप्त महिला स्वयं सहायता समूह (SHG) की सक्रिय सदस्य हैं?",
        why_asked_en="Qualifies for credit linkage, revolving funds, and enterprise grants under DAY-NRLM.",
        why_asked_hi="दीनदयाल अंत्योदय योजना - राष्ट्रीय ग्रामीण आजीविका मिशन (DAY-NRLM) के तहत ऋण और अनुदान के लिए आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "family.girl_children_count": QuestionMetadata(
        fact_key="family.girl_children_count",
        component_type="number",
        label_en="How many girl children are there in your family?",
        label_hi="आपके परिवार में कुल कितनी बेटियां हैं?",
        why_asked_en="Schemes like UP Kanya Sumangala apply benefit caps based on the number of girl children in the family.",
        why_asked_hi="उत्तर प्रदेश कन्या सुमंगला जैसी योजनाओं में परिवार में बालिकाओं की संख्या के आधार पर सीमा तय होती है।",
        min_value=0,
        max_value=10,
        sensitivity="normal",
        scope="family",
        can_skip=False
    ),
    "student.educational_milestone_completed": QuestionMetadata(
        fact_key="student.educational_milestone_completed",
        component_type="select",
        label_en="What educational milestone has been completed?",
        label_hi="कौन सा शैक्षणिक पड़ाव पूरा किया गया है?",
        why_asked_en="Determines tranche eligibility for education incentives such as Bihar Mukhyamantri Kanya Utthan Yojana.",
        why_asked_hi="बिहार मुख्यमंत्री कन्या उत्थान योजना जैसे शिक्षा प्रोत्साहनों के लिए किस्त पात्रता तय करता है।",
        allowed_values=[
            {"value": "matriculation", "label_en": "Matriculation (Class 10)", "label_hi": "मैट्रिक (10वीं)"},
            {"value": "intermediate", "label_en": "Intermediate (Class 12)", "label_hi": "इंटरमीडिएट (12वीं)"},
            {"value": "graduation", "label_en": "Graduation / Degree", "label_hi": "स्नातक / डिग्री"},
            {"value": "post_graduation", "label_en": "Post Graduation", "label_hi": "स्नातकोत्तर"},
            {"value": "none", "label_en": "None / Lower", "label_hi": "कोई नहीं / निचली कक्षा"}
        ],
        sensitivity="normal",
        scope="student",
        can_skip=False
    ),
    "applicant.is_unmarried": QuestionMetadata(
        fact_key="applicant.is_unmarried",
        component_type="boolean",
        label_en="Is the applicant/student unmarried?",
        label_hi="क्या आवेदिका/छात्रा अविवाहित है?",
        why_asked_en="Certain girl-child education cash transfers require the beneficiary to remain unmarried until completion.",
        why_asked_hi="बालिका शिक्षा नकद सहायता योजनाओं में पढ़ाई पूरी होने तक अविवाहित रहना आवश्यक होता है।",
        sensitivity="sensitive",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_woman_head_of_family": QuestionMetadata(
        fact_key="applicant.is_woman_head_of_family",
        component_type="boolean",
        label_en="Are you designated as the woman head of the family in the ration card?",
        label_hi="क्या आप राशन कार्ड में परिवार की महिला मुखिया के रूप में दर्ज हैं?",
        why_asked_en="Statutory eligibility requirement for direct financial support schemes like Karnataka Gruha Lakshmi.",
        why_asked_hi="कर्नाटक गृह लक्ष्मी जैसी योजनाओं में प्रत्यक्ष वित्तीय सहायता के लिए महिला मुखिया होना अनिवार्य है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_gst_registered_trader": QuestionMetadata(
        fact_key="applicant.is_gst_registered_trader",
        component_type="boolean",
        label_en="Are you or your spouse a GST-registered taxpayer / trader?",
        label_hi="क्या आप या आपके जीवनसाथी जीएसटी पंजीकृत करदाता / व्यापारी हैं?",
        why_asked_en="Statutory exclusion criterion for welfare cash-assistance programmes (Gruha Lakshmi, Ladki Bahin).",
        why_asked_hi="कल्याणकारी नकद सहायता योजनाओं के लिए वैधानिक अपवर्जन मानदंड।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "household.is_swasthya_sathi_enrolled": QuestionMetadata(
        fact_key="household.is_swasthya_sathi_enrolled",
        component_type="boolean",
        label_en="Is your household enrolled with an active Swasthya Sathi card?",
        label_hi="क्या आपके परिवार के पास सक्रिय स्वास्थ्य साथी कार्ड है?",
        why_asked_en="Used as primary household identity rail for West Bengal Lakshmir Bhandar entitlement.",
        why_asked_hi="पश्चिम बंगाल लक्ष्मी भंडार योजना में परिवार की पहचान और पात्रता के लिए आवश्यक।",
        sensitivity="normal",
        scope="household",
        can_skip=False
    ),
    "applicant.is_regular_government_employee": QuestionMetadata(
        fact_key="applicant.is_regular_government_employee",
        component_type="boolean",
        label_en="Are you or any family member a regular, permanent government or PSU employee?",
        label_hi="क्या आप या आपके परिवार का कोई सदस्य नियमित सरकारी या पीएसयू कर्मचारी है?",
        why_asked_en="Standard statutory exclusion across targeted social assistance schemes.",
        why_asked_hi="लक्षित सामाजिक सहायता योजनाओं में मानक वैधानिक अपवर्जन मानदंड।",
        sensitivity="normal",
        scope="applicant",
        can_skip=True
    ),
    "applicant.has_eligible_participating_account": QuestionMetadata(
        fact_key="applicant.has_eligible_participating_account",
        component_type="boolean",
        label_en="Do you hold an active individual savings account in a participating bank or Post Office?",
        label_hi="क्या आपके पास सहभागी बैंक या डाकघर में सक्रिय व्यक्तिगत बचत खाता है?",
        why_asked_en="Statutory requirement: PMJJBY coverage is provided through individual accounts in participating banks/Post Offices.",
        why_asked_hi="वैधानिक आवश्यकता: पीएमजेजेबीवाई बीमा सहभागी बैंक/डाकघर के व्यक्तिगत खाते के माध्यम से प्रदान किया जाता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.auto_debit_consent": QuestionMetadata(
        fact_key="applicant.auto_debit_consent",
        component_type="boolean",
        label_en="Have you submitted auto-debit consent for annual premium deduction?",
        label_hi="क्या आपने वार्षिक प्रीमियम कटौती के लिए ऑटो-डेबिट सहमति दी है?",
        why_asked_en="Administrative prerequisite: enables participating banks to automatically debit the annual premium on or before May 31.",
        why_asked_hi="प्रशासनिक पूर्वापेक्षा: सहभागी बैंक को 31 मई तक वार्षिक प्रीमियम स्वचालित रूप से काटने की अनुमति देती है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),

    # ── 11. Statutory Welfare & Labour Board Criteria (Phase 2.3 Questions) ──
    "student.is_enrolled": QuestionMetadata(
        fact_key="student.is_enrolled",
        component_type="boolean",
        label_en="Are you currently enrolled as a student in a recognized educational institution?",
        label_hi="क्या आप वर्तमान में किसी मान्यता प्राप्त शिक्षण संस्थान में एक छात्र के रूप में नामांकित हैं?",
        why_asked_en="Required for academic scholarships, fee reimbursements, and student welfare programmes.",
        why_asked_hi="शैक्षणिक छात्रवृत्ति, शुल्क प्रतिपूर्ति और छात्र कल्याण कार्यक्रमों के लिए आवश्यक।",
        sensitivity="normal",
        scope="student",
        can_skip=False
    ),
    "applicant.is_registered_bocw_worker": QuestionMetadata(
        fact_key="applicant.is_registered_bocw_worker",
        component_type="boolean",
        label_en="Are you registered with the Building and Other Construction Workers (BOCW) Welfare Board?",
        label_hi="क्या आप भवन एवं अन्य सन्निर्माण कर्मकार (BOCW) कल्याण बोर्ड में पंजीकृत हैं?",
        why_asked_en="Statutory requirement: unlocks construction worker welfare funds, education grants, and maternity benefits.",
        why_asked_hi="वैधानिक आवश्यकता: निर्माण श्रमिक कल्याण कोष, शिक्षा अनुदान और मातृत्व लाभ प्राप्त करने के लिए आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.parent_is_registered_bocw_worker": QuestionMetadata(
        fact_key="applicant.parent_is_registered_bocw_worker",
        component_type="boolean",
        label_en="Is either of your parents a registered BOCW construction worker?",
        label_hi="क्या आपके माता-पिता में से कोई भवन एवं अन्य सन्निर्माण कर्मकार (BOCW) कल्याण बोर्ड में पंजीकृत श्रमिक हैं?",
        why_asked_en="Required to qualify for BOCW children scholarship schemes and educational stipends.",
        why_asked_hi="BOCW बच्चों की छात्रवृत्ति योजनाओं और शैक्षणिक वजीफे के लिए पात्र होने के लिए आवश्यक।",
        sensitivity="normal",
        scope="family",
        can_skip=False
    ),
    "person.is_widow": QuestionMetadata(
        fact_key="person.is_widow",
        component_type="boolean",
        label_en="Is the applicant a widow?",
        label_hi="क्या आवेदिका विधवा हैं?",
        why_asked_en="Required for widow pension schemes, destitute survivor support, and financial rehabilitation.",
        why_asked_hi="विधवा पेंशन योजनाओं, निराश्रित उत्तरजीवी सहायता और वित्तीय पुनर्वास के लिए आवश्यक।",
        sensitivity="sensitive",
        scope="applicant",
        can_skip=False
    ),
    "person.is_widow_or_destitute": QuestionMetadata(
        fact_key="person.is_widow_or_destitute",
        component_type="boolean",
        label_en="Are you a widow, destitute, or deserted woman without independent livelihood?",
        label_hi="क्या आप विधवा, निराश्रित या परित्यक्ता महिला हैं जिनका कोई स्वतंत्र आजीविका साधन नहीं है?",
        why_asked_en="Statutory eligibility criterion for state social security and destitute pension schemes.",
        why_asked_hi="राज्य सामाजिक सुरक्षा और निराश्रित पेंशन योजनाओं के लिए वैधानिक पात्रता मानदंड।",
        sensitivity="sensitive",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_destitute": QuestionMetadata(
        fact_key="applicant.is_destitute",
        component_type="boolean",
        label_en="Do you have certified destitute or indigent status?",
        label_hi="क्या आपके पास प्रमाणित निराश्रित या निर्धन व्यक्ति का दर्जा है?",
        why_asked_en="Qualifies severely indigent citizens for state subsistence support and essential aid.",
        why_asked_hi="अत्यधिक निर्धन नागरिकों को राज्य निर्वाह सहायता और आवश्यक सहायता के लिए योग्य बनाता है।",
        sensitivity="sensitive",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_head_or_earning_member": QuestionMetadata(
        fact_key="applicant.is_head_or_earning_member",
        component_type="boolean",
        label_en="Are you designated as the head of household or principal earning breadwinner?",
        label_hi="क्या आप परिवार के मुखिया या मुख्य कमाने वाले सदस्य हैं?",
        why_asked_en="Required under group life insurance schemes such as Aam Aadmi Bima Yojana (AABY).",
        why_asked_hi="आम आदमी बीमा योजना (AABY) जैसी समूह जीवन बीमा योजनाओं के तहत आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.has_active_education_loan": QuestionMetadata(
        fact_key="applicant.has_active_education_loan",
        component_type="boolean",
        label_en="Do you have an active sanctioned education loan from a scheduled bank?",
        label_hi="क्या आपके पास किसी अनुसूचित बैंक से स्वीकृत सक्रिय शिक्षा ऋण है?",
        why_asked_en="Required to assess eligibility for Central Sector Interest Subsidy (CSIS) schemes.",
        why_asked_hi="केंद्रीय क्षेत्र ब्याज सब्सिडी (CSIS) योजनाओं की पात्रता जांचने के लिए आवश्यक।",
        sensitivity="financial",
        scope="applicant",
        can_skip=False
    ),
    "financial.education_loan_amount": QuestionMetadata(
        fact_key="financial.education_loan_amount",
        component_type="number",
        label_en="What is the sanctioned principal amount of your education loan?",
        label_hi="आपके शिक्षा ऋण की स्वीकृत मूल राशि कितनी है?",
        why_asked_en="Assesses compliance with education loan interest subsidy ceilings.",
        why_asked_hi="शिक्षा ऋण ब्याज सब्सिडी की अधिकतम सीमाओं के अनुपालन का मूल्यांकन करता है।",
        unit="INR",
        sensitivity="financial",
        scope="applicant",
        can_skip=False
    ),
    "applicant.owns_cattle": QuestionMetadata(
        fact_key="applicant.owns_cattle",
        component_type="boolean",
        label_en="Do you or your household own cattle, cows, buffaloes, or dairy animals?",
        label_hi="क्या आपके या आपके परिवार के पास मवेशी, गाय, भैंस या दुधारू पशु हैं?",
        why_asked_en="Qualifies rural households for livestock vaccination, cattle insurance, and dairy subsidies.",
        why_asked_hi="ग्रामीण परिवारों को पशुधन टीकाकरण, मवेशी बीमा और डेयरी सब्सिडी के लिए योग्य बनाता है।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    ),
    "applicant.is_registered_worker": QuestionMetadata(
        fact_key="applicant.is_registered_worker",
        component_type="boolean",
        label_en="Are you registered with any state unorganized labour or social security board?",
        label_hi="क्या आप किसी राज्य असंगठित श्रमिक या सामाजिक सुरक्षा बोर्ड में पंजीकृत हैं?",
        why_asked_en="Unlocks social security stipends, toolkit assistance, and occupational health benefits.",
        why_asked_hi="सामाजिक सुरक्षा वजीफे, टूलकिट सहायता और व्यावसायिक स्वास्थ्य लाभ प्राप्त करने के लिए आवश्यक।",
        sensitivity="normal",
        scope="applicant",
        can_skip=False
    )
}

CATALOGUE_ALIASES: Dict[str, str] = {
    "location.area_type": "location.urban_rural",
    "person.income": "household.annual_income",
    "student.family_annual_income": "household.annual_income",
    "beneficiary.has_disability_certificate": "health.has_disability",
    "applicant.is_single_girl_child": "person.is_single_girl_child",
    "person.is_student": "student.is_enrolled",
    "applicant.is_student": "student.is_enrolled",
    "scheme.owns_cattle": "applicant.owns_cattle",
    "scheme.is_registered_worker": "applicant.is_registered_worker",
    "applicant.is_widow": "person.is_widow",
    "applicant.is_widow_or_destitute": "person.is_widow_or_destitute"
}

def get_question_metadata(fact_key: str) -> Optional[QuestionMetadata]:
    """Retrieves full presentation metadata for a canonical fact key."""
    if fact_key in QUESTION_METADATA_CATALOGUE:
        return QUESTION_METADATA_CATALOGUE[fact_key]

    # Check alias
    if fact_key in CATALOGUE_ALIASES:
        alias_key = CATALOGUE_ALIASES[fact_key]
        if alias_key in QUESTION_METADATA_CATALOGUE:
            base = QUESTION_METADATA_CATALOGUE[alias_key]
            # Return copy adapted for fact_key
            return QuestionMetadata(
                fact_key=fact_key,
                component_type=base.component_type,
                label_en=base.label_en,
                label_hi=base.label_hi,
                help_text_en=base.help_text_en,
                help_text_hi=base.help_text_hi,
                why_asked_en=base.why_asked_en,
                why_asked_hi=base.why_asked_hi,
                allowed_values=base.allowed_values,
                unit=base.unit,
                min_value=base.min_value,
                max_value=base.max_value,
                sensitivity=base.sensitivity,
                scope=base.scope,
                can_skip=base.can_skip
            )

    # Dynamic fallback if in fact catalogue
    fact_def = FACT_CATALOGUE.get(fact_key)
    if fact_def:
        comp_type = "number" if fact_def.type in ("integer", "float") else ("boolean" if fact_def.type == "boolean" else "text")
        clean_title = fact_key.split(".")[-1].replace("_", " ").title()
        return QuestionMetadata(
            fact_key=fact_key,
            component_type=comp_type,
            label_en=f"What is your {clean_title}?",
            label_hi=f"आपका {clean_title} क्या है?",
            why_asked_en="This information helps check qualification for relevant government schemes.",
            why_asked_hi="यह जानकारी प्रासंगिक सरकारी योजनाओं के लिए पात्रता जांचने में मदद करती है।",
            unit=fact_def.unit,
            sensitivity=fact_def.sensitivity, # type: ignore
            can_skip=True
        )

    # Clean synthesis fallback for statutory facts not in registry
    last_part = fact_key.split(".")[-1].lower()
    is_bool = any(prefix in last_part for prefix in ["has_", "is_", "owns_", "meets_", "exceeds_", "covered_", "lacks_", "pays_", "completed_"])
    is_num = any(sub in last_part for prefix in ["income", "amount", "size", "pct", "percentage", "count", "years", "grade"] for sub in [prefix])
    comp_type = "boolean" if is_bool else ("number" if is_num else "text")
    clean_words = fact_key.split(".")[-1].replace("_", " ").title()

    label_en = f"Do you / Does your household {clean_words.lower()}?" if is_bool else f"What is your {clean_words}?"
    label_hi = f"क्या आपके पास / क्या आप {clean_words} हैं?" if is_bool else f"आपका {clean_words} क्या है?"

    return QuestionMetadata(
        fact_key=fact_key,
        component_type=comp_type,
        label_en=label_en,
        label_hi=label_hi,
        why_asked_en="Required to determine statutory qualification for specific government schemes.",
        why_asked_hi="विशिष्ट सरकारी योजनाओं के लिए वैधानिक पात्रता निर्धारित करने के लिए आवश्यक।",
        sensitivity="normal",
        can_skip=True
    )
