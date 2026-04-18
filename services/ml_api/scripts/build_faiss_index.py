import os
import sys
import argparse
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Add ml_api to path
ml_api_dir = Path(__file__).resolve().parent.parent
if str(ml_api_dir) not in sys.path:
    sys.path.insert(0, str(ml_api_dir))

import pandas as pd
from agents.retrieval_agent import RetrievalAgent

def main():
    parser = argparse.ArgumentParser(description="Build FAISS vector database for CivixAI schemes.")
    parser.add_argument("--csv_path", type=str, default=str(root_dir / "data" / "master" / "schemes_master.csv"), help="Path to schemes_master.csv")
    parser.add_argument("--index_out", type=str, default=str(root_dir / "data" / "master" / "schemes.index"), help="Path to save the generated FAISS index")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"Error: Schemes master file not found at {args.csv_path}")
        sys.exit(1)
        
    print(f"Loading schemes from {args.csv_path}...")
    df = pd.read_csv(args.csv_path)
    
    # Fill nan to prevent errors
    df["benefit_description"] = df.get("benefit_description", "").fillna("No description available.")
    df["scheme_name"] = df.get("scheme_name", "").fillna("Unknown Scheme")
    
    scheme_texts = (df["scheme_name"] + ". " + df["benefit_description"]).tolist()
    scheme_ids = df["scheme_id"].astype(str).tolist()
    
    print(f"Found {len(df)} schemes. Building FAISS index...")
    try:
        # Build index
        RetrievalAgent.build_index(
            scheme_texts=scheme_texts,
            scheme_ids=scheme_ids,
            output_path=args.index_out
        )
        print(f"[Done] FAISS index built successfully and saved to {args.index_out}")
    except Exception as e:
        print(f"[Error] Failed to build FAISS index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
