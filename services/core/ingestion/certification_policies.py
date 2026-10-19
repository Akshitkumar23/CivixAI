"""
CivixAI Declarative Certification Policies Engine
Phase 3.8 / 3.9 Architecture

Dynamically loads, validates, and manages declarative scheme completeness and certification policies from JSON.
Provides unified statutory exclusion validation, policy versioning, and lifecycle management.
Replaces hardcoded Python registrations while preserving 100% backward compatibility.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger("civix.ingestion.certification_policies")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "data" / "certification_policies.json"


class PolicyValidationError(ValueError):
    """Raised when policy JSON schema or structure fails validation."""
    pass


class CompletenessPolicy:
    """
    Declarative, data-driven completeness policy for schemes.
    Defines required statutory exclusion facts, patterns, and custom validators.
    """
    def __init__(
        self,
        required_exclusion_facts: Optional[Union[Set[str], List[str]]] = None,
        required_exclusion_patterns: Optional[List[str]] = None,
        custom_validator: Optional[Callable[[List[Any]], List[str]]] = None,
        policy_id: Optional[str] = None,
        policy_version: Optional[str] = "1.0.0",
        scheme_id: Optional[str] = None,
        canonical_name: Optional[str] = None,
        description: Optional[str] = None,
        documentation: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        required_inclusion_facts: Optional[Union[Set[str], List[str]]] = None,
        mandatory_rule_scopes: Optional[List[str]] = None,
        effective_date: Optional[str] = None,
        is_active: bool = True
    ):
        self.required_exclusion_facts: Set[str] = (
            set(required_exclusion_facts) if required_exclusion_facts else set()
        )
        self.required_exclusion_patterns: List[str] = (
            list(required_exclusion_patterns) if required_exclusion_patterns else []
        )
        self.custom_validator = custom_validator
        self.policy_id = policy_id
        self.policy_version = policy_version or "1.0.0"
        self.scheme_id = scheme_id
        self.canonical_name = canonical_name
        self.description = description or ""
        self.documentation = documentation or ""
        self.aliases: List[str] = list(aliases) if aliases else []
        self.required_inclusion_facts: Set[str] = (
            set(required_inclusion_facts) if required_inclusion_facts else set()
        )
        self.mandatory_rule_scopes: List[str] = (
            list(mandatory_rule_scopes) if mandatory_rule_scopes else []
        )
        self.effective_date = effective_date
        self.is_active = is_active

    def evaluate(self, scheme_id: str, rules: List[Any]) -> List[str]:
        findings = []
        exclusion_rules = [
            r for r in rules
            if getattr(r, "rule_scope", "") in ("exclusion", "exception")
        ]
        exclusion_facts = {getattr(r, "fact_key", "") for r in exclusion_rules}

        # 1. Statutory exclusion facts validation
        if self.required_exclusion_facts:
            missing = self.required_exclusion_facts - exclusion_facts
            if missing:
                findings.append(
                    f"Scheme '{scheme_id}' missing mandatory statutory exclusion rules for: {missing}"
                )

        # 2. Exclusion pattern validation (checks fact_key and reason_code)
        for pattern in self.required_exclusion_patterns:
            pattern_lower = pattern.lower()
            matched = any(
                pattern in f or pattern_lower in f.lower()
                for f in exclusion_facts
            ) or any(
                pattern_lower in getattr(r, "reason_code", "").lower()
                for r in exclusion_rules
            )
            if not matched:
                findings.append(
                    f"Scheme '{scheme_id}' missing mandatory exclusion rule matching pattern: '{pattern}'"
                )

        # 3. Custom validator callback if provided
        if self.custom_validator:
            findings.extend(self.custom_validator(rules))

        return findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "scheme_id": self.scheme_id,
            "canonical_name": self.canonical_name,
            "policy_version": self.policy_version,
            "description": self.description,
            "documentation": self.documentation,
            "aliases": self.aliases,
            "required_exclusion_facts": sorted(list(self.required_exclusion_facts)),
            "required_exclusion_patterns": self.required_exclusion_patterns,
            "required_inclusion_facts": sorted(list(self.required_inclusion_facts)),
            "mandatory_rule_scopes": self.mandatory_rule_scopes,
            "effective_date": self.effective_date,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return (
            f"<CompletenessPolicy scheme={self.scheme_id} version={self.policy_version} "
            f"facts={len(self.required_exclusion_facts)} patterns={len(self.required_exclusion_patterns)}>"
        )


class CertificationPolicyManager:
    """
    Dynamic Certification Policy Manager for CivixAI.
    Loads, validates, caches, and queries scheme completeness policies from
    data/certification_policies.json with full runtime management and backward compatibility.
    """
    _instance: Optional["CertificationPolicyManager"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        policy_file_path: Optional[Union[str, Path]] = None,
        auto_load: bool = True
    ):
        if policy_file_path:
            self.policy_file_path = Path(policy_file_path)
        else:
            env_path = os.getenv("CERTIFICATION_POLICIES_PATH")
            if env_path:
                self.policy_file_path = Path(env_path)
            else:
                self.policy_file_path = DEFAULT_POLICY_PATH

        self.schema_version: str = "1.0.0"
        self.policy_framework_version: str = "3.8.0"
        self.last_updated: Optional[str] = None
        self.description: str = ""
        self._policies: Dict[str, CompletenessPolicy] = {}
        self._alias_map: Dict[str, str] = {}
        self._raw_config: Dict[str, Any] = {}

        if auto_load and self.policy_file_path.exists():
            self.load_policies()

    @classmethod
    def get_instance(
        cls,
        policy_file_path: Optional[Union[str, Path]] = None,
        force_reload: bool = False
    ) -> "CertificationPolicyManager":
        """
        Thread-safe singleton accessor.
        """
        with cls._lock:
            if cls._instance is None or force_reload:
                cls._instance = cls(policy_file_path=policy_file_path, auto_load=True)
            elif policy_file_path and Path(policy_file_path) != cls._instance.policy_file_path:
                cls._instance.policy_file_path = Path(policy_file_path)
                cls._instance.load_policies()
            return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets the singleton instance (useful for test isolation)."""
        with cls._lock:
            cls._instance = None

    def load_policies(self, file_path: Optional[Union[str, Path]] = None) -> Dict[str, CompletenessPolicy]:
        """
        Loads and validates certification policies from a JSON file.
        """
        target_path = Path(file_path) if file_path else self.policy_file_path
        if not target_path.exists():
            raise FileNotFoundError(f"Certification policies configuration file not found at: {target_path}")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise PolicyValidationError(f"Malformed JSON in certification policies file '{target_path}': {e}") from e

        # Validate schema structure
        self.validate_configuration(config)

        self._raw_config = config
        self.schema_version = config.get("schema_version", config.get("version", "1.0.0"))
        self.policy_framework_version = config.get("policy_framework_version", "1.0.0")
        self.last_updated = config.get("last_updated")
        self.description = config.get("description", "")

        policies_data = config.get("policies", {})
        loaded_policies: Dict[str, CompletenessPolicy] = {}
        alias_map: Dict[str, str] = {}

        items = (
            policies_data.items()
            if isinstance(policies_data, dict)
            else [(p.get("scheme_id", str(i)), p) for i, p in enumerate(policies_data)]
        )

        for key, pdata in items:
            scheme_id = pdata.get("scheme_id", key)
            policy = CompletenessPolicy(
                required_exclusion_facts=pdata.get("required_exclusion_facts"),
                required_exclusion_patterns=pdata.get("required_exclusion_patterns"),
                policy_id=pdata.get("policy_id"),
                policy_version=pdata.get("policy_version", "1.0.0"),
                scheme_id=scheme_id,
                canonical_name=pdata.get("canonical_name"),
                description=pdata.get("description"),
                documentation=pdata.get("documentation"),
                aliases=pdata.get("aliases"),
                required_inclusion_facts=pdata.get("required_inclusion_facts"),
                mandatory_rule_scopes=pdata.get("mandatory_rule_scopes"),
                effective_date=pdata.get("effective_date"),
                is_active=pdata.get("is_active", True)
            )

            canonical_key = scheme_id.lower().strip()
            loaded_policies[canonical_key] = policy
            alias_map[canonical_key] = canonical_key

            # Map aliases with normalization
            for alias in policy.aliases:
                normalized_alias = alias.lower().strip()
                alias_map[normalized_alias] = canonical_key
                alias_map[normalized_alias.replace("-", "_")] = canonical_key
                alias_map[normalized_alias.replace("_", "-")] = canonical_key

            # Normalize canonical key
            alias_map[canonical_key.replace("-", "_")] = canonical_key
            alias_map[canonical_key.replace("_", "-")] = canonical_key

        self._policies = loaded_policies
        self._alias_map = alias_map
        logger.debug("Loaded %d certification policies from %s", len(loaded_policies), target_path)
        return self._policies

    @staticmethod
    def validate_configuration(config: Any) -> Tuple[bool, List[str]]:
        """
        Validates the structure of a certification policies configuration dict.
        Raises PolicyValidationError if invalid.
        """
        errors = []
        if not isinstance(config, dict):
            errors.append("Configuration root must be a JSON object (dict)")
            raise PolicyValidationError(errors[0])

        if "policies" not in config:
            errors.append("Missing required root property 'policies'")

        policies = config.get("policies")
        if not isinstance(policies, (dict, list)):
            errors.append("Property 'policies' must be a dictionary or list")

        if isinstance(policies, dict):
            for pkey, pval in policies.items():
                if not isinstance(pval, dict):
                    errors.append(f"Policy '{pkey}' must be a dictionary")
                    continue
                if "policy_version" not in pval and "version" not in pval:
                    errors.append(f"Policy '{pkey}' missing required 'policy_version'")
                if "required_exclusion_facts" in pval and not isinstance(pval["required_exclusion_facts"], list):
                    errors.append(f"Policy '{pkey}' 'required_exclusion_facts' must be a list")
                if "required_exclusion_patterns" in pval and not isinstance(pval["required_exclusion_patterns"], list):
                    errors.append(f"Policy '{pkey}' 'required_exclusion_patterns' must be a list")
        elif isinstance(policies, list):
            for i, pval in enumerate(policies):
                if not isinstance(pval, dict):
                    errors.append(f"Policy at index {i} must be a dictionary")
                    continue
                if "scheme_id" not in pval:
                    errors.append(f"Policy at index {i} missing required 'scheme_id'")
                if "policy_version" not in pval and "version" not in pval:
                    errors.append(f"Policy at index {i} missing required 'policy_version'")

        if errors:
            raise PolicyValidationError(f"Policy validation failed: {'; '.join(errors)}")
        return True, []

    def reload_policies(self) -> Dict[str, CompletenessPolicy]:
        """Forces reload of policies from disk."""
        return self.load_policies(self.policy_file_path)

    def save_policies(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Serializes current in-memory policies back to JSON file."""
        target_path = Path(file_path) if file_path else self.policy_file_path
        data = {
            "$schema": "https://civix.ai/schemas/certification_policies.v1.json",
            "schema_version": self.schema_version,
            "policy_framework_version": self.policy_framework_version,
            "last_updated": self.last_updated,
            "description": self.description,
            "policies": {
                k: v.to_dict() for k, v in self._policies.items()
            }
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_policy(self, scheme_id: str) -> Optional[CompletenessPolicy]:
        """
        Resolves policy for a scheme using exact key, alias, normalized name, or substring.
        Maintains backward compatibility with legacy registry lookups.
        """
        if not scheme_id:
            return None

        cleaned_id = scheme_id.lower().strip()

        # 1. Direct key match
        if cleaned_id in self._policies:
            return self._policies[cleaned_id]

        # 2. Alias lookup
        if cleaned_id in self._alias_map:
            canonical = self._alias_map[cleaned_id]
            if canonical in self._policies:
                return self._policies[canonical]

        # 3. Normalized variation (- vs _)
        with_underscore = cleaned_id.replace("-", "_")
        if with_underscore in self._alias_map:
            return self._policies.get(self._alias_map[with_underscore])
        with_hyphen = cleaned_id.replace("_", "-")
        if with_hyphen in self._alias_map:
            return self._policies.get(self._alias_map[with_hyphen])

        # 4. Containment / substring matching for registered aliases (backward compatibility)
        for alias, canonical in self._alias_map.items():
            if alias and (alias in cleaned_id or cleaned_id in alias):
                return self._policies.get(canonical)

        for key, policy in self._policies.items():
            if key in cleaned_id or cleaned_id in key:
                return policy

        return None

    def register_policy(
        self,
        scheme_id_or_alias: str,
        policy: CompletenessPolicy,
        aliases: Optional[List[str]] = None,
        policy_version: Optional[str] = None,
        documentation: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Dynamically registers or overrides a policy in memory.
        """
        canonical_key = scheme_id_or_alias.lower().strip()
        policy.scheme_id = policy.scheme_id or scheme_id_or_alias
        if policy_version:
            policy.policy_version = policy_version
        if documentation:
            policy.documentation = documentation
        if description:
            policy.description = description
        if aliases:
            policy.aliases.extend([a for a in aliases if a not in policy.aliases])

        self._policies[canonical_key] = policy
        self._alias_map[canonical_key] = canonical_key
        self._alias_map[canonical_key.replace("-", "_")] = canonical_key
        self._alias_map[canonical_key.replace("_", "-")] = canonical_key

        for alias in policy.aliases:
            norm = alias.lower().strip()
            self._alias_map[norm] = canonical_key
            self._alias_map[norm.replace("-", "_")] = canonical_key
            self._alias_map[norm.replace("_", "-")] = canonical_key

    def unregister_policy(self, scheme_id_or_alias: str) -> bool:
        """Removes a policy from memory."""
        cleaned = scheme_id_or_alias.lower().strip()
        canonical = self._alias_map.get(cleaned, cleaned)
        if canonical in self._policies:
            del self._policies[canonical]
            # Clean alias map
            keys_to_remove = [k for k, v in self._alias_map.items() if v == canonical]
            for k in keys_to_remove:
                del self._alias_map[k]
            return True
        return False

    def list_policies(self) -> List[Dict[str, Any]]:
        """Returns metadata dictionaries for all active policies."""
        return [p.to_dict() for p in self._policies.values()]

    def get_policy_metadata(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata dictionary for a specific scheme policy."""
        policy = self.get_policy(scheme_id)
        return policy.to_dict() if policy else None

    def get_version(self, scheme_id: str) -> Optional[str]:
        """Returns the version of a scheme's certification policy."""
        policy = self.get_policy(scheme_id)
        return policy.policy_version if policy else None

    def get_documentation(self, scheme_id: str) -> Optional[str]:
        """Returns documentation reference for a scheme's policy."""
        policy = self.get_policy(scheme_id)
        return policy.documentation if policy else None

    def evaluate(self, scheme_id: str, rules: List[Any]) -> List[str]:
        """Evaluates rules against the policy for the given scheme."""
        policy = self.get_policy(scheme_id)
        if policy:
            return policy.evaluate(scheme_id, rules)
        return []

    def get_policies_map(self) -> Dict[str, CompletenessPolicy]:
        """Returns direct reference to policies dictionary."""
        return self._policies
