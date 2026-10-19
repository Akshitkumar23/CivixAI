"""
Ingestion Document Parser
Parses HTML and text PDF documents into structured text and clause sections.
"""
import re
import io
from enum import Enum
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from pypdf import PdfReader

class ParserQuality(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    OCR_REQUIRED = "ocr_required"
    FAILED = "failed"

class DocumentSection:
    def __init__(self, heading: str, fragment_id: str, content: str):
        self.heading = heading
        self.fragment_id = fragment_id
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {
            "heading": self.heading,
            "fragment_id": self.fragment_id,
            "content": self.content
        }

class ParsedDocument:
    def __init__(
        self,
        title: str,
        full_text: str,
        sections: List[DocumentSection],
        quality: ParserQuality = ParserQuality.COMPLETE,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.full_text = full_text
        self.sections = sections
        self.quality = quality
        self.metadata = metadata or {}

class DocumentParser:
    @staticmethod
    def parse_html(html_bytes: bytes, url: Optional[str] = None) -> ParsedDocument:
        """Parses HTML into clean text and structured clause sections."""
        soup = BeautifulSoup(html_bytes, "html.parser")

        # Strip scripts, styles, nav, and footers
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()

        sections: List[DocumentSection] = []
        full_text_parts: List[str] = []

        current_heading = "General Overview"
        current_content: List[str] = []
        section_idx = 1

        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
            text = elem.get_text().strip()
            if not text:
                continue

            if elem.name in ["h1", "h2", "h3", "h4"]:
                if current_content:
                    sections.append(DocumentSection(
                        heading=current_heading,
                        fragment_id=f"Section {section_idx}: {current_heading[:40]}",
                        content="\n".join(current_content)
                    ))
                    section_idx += 1
                    current_content = []
                current_heading = text
            else:
                current_content.append(text)
                full_text_parts.append(text)

        if current_content:
            sections.append(DocumentSection(
                heading=current_heading,
                fragment_id=f"Section {section_idx}: {current_heading[:40]}",
                content="\n".join(current_content)
            ))

        full_text = "\n\n".join(full_text_parts)
        quality = ParserQuality.COMPLETE
        if not full_text.strip():
            quality = ParserQuality.FAILED
        elif len(full_text.split()) < 30:
            quality = ParserQuality.PARTIAL

        return ParsedDocument(
            title=title or "Government Scheme Document",
            full_text=full_text,
            sections=sections,
            quality=quality,
            metadata={"source_type": "html", "url": url}
        )

    @staticmethod
    def parse_pdf(pdf_bytes: bytes, title: Optional[str] = None) -> ParsedDocument:
        """Parses text PDF bytes into pages and numbered sections using pypdf. Detects image-only/scanned documents."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            return ParsedDocument(
                title=title or "Unreadable Document",
                full_text="",
                sections=[],
                quality=ParserQuality.FAILED,
                metadata={"source_type": "pdf", "error": str(e)}
            )

        sections: List[DocumentSection] = []
        full_text_parts: List[str] = []

        # Extract title from metadata if present
        meta_title = None
        if reader.metadata and reader.metadata.title:
            meta_title = reader.metadata.title

        doc_title = title or meta_title or "Official Guidelines Document"

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue
            full_text_parts.append(page_text)

            # Split page into potential clauses (e.g., "1. Eligibility", "Para 3", "Clause 4")
            clause_pattern = re.compile(r"(?=(?:Clause|Section|Para|\b\d+\.\d+)\b)", re.IGNORECASE)
            parts = clause_pattern.split(page_text)

            if len(parts) > 1:
                for idx, part in enumerate(parts):
                    clean_part = part.strip()
                    if len(clean_part) > 20:
                        first_line = clean_part.splitlines()[0][:50]
                        sections.append(DocumentSection(
                            heading=f"Page {page_idx + 1} - {first_line}",
                            fragment_id=f"Page {page_idx + 1}, {first_line}",
                            content=clean_part
                        ))
            else:
                sections.append(DocumentSection(
                    heading=f"Page {page_idx + 1}",
                    fragment_id=f"Page {page_idx + 1}",
                    content=page_text.strip()
                ))

        if not sections and len(reader.pages) > 0:
            sections.append(DocumentSection(
                heading="Page 1",
                fragment_id="Page 1",
                content=""
            ))

        full_text = "\n\n".join(full_text_parts)
        num_pages = len(reader.pages)
        total_words = len(full_text.split())
        metadata: Dict[str, Any] = {"source_type": "pdf", "pages": num_pages, "words": total_words}

        if num_pages == 0 or (not full_text.strip() and num_pages == 0):
            quality = ParserQuality.FAILED
        elif total_words < 15 * max(num_pages, 1):
            # Scanned or image-only PDF with minimal text layer
            quality = ParserQuality.OCR_REQUIRED
            metadata["ocr_reason"] = f"Low text density ({total_words} words across {num_pages} pages)"
        elif len(sections) < 2 or total_words < 50:
            quality = ParserQuality.PARTIAL
        else:
            quality = ParserQuality.COMPLETE

        return ParsedDocument(
            title=doc_title,
            full_text=full_text,
            sections=sections,
            quality=quality,
            metadata=metadata
        )

    @classmethod
    def parse(cls, content: bytes, content_type: str, title: Optional[str] = None) -> ParsedDocument:
        if "pdf" in content_type.lower():
            return cls.parse_pdf(content, title=title)
        return cls.parse_html(content)
