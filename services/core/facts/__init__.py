from .registry import FACT_CATALOGUE, FactDefinition, normalize_profile_to_facts
from .dependencies import extract_facts_from_ast, FactDependencyEngine
from .resolver import (
    resolve_fact, FactResolution, get_canonical_key, get_equivalent_representations
)

__all__ = [
    "FACT_CATALOGUE", "FactDefinition", "normalize_profile_to_facts",
    "extract_facts_from_ast", "FactDependencyEngine",
    "resolve_fact", "FactResolution", "get_canonical_key", "get_equivalent_representations"
]

