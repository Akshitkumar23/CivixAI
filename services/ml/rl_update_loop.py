import pandas as pd
import json
import os
from pathlib import Path
from collections import defaultdict

# Paths
ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_CSV = ROOT / "data" / "master" / "schemes_master.csv"
LOG_PATH = ROOT / "services" / "ml_api" / "logs" / "shadow_logs.jsonl"

def process_feedback():
    if not LOG_PATH.exists():
        print("No feedback logs found yet.")
        return

    print("--- Reinforcement Learning Update Loop (#22) ---")
    
    # 1. Aggregating Rewards
    # Reward: Liked/Applied = +1, Disliked = -1
    rewards = defaultdict(float)
    total_events = 0
    
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                scheme_id = event.get("scheme_id")
                # event_type can be shadow (request) or feedback (click)
                if event.get("event_type") == "click_feedback":
                    accepted = event.get("accepted", 0)
                    reward = 1.0 if accepted == 1 else -1.0
                    rewards[scheme_id] += reward
                    total_events += 1
            except:
                continue
                
    if total_events == 0:
        print("No new click feedback events to process.")
        return

    # 2. Updating CSV
    df = pd.read_csv(MASTER_CSV)
    
    # Ensure popularity_score exists
    if "popularity_score" not in df.columns:
        df["popularity_score"] = 5.0
    
    df["popularity_score"] = df["popularity_score"].fillna(5.0)
    
    updated_count = 0
    for scheme_id, total_reward in rewards.items():
        mask = df["scheme_id"] == scheme_id
        if mask.any():
            # Update formula: New score influenced by reward
            # Scale reward to be small per event to avoid wild swings
            learning_rate = 0.5
            current_score = df.loc[mask, "popularity_score"].iloc[0]
            new_score = current_score + (total_reward * learning_rate)
            
            # Clip between 1.0 and 10.0
            new_score = max(1.0, min(10.0, new_score))
            df.loc[mask, "popularity_score"] = new_score
            updated_count += 1
            print(f"Updated {scheme_id}: {current_score:.2f} -> {new_score:.2f} (Reward: {total_reward})")

    df.to_csv(MASTER_CSV, index=False)
    print(f"RL Update Complete: {updated_count} schemes updated based on {total_events} events.")
    
    # Optional: Clear logs after processing to avoid double counting? 
    # Or keep them and use timestamps. For simplicity, we'll keep them 
    # but in a real system we'd use a 'processed' watermark.

if __name__ == "__main__":
    process_feedback()
