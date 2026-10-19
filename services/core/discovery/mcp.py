"""
CIVIXAI — GOVERNMENT DISCOVERY MCP CONNECTOR LAYER
=================================================
Model Context Protocol (MCP) data-access tools for external tools and agents.
Provides read-only query and discovery capabilities across the national programme universe.

CRITICAL INVARIANT:
MCP is EXCLUSIVELY a data-access/discovery interface.
MCP MUST NOT decide:
- eligibility
- certification
- governance disposition
- benefit legality
- programme validity
"""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from services.core.database.session import SessionLocal
from services.core.discovery.models import ProgrammeDiscovery
from services.core.discovery.registry import GovernmentProgrammeSourceRegistry


class GovernmentDiscoveryMCP:
    """
    Standard MCP discovery interface exposing read-only queries over the
    CIVIXAI national government programme universe.
    """

    def __init__(self, db_session: Optional[Session] = None):
        if db_session is not None:
            self.session: Session = db_session
            self._owns_session = False
        else:
            self.session: Session = SessionLocal()
            self._owns_session = True
        self.registry = GovernmentProgrammeSourceRegistry()

    def close(self):
        if self._owns_session and self.session:
            self.session.close()

    def search_programmes(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        programme_type: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Full-text discovery search across programme names, descriptions, and authorities.
        """
        q = f"%{query}%"
        filters = [
            or_(
                ProgrammeDiscovery.canonical_name.ilike(q),
                ProgrammeDiscovery.description.ilike(q),
                ProgrammeDiscovery.authority.ilike(q),
                ProgrammeDiscovery.ministry.ilike(q),
                ProgrammeDiscovery.category.ilike(q),
            )
        ]
        if jurisdiction:
            filters.append(ProgrammeDiscovery.jurisdiction == jurisdiction.upper())
        if programme_type:
            filters.append(ProgrammeDiscovery.programme_type == programme_type.upper())
        if state:
            filters.append(ProgrammeDiscovery.state_or_ut.ilike(f"%{state}%"))

        records = self.session.query(ProgrammeDiscovery).filter(and_(*filters)).limit(limit).all()
        return [self._format_programme(p) for p in records]

    def list_programmes(
        self,
        jurisdiction: Optional[str] = None,
        state: Optional[str] = None,
        ministry: Optional[str] = None,
        programme_type: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Lists discovered programmes with structured pagination and filters.
        """
        filters = []
        if jurisdiction:
            filters.append(ProgrammeDiscovery.jurisdiction == jurisdiction.upper())
        if state:
            filters.append(ProgrammeDiscovery.state_or_ut.ilike(f"%{state}%"))
        if ministry:
            filters.append(ProgrammeDiscovery.ministry.ilike(f"%{ministry}%"))
        if programme_type:
            filters.append(ProgrammeDiscovery.programme_type == programme_type.upper())
        if category:
            filters.append(ProgrammeDiscovery.category.ilike(f"%{category}%"))

        query_obj = self.session.query(ProgrammeDiscovery)
        if filters:
            query_obj = query_obj.filter(and_(*filters))

        total = query_obj.count()
        offset = (page - 1) * page_size
        records = query_obj.offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._format_programme(p) for p in records],
        }

    def get_programme(self, programme_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full canonical details of a single discovered programme.
        """
        prog = self.session.query(ProgrammeDiscovery).filter(ProgrammeDiscovery.programme_id == programme_id).first()
        if not prog:
            return None
        return self._format_programme(prog, full=True)

    def search_authority(self, authority_query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Finds all programmes governed or implemented by a specific Ministry, Department, or State Agency.
        """
        q = f"%{authority_query}%"
        records = (
            self.session.query(ProgrammeDiscovery)
            .filter(
                or_(
                    ProgrammeDiscovery.authority.ilike(q),
                    ProgrammeDiscovery.ministry.ilike(q),
                    ProgrammeDiscovery.department.ilike(q),
                )
            )
            .limit(limit)
            .all()
        )
        return [self._format_programme(p) for p in records]

    def search_jurisdiction(self, jurisdiction: str, state_or_ut: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Finds programmes under a specific jurisdiction (CENTRAL, STATE, UT).
        """
        filters = [ProgrammeDiscovery.jurisdiction == jurisdiction.upper()]
        if state_or_ut:
            filters.append(ProgrammeDiscovery.state_or_ut.ilike(f"%{state_or_ut}%"))
        records = self.session.query(ProgrammeDiscovery).filter(and_(*filters)).limit(limit).all()
        return [self._format_programme(p) for p in records]

    def get_source_metadata(self, source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns registry metadata, update status, and operational tier for discovery sources.
        """
        if source_id:
            src = self.registry.get_source(source_id)
            return [src.model_dump()] if src else []
        return [s.model_dump() for s in self.registry.list_sources()]

    def get_programme_documents(self, programme_id: str) -> List[Dict[str, Any]]:
        """
        Returns discovered document references (guidelines, official gazettes, application forms).
        """
        prog = self.session.query(ProgrammeDiscovery).filter(ProgrammeDiscovery.programme_id == programme_id).first()
        if not prog:
            return []
        try:
            lineage = json.loads(prog.lineage or "[]")
            srcs = json.loads(prog.source_records or "[]")
            return [
                {"title": f"Official Portal Record ({s.get('source_id')})", "url": s.get("url"), "type": "PORTAL_REF"}
                for s in srcs
            ]
        except Exception:
            return []

    def _format_programme(self, p: ProgrammeDiscovery, full: bool = False) -> Dict[str, Any]:
        """
        Formats ProgrammeDiscovery model into clean MCP response payload.
        Ensures clear eligibility status labelling per governance rules.
        """
        # Determine strict UI/MCP eligibility label
        if str(p.programme_type) == "INSTITUTIONAL_PROGRAMME":
            elig_label = "Institutional programme"
        elif str(p.programme_type) == "EMPLOYER_PROGRAMME":
            elig_label = "Employer programme"
        elif bool(p.eligibility_available):
            elig_label = "Check My Eligibility"
        elif str(p.governance_status) == "GOVERNANCE_REVIEW_REQUIRED":
            elig_label = "Eligibility review pending"
        else:
            elig_label = "Eligibility verification unavailable"

        item: Dict[str, Any] = {
            "programme_id": str(p.programme_id),
            "canonical_name": str(p.canonical_name),
            "programme_type": str(p.programme_type),
            "authority": str(p.authority) if p.authority else None,
            "ministry": str(p.ministry) if p.ministry else None,
            "department": str(p.department) if p.department else None,
            "jurisdiction": str(p.jurisdiction),
            "state_or_ut": str(p.state_or_ut) if p.state_or_ut else None,
            "category": str(p.category) if p.category else "General",
            "beneficiary_type": str(p.beneficiary_type) if p.beneficiary_type else "individual",
            "official_url": str(p.official_url) if p.official_url else None,
            "currentness": str(p.currentness) if p.currentness else "ACTIVE",
            "source_status": str(p.source_status) if p.source_status else "SOURCE_VERIFIED",
            "eligibility_status_label": elig_label,
            "eligibility_available": bool(p.eligibility_available),
            "is_certified": False,  # Discovery invariant: never certified
        }

        if full:
            item.update({
                "description": str(p.description) if p.description else None,
                "benefit_summary": str(p.benefit_summary) if p.benefit_summary else None,
                "application_route": str(p.application_route) if p.application_route else None,
                "governance_status": str(p.governance_status) if p.governance_status else None,
                "source_records": json.loads(str(p.source_records or "[]")),
                "lineage": json.loads(str(p.lineage or "[]")),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })
        else:
            desc = str(p.description or "")
            item["description"] = (desc[:200] + "...") if len(desc) > 200 else desc

        return item
