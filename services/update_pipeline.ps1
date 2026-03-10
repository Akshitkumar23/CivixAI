# CivixAI Automated Weekly Update Pipeline
# This script automatically downloads the latest schemes, enriches them, runs the ML synthetic dataset generator, and updates the models.
$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "Starting CivixAI Auto Update Pipeline..."
Write-Host "=========================================="

$projectDir = "C:\Users\akshi\Desktop\CivixAI"
Set-Location $projectDir

Write-Host "[1/5] Running Scraper..."
python services/scraper/scrape_schemes.py

Write-Host "[2/5] Running Enrichment Rules..."
python services/scraper/enrich_schemes.py

Write-Host "[3/5] Generating ML Dataset (Synthetic Users)..."
python services/ml/generate_synthetic_dataset.py

Write-Host "[4/5] Retraining Eligibility Model..."
python services/ml/train_eligibility_model.py

Write-Host "[5/5] Retraining Benefit Score Model..."
python services/ml/train_benefit_model.py

Write-Host "[6/6] Writing ML Evaluation Report..."
python services/ml/evaluate_models.py > data/logs/evaluate.txt

Write-Host "=========================================="
Write-Host "✅ CivixAI Data & ML Pipeline completed successfully!"
Write-Host "=========================================="
