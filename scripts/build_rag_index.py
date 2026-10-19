"""
Script to build the RAG Index for verified citizen schemes in data/civix.db.
Executes RagIndexingPipeline, verifies is_rag_certified gate, and tests search.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

from services.core.database import SessionLocal
from services.core.rag.fts_manager import FtsManager
from services.core.rag.indexer import RagIndexingPipeline
from services.core.rag.retriever import HybridRetriever
from services.core.rag.normalizer import MultilingualQueryNormalizer

def main():
    db = SessionLocal()
    fts = FtsManager(PROJECT_ROOT / "data" / "civix.db")

    pipeline = RagIndexingPipeline(db, fts)
    result = pipeline.run_indexing()

    print(f"Indexing Status: {result['status']}")
    print(f"Schemes Indexed ({result['schemes_indexed_count']}):")
    for s in result['indexed_schemes']:
        print(f"  ✔ {s}")
    if result['rejected_schemes']:
        print(f"Rejected Schemes ({len(result['rejected_schemes'])}):")
        for r_id, r_reason in result['rejected_schemes']:
            print(f"  ⛔ {r_id}: {r_reason}")
    print(f"Total Chunks Created: {result['total_chunks_created']}")

    # Quick search verification
    print("\n--- Testing Hybrid Retrieval ---")
    retriever = HybridRetriever(db, fts)
    retriever.refresh_dense_index()

    test_queries = [
        "What is the amount in PM-KISAN?",
        "पीएम किसान में कितने पैसे मिलते हैं?",
        "svanidhi restructured tranches loan amount 2025",
        "ujjwala 2.0 free stove and first refill",
        "pm vishwakarma 18 trades and toolkit stipend",
        "Tell me about Ayushman Bharat" # Unverified scheme test
    ]

    for q in test_queries:
        norm = MultilingualQueryNormalizer.normalize_query(q)
        hits = retriever.retrieve(norm["search_query"], target_scheme_id=norm["primary_scheme_id"], top_k=2)
        print(f"\nQuery: '{q}' [Lang: {norm['detected_language']}]")
        if hits:
            for h in hits:
                print(f"  -> [{h['source_citation']}] (Score: {h['rrf_score']:.4f})")
                print(f"     Excerpt: {h['content'][:110]}...")
        else:
            print("  -> ZERO HITS (Filtered by certification gate or no evidence)")

    db.close()

if __name__ == "__main__":
    main()
