Scraper usage

1) Install deps:
   pip install -r services/scraper/requirements.txt

2) Run:
   python services/scraper/scrape_schemes.py

3) Output:
   data/master/schemes_master.csv

Notes:
- The scraper respects robots.txt. If robots.txt blocks access, it will skip.
- For data.gov.in, set DATAGOVINDIA_API_KEY and add a resource_id in services/scraper/sources.json.
- Add more sources into services/scraper/sources.json to reach 100+ schemes from multiple websites.

Auto-run (Windows Task Scheduler):
- powershell -ExecutionPolicy Bypass -File services/scraper/schedule_task.ps1 -WorkingDir "C:\Users\akshi\Desktop\CivixAI" -TaskName "CivixAI_SchemeScraper" -Schedule DAILY -Time "02:00"

Current default sources:
- https://dbtbharat.gov.in/central-scheme/list
- https://www.dbtharyana.gov.in/scheme/schemelist
- https://pandr.py.gov.in/restructured-css-list
- https://dge.gov.in/dge/schemes_programmes
