"""
Document processor for extracting text from PDFs with page-level tracking.
Handles lecture notes, textbooks, and reference materials.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
import pdfplumber
from dataclasses import dataclass


@dataclass
class DocumentPage:
    """Represents a single page from a document."""
    page_number: int
    text: str
    source_file: str
    unit_id: Optional[str] = None


class DocumentProcessor:
    """
    Extracts text from PDF documents with page-level tracking.
    
    Used for processing lecture notes and textbooks that will be chunked
    and stored in vector databases.
    """
    
    def __init__(self, pdf_path: Path, unit_id: Optional[str] = None):
        """
        Initialize document processor.
        
        Args:
            pdf_path: Path to PDF file
            unit_id: Optional unit identifier (e.g., "unit_1", "unit_2")
        """
        self.pdf_path = pdf_path
        self.unit_id = unit_id
        self.pages: List[DocumentPage] = []
    
    def extract_pages(self) -> List[DocumentPage]:
        """
        Extract text from all pages in PDF.
        
        Returns:
            List of DocumentPage objects, one per page
        """
        print(f"📄 Processing: {self.pdf_path.name}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # Clean text
                        cleaned_text = self._clean_text(text)
                        
                        doc_page = DocumentPage(
                            page_number=page_num,
                            text=cleaned_text,
                            source_file=self.pdf_path.name,
                            unit_id=self.unit_id
                        )
                        
                        self.pages.append(doc_page)
            
            print(f"  ✓ Extracted {len(self.pages)} pages")
            return self.pages
            
        except Exception as e:
            print(f"  ✗ Error processing {self.pdf_path.name}: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing artifacts and normalizing whitespace.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common pattern: "Page 15" or just "15" at end)
        text = re.sub(r'\bPage\s+\d+\b', '', text, flags=re.IGNORECASE)
        
        # Remove common footer/header artifacts
        text = re.sub(r'\b\d+\s*$', '', text)  # Trailing page numbers
        
        # Normalize quotes and apostrophes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def get_full_text(self) -> str:
        """
        Get complete text from all pages concatenated.
        
        Returns:
            Full document text
        """
        if not self.pages:
            self.extract_pages()
        
        return "\n\n".join(page.text for page in self.pages)