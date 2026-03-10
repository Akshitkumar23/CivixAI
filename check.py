import requests; r=requests.post('http://127.0.0.1:8001/api/check-eligibility', json={'age': 30, 'income': 250000, 'state': 'Goa', 'caste': 'general', 'occupation': 'employed'}); data=r.json(); loans = [];
for s in data.get('eligible_schemes', []):
  print(s)

