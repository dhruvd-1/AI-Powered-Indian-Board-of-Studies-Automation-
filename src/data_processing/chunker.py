"""
Step 2: Document Chunking + Metadata Tagging

Takes extracted pages and splits them into chunks with metadata.
Each chunk is tagged with:
- unit_id (which unit it belongs to)
- source_file (which PDF it came from)
- page_number (which page it's from)
- chunk_index (position in sequence)
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from config.settings import PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from src.data_processing.document_processor import DocumentProcessor, DocumentPage


@dataclass
class Chunk:
    """Represents a single text chunk with metadata."""
    text: str
    unit_id: str
    source_file: str
    page_number: int
    chunk_index: int
    char_count: int
    metadata: Dict


class DocumentChunker:
    """
    Splits documents into overlapping chunks with metadata preservation.
    
    Uses character-based chunking with overlap to ensure context continuity.
    Each chunk maintains metadata about its source (unit, file, page).
    """
    
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        """
        Initialize chunker with size parameters.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[Chunk] = []
    
    def chunk_pages(
        self,
        pages: List[DocumentPage],
        unit_id: str
    ) -> List[Chunk]:
        """
        Chunk a list of document pages.
        
        Args:
            pages: List of DocumentPage objects to chunk
            unit_id: Unit identifier for all chunks
            
        Returns:
            List of Chunk objects
        """
        all_chunks = []
        
        for page in pages:
            page_chunks = self._chunk_text(
                text=page.text,
                unit_id=unit_id,
                source_file=page.source_file,
                page_number=page.page_number
            )
            all_chunks.extend(page_chunks)
        
        return all_chunks
    
    def _chunk_text(
        self,
        text: str,
        unit_id: str,
        source_file: str,
        page_number: int
    ) -> List[Chunk]:
        """
        Split a single page's text into overlapping chunks.
        
        Args:
            text: Text to chunk
            unit_id: Unit identifier
            source_file: Source PDF filename
            page_number: Page number in source PDF
            
        Returns:
            List of chunks from this page
        """
        chunks = []
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            chunk = Chunk(
                text=text,
                unit_id=unit_id,
                source_file=source_file,
                page_number=page_number,
                chunk_index=0,
                char_count=len(text),
                metadata={
                    "unit_id": unit_id,
                    "source_file": source_file,
                    "page_number": page_number,
                }
            )
            return [chunk]
        
        # Split into overlapping chunks
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Determine end position
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at sentence boundary
            if end < len(text):
                end = self._find_sentence_boundary(text, end)
            else:
                end = len(text)
            
            chunk_text = text[start:end].strip()
            
            # Only create chunk if it has meaningful content
            if len(chunk_text) > 50:  # Minimum chunk size
                chunk = Chunk(
                    text=chunk_text,
                    unit_id=unit_id,
                    source_file=source_file,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    char_count=len(chunk_text),
                    metadata={
                        "unit_id": unit_id,
                        "source_file": source_file,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position (with overlap)
            start = end - self.chunk_overlap
            
            # Avoid infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, target_pos: int) -> int:
        """
        Find the nearest sentence boundary to target position.
        
        Looks for sentence-ending punctuation (., !, ?) followed by space.
        Falls back to target_pos if no boundary found within 200 chars.
        
        Args:
            text: Full text
            target_pos: Target position to find boundary near
            
        Returns:
            Position of sentence boundary
        """
        # Search window: 200 chars before and after target
        search_start = max(0, target_pos - 200)
        search_end = min(len(text), target_pos + 200)
        search_text = text[search_start:search_end]
        
        # Look for sentence endings
        sentence_pattern = r'[.!?]\s+'
        matches = list(re.finditer(sentence_pattern, search_text))
        
        if not matches:
            return target_pos
        
        # Find closest match to target position
        target_in_search = target_pos - search_start
        closest_match = min(
            matches,
            key=lambda m: abs(m.end() - target_in_search)
        )
        
        # Return absolute position
        return search_start + closest_match.end()
    
    def save_chunks(
        self,
        chunks: List[Chunk],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Save chunks to JSONL file (one JSON object per line).
        
        Args:
            chunks: List of chunks to save
            output_path: Optional custom output path
            
        Returns:
            Path where chunks were saved
        """
        if output_path is None:
            output_path = PROCESSED_DATA_DIR / "chunks.jsonl"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                # Convert dataclass to dict
                chunk_dict = asdict(chunk)
                # Write as single-line JSON
                f.write(json.dumps(chunk_dict, ensure_ascii=False) + '\n')
        
        print(f"💾 Saved {len(chunks)} chunks to: {output_path}")
        return output_path
    
    def load_chunks(self, input_path: Path) -> List[Chunk]:
        """
        Load chunks from JSONL file.
        
        Args:
            input_path: Path to chunks.jsonl file
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunk_dict = json.loads(line)
                chunk = Chunk(**chunk_dict)
                chunks.append(chunk)
        
        print(f"📂 Loaded {len(chunks)} chunks from: {input_path}")
        return chunks


class UnitContentProcessor:
    """
    Processes all content for a single unit (lecture notes, textbooks, etc.)
    and produces tagged chunks.
    """
    
    def __init__(self, unit_id: str, unit_name: str):
        """
        Initialize processor for a specific unit.
        
        Args:
            unit_id: Unit identifier (e.g., "unit_1")
            unit_name: Human-readable unit name
        """
        self.unit_id = unit_id
        self.unit_name = unit_name
        self.chunker = DocumentChunker()
        self.all_chunks: List[Chunk] = []
    
    def process_pdfs(self, pdf_paths: List[Path]) -> List[Chunk]:
        """
        Process multiple PDFs for this unit.
        
        Args:
            pdf_paths: List of paths to PDF files for this unit
            
        Returns:
            List of all chunks from all PDFs
        """
        print(f"\n📚 Processing Unit: {self.unit_name} ({self.unit_id})")
        print(f"   Files to process: {len(pdf_paths)}")
        
        for pdf_path in pdf_paths:
            # Extract pages
            processor = DocumentProcessor(pdf_path, self.unit_id)
            pages = processor.extract_pages()
            
            if not pages:
                print(f"  ⚠️ No content extracted from {pdf_path.name}")
                continue
            
            # Chunk pages
            chunks = self.chunker.chunk_pages(pages, self.unit_id)
            self.all_chunks.extend(chunks)
            
            print(f"  ✓ {pdf_path.name}: {len(pages)} pages → {len(chunks)} chunks")
        
        print(f"✅ Total chunks for {self.unit_name}: {len(self.all_chunks)}")
        return self.all_chunks
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about processed chunks.
        
        Returns:
            Dict with chunk statistics
        """
        if not self.all_chunks:
            return {}
        
        total_chars = sum(c.char_count for c in self.all_chunks)
        avg_chunk_size = total_chars / len(self.all_chunks)
        
        # Count unique source files
        source_files = set(c.source_file for c in self.all_chunks)
        
        # Count unique pages
        pages = set((c.source_file, c.page_number) for c in self.all_chunks)
        
        return {
            "unit_id": self.unit_id,
            "unit_name": self.unit_name,
            "total_chunks": len(self.all_chunks),
            "total_characters": total_chars,
            "avg_chunk_size": int(avg_chunk_size),
            "num_source_files": len(source_files),
            "num_pages_processed": len(pages),
            "source_files": list(source_files),
        }


def run_step2_demo(unit_pdfs: Dict[str, List[str]]):
    """
    Demo function to test Step 2 on sample PDFs.
    
    Args:
        unit_pdfs: Dict mapping unit_id to list of PDF filenames
                   Example: {"unit_1": ["unit1_notes.pdf", "unit1_textbook.pdf"]}
    """
    from config.settings import RAW_DATA_DIR
    
    print("\n" + "="*60)
    print("STEP 2: DOCUMENT CHUNKING + METADATA TAGGING")
    print("="*60 + "\n")
    
    all_chunks = []
    statistics = []
    
    # Process each unit
    for unit_id, pdf_filenames in unit_pdfs.items():
        # Get full paths
        pdf_paths = [RAW_DATA_DIR / fname for fname in pdf_filenames]
        
        # Check if files exist
        missing = [p for p in pdf_paths if not p.exists()]
        if missing:
            print(f"⚠️ Missing files for {unit_id}:")
            for p in missing:
                print(f"   - {p}")
            continue
        
        # Process unit
        unit_name = unit_id.replace('_', ' ').title()
        processor = UnitContentProcessor(unit_id, unit_name)
        chunks = processor.process_pdfs(pdf_paths)
        
        all_chunks.extend(chunks)
        statistics.append(processor.get_statistics())
    
    # Save all chunks to single file
    if all_chunks:
        chunker = DocumentChunker()
        output_path = chunker.save_chunks(all_chunks)
        
        print("\n" + "="*60)
        print("📊 CHUNKING STATISTICS")
        print("="*60)
        
        for stats in statistics:
            print(f"\n{stats['unit_name']}:")
            print(f"  - Chunks: {stats['total_chunks']}")
            print(f"  - Avg chunk size: {stats['avg_chunk_size']} chars")
            print(f"  - Source files: {stats['num_source_files']}")
            print(f"  - Pages processed: {stats['num_pages_processed']}")
        
        print(f"\n{'='*60}")
        print(f"✅ STEP 2 COMPLETE")
        print(f"   Total chunks: {len(all_chunks)}")
        print(f"   Output: {output_path}")
        print("="*60 + "\n")
        
        return all_chunks, statistics
    else:
        print("❌ No chunks generated. Check if PDFs exist in data/raw/")
        return None, None


if __name__ == "__main__":
    # Example: Process sample PDFs
    # Place your lecture notes in data/raw/ with these names
    
    unit_pdfs = {
        "unit_1": ["unit1_lecture_notes.pdf"],
        "unit_2": ["unit2_lecture_notes.pdf"],
        # Add more units as needed
    }
    
    run_step2_demo(unit_pdfs)
