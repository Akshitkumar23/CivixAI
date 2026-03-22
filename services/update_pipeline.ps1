# CivixAI Automated Weekly Update Pipeline
# This script automatically downloads the latest schemes, adds financial schemes, fixes broken links, enriches them, runs the ML synthetic dataset generator, and updates the models.
$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "Starting Elite CivixAI Auto Update Pipeline..."
Write-Host "=========================================="

$projectDir = "C:\Users\akshi\Desktop\CivixAI"
Set-Location $projectDir

Write-Host "[1/9] Running Scheme Scraper (DbtBharat/StandUpIndia)..."
python services/scraper/scrape_schemes.py

Write-Host "[2/9] Injecting Elite Financial/Bank Schemes & Loans..."
python services/scraper/scrape_financials.py

Write-Host "[3/9] Fixing Private Financial URLs..."
python scripts/fix_financial_links.py

Write-Host "[4/9] Applying Master Heuristic Link Fixer (Resolving 404s/Redirects)..."
python scripts/master_link_fixer.py

Write-Host "[5/9] Running Enrichment Rules (P3 ML Markers)..."
python services/scraper/enrich_schemes.py

Write-Host "[6/9] Generating Synthetic Users Benchmark Dataset..."
python services/ml/generate_synthetic_dataset.py

Write-Host "[7/9] Retraining Eligibility XGBoost/CatBoost Models..."
python services/ml/train_eligibility_model.py

Write-Host "[8/9] Retraining Benefit Score (Deep Ranking) System..."
python services/ml/train_benefit_model.py

Write-Host "[9/9] Generating ML Evaluation Report..."
python services/ml/evaluate_models.py > data/logs/evaluate.txt

Write-Host "=========================================="
Write-Host "✅ CivixAI Pro-Level Data & ML Pipeline completed successfully!"
Write-Host "=========================================="
