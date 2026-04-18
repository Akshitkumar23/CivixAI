import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, List
import hashlib

class DataEngine:
    def __init__(self, csv_path: Path, db_path: Path):
        self.csv_path = csv_path
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def compute_hash(self) -> str:
        """Computes hash of CSV for change detection."""
        return hashlib.md5(self.csv_path.read_bytes()).hexdigest() if self.csv_path.exists() else ""

    def sync_to_db(self, force: bool = False):
        """
        Synchronizes CSV data into a local SQLite database for production-level throughput.
        """
        if not self.csv_path.exists():
            print(f"Error: {self.csv_path} not found.")
            return

        current_hash = self.compute_hash()
        
        # Simple change detection
        hash_file = self.db_path.parent / ".csv_hash"
        if not force and hash_file.exists() and hash_file.read_text() == current_hash:
            print("Data already synced. Use force=True to restart.")
            return

        print(f"Syncing {self.csv_path} to {self.db_path}...")
        df = pd.read_csv(self.csv_path)
        
        # Clean data
        df = df.where(pd.notnull(df), None)
        
        conn = sqlite3.connect(self.db_path)
        df.to_sql("schemes", conn, if_exists="replace", index=False)
        conn.close()
        
        hash_file.write_text(current_hash)
        print("Sync complete.")

    def search_schemes(self, query: str) -> List[dict]:
        """SQL-based similarity search (fallback if no vector DB)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Basic text search
        cur.execute("SELECT * FROM schemes WHERE scheme_name LIKE ? OR benefit_description LIKE ?", (f"%{query}%", f"%{query}%"))
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results

if __name__ == "__main__":
    APP_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = APP_ROOT.parent / "data"
    
    engine = DataEngine(
        csv_path=DATA_DIR / "master" / "schemes_master.csv",
        db_path=DATA_DIR / "master" / "civix_prod.db"
    )
    engine.sync_to_db()
