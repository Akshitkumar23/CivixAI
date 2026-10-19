"""
Questionnaire Progress Calculator
Computes exact dependency-derived questionnaire progress.
Strictly avoids static 30-field formulas or false precision.
"""
from typing import Set
from .models import QuestionnaireProgress

def calculate_progress(
    answered_facts_count: int,
    unresolved_relevant_facts: Set[str],
    eligible_schemes_count: int,
    needs_info_schemes_count: int
) -> QuestionnaireProgress:
    """
    Progress is strictly defined as:
    answered_count / (answered_count + remaining_relevant_unresolved_facts) * 100
    """
    remaining_count = len(unresolved_relevant_facts)
    total_relevant = answered_facts_count + remaining_count

    if total_relevant == 0:
        pct = 100.0
    else:
        pct = round((answered_facts_count / total_relevant) * 100, 1)

    return QuestionnaireProgress(
        answered_count=answered_facts_count,
        unresolved_relevant_facts_count=remaining_count,
        estimated_remaining_questions=min(remaining_count, 12),
        progress_pct=min(100.0, max(0.0, pct)),
        current_eligible_schemes_count=eligible_schemes_count,
        current_needs_info_schemes_count=needs_info_schemes_count
    )
