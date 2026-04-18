import requests
import json

def test_recommendations():
    url = "http://localhost:8000/api/recommend"
    
    # 1. Profile: Low-income student from Maharashtra
    profile_student = {
        "age": 20,
        "annual_income": 150000,
        "state": "Maharashtra",
        "category": "SC",
        "occupation": "student",
        "gender": "male"
    }

    # 2. Profile: Middle-income farmer from Uttar Pradesh
    profile_farmer = {
        "age": 45,
        "annual_income": 250000,
        "state": "Uttar Pradesh",
        "category": "OBC",
        "occupation": "farmer",
        "gender": "male",
        "has_land": True
    }

    print("--- TESTING STUDENT PROFILE ---")
    try:
        res1 = requests.post(url, json=profile_student)
        res1.raise_for_status()
        data1 = res1.json()
        print(f"Total Matches: {len(data1['ranked_schemes'])}")
        print(f"Top 3 for Student: {[s['name'] for s in data1['ranked_schemes'][:3]]}")
    except Exception as e:
        print(f"FAIL: {e}")

    print("\n--- TESTING FARMER PROFILE ---")
    try:
        res2 = requests.post(url, json=profile_farmer)
        res2.raise_for_status()
        data2 = res2.json()
        print(f"Total Matches: {len(data2['ranked_schemes'])}")
        print(f"Top 3 for Farmer: {[s['name'] for s in data2['ranked_schemes'][:3]]}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test_recommendations()
