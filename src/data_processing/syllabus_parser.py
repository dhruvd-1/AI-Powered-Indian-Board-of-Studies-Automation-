"""
Step 1: Syllabus Structure Extraction

Parses syllabus PDF and extracts:
- Course metadata (name, code, credits)
- Units with topics
- Course Outcomes (COs)

Output: JSON file with structured syllabus data
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber

from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


class SyllabusParser:
    """
    Extracts structured data from engineering syllabus PDFs.
    
    Handles Indian engineering syllabus format:
    - Course header (name, code, credits)
    - Unit-wise topic breakdown
    - Course Outcomes (COs)
    """
    
    def __init__(self, pdf_path: Path):
        """
        Initialize parser with syllabus PDF path.
        
        Args:
            pdf_path: Path to syllabus PDF file
        """
        self.pdf_path = pdf_path
        self.raw_text: str = ""
        self.course_info: Dict = {}
        self.units: List[Dict] = []
        self.course_outcomes: List[Dict] = []
    
    def extract_text(self) -> str:
        """
        Extract raw text from PDF using pdfplumber.
        
        Returns:
            Complete text content of PDF
        """
        print(f"📄 Reading PDF: {self.pdf_path.name}")
        
        text_parts = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n--- PAGE {page_num} ---\n")
                        text_parts.append(page_text)
            
            self.raw_text = "\n".join(text_parts)
            print(f"✅ Extracted {len(self.raw_text)} characters from {len(pdf.pages)} pages")
            return self.raw_text
            
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            raise
    
    def parse_course_info(self) -> Dict:
        """
        Extract course metadata from syllabus header.
        
        Returns:
            Dict with course_name, course_code, credits, etc.
        """
        print("🔍 Parsing course information...")
        
        # Extract course name (usually in ALL CAPS or bold)
        course_name_pattern = r"ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING|[A-Z\s&]{20,}"
        course_match = re.search(course_name_pattern, self.raw_text)
        course_name = course_match.group(0).strip() if course_match else "Unknown Course"
        
        # Extract course code (e.g., IS353IA)
        code_pattern = r"Course Code\s*:?\s*([A-Z0-9]+)"
        code_match = re.search(code_pattern, self.raw_text, re.IGNORECASE)
        course_code = code_match.group(1) if code_match else "UNKNOWN"
        
        # Extract credits (e.g., 3:0:1)
        credits_pattern = r"Credits:\s*L:T:P\s*:?\s*(\d+:\d+:\d+)"
        credits_match = re.search(credits_pattern, self.raw_text, re.IGNORECASE)
        credits = credits_match.group(1) if credits_match else "Unknown"
        
        # Extract total hours (e.g., 45L + 30P)
        hours_pattern = r"Total Hours\s*:?\s*(\d+L\s*\+\s*\d+P)"
        hours_match = re.search(hours_pattern, self.raw_text, re.IGNORECASE)
        total_hours = hours_match.group(1) if hours_match else "Unknown"
        
        self.course_info = {
            "course_name": course_name,
            "course_code": course_code,
            "credits": credits,
            "total_hours": total_hours,
            "semester": "V",  # Hardcoded from AIML syllabus, make dynamic later
        }
        
        print(f"✅ Course: {course_name} ({course_code})")
        return self.course_info
    
    def parse_units(self) -> List[Dict]:
        """
        Extract units and their topics from syllabus.
        
        Returns:
            List of dicts, each containing unit_number, title, hours, topics
        """
        print("🔍 Parsing units and topics...")
        
        # Split text into unit sections
        # Pattern: "Unit-I", "Unit – II", "Unit-III", etc.
        unit_pattern = r"Unit\s*[–-]\s*([IVX]+)\s+(\d+)\s*Hrs"
        unit_matches = list(re.finditer(unit_pattern, self.raw_text, re.IGNORECASE))
        
        if not unit_matches:
            print("⚠️ No units found in syllabus")
            return []
        
        self.units = []
        
        for i, match in enumerate(unit_matches):
            unit_roman = match.group(1)
            unit_hours = match.group(2)
            unit_number = self._roman_to_int(unit_roman)
            
            # Extract text between current unit and next unit (or end of document)
            start_pos = match.end()
            end_pos = unit_matches[i + 1].start() if i + 1 < len(unit_matches) else len(self.raw_text)
            unit_text = self.raw_text[start_pos:end_pos]
            
            # Extract topics (lines that look like topics, not headers)
            topics = self._extract_topics(unit_text)
            
            unit_data = {
                "unit_number": unit_number,
                "unit_id": f"unit_{unit_number}",
                "title": topics[0] if topics else f"Unit {unit_number}",  # First line often is title
                "hours": int(unit_hours),
                "topics": topics[1:] if len(topics) > 1 else topics,  # Rest are topics
            }
            
            self.units.append(unit_data)
            print(f"  ✓ Unit {unit_number}: {len(topics)} topics, {unit_hours} hours")
        
        print(f"✅ Parsed {len(self.units)} units")
        return self.units
    
    def parse_course_outcomes(self) -> List[Dict]:
        """
        Extract Course Outcomes (COs) from syllabus.
        
        Returns:
            List of dicts, each containing co_number, description
        """
        print("🔍 Parsing Course Outcomes...")
        
        # Find "Course Outcomes" section
        co_section_pattern = r"Course Outcomes:.*?(?=Reference Books|LABORATORY|$)"
        co_section_match = re.search(co_section_pattern, self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if not co_section_match:
            print("⚠️ No Course Outcomes section found")
            return []
        
        co_section = co_section_match.group(0)
        
        # Extract individual COs (e.g., "CO 1", "CO 2")
        co_pattern = r"CO\s*(\d+)\s+(.*?)(?=CO\s*\d+|Reference Books|LABORATORY|$)"
        co_matches = re.finditer(co_pattern, co_section, re.DOTALL | re.IGNORECASE)
        
        self.course_outcomes = []
        
        for match in co_matches:
            co_number = int(match.group(1))
            co_description = match.group(2).strip()
            
            # Clean up description (remove extra whitespace, newlines)
            co_description = re.sub(r'\s+', ' ', co_description)
            
            co_data = {
                "co_number": co_number,
                "co_id": f"CO{co_number}",
                "description": co_description,
            }
            
            self.course_outcomes.append(co_data)
            print(f"  ✓ CO{co_number}: {co_description[:60]}...")
        
        print(f"✅ Parsed {len(self.course_outcomes)} Course Outcomes")
        return self.course_outcomes
    
    def _extract_topics(self, unit_text: str) -> List[str]:
        """
        Extract individual topics from unit text.
        
        Args:
            unit_text: Raw text of a unit section
            
        Returns:
            List of topic strings
        """
        # Split by lines and filter
        lines = unit_text.split('\n')
        topics = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, page numbers, headers
            if not line:
                continue
            if re.match(r'^\d+$', line):  # Skip page numbers
                continue
            if re.match(r'^Page\s+\d+', line, re.IGNORECASE):
                continue
            if 'Computer Science' in line or 'Engineering' in line:
                continue
            
            # Topic lines are usually descriptive (3+ words)
            if len(line.split()) >= 3:
                topics.append(line)
        
        return topics
    
    def _roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer (I-V)."""
        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
        return roman_map.get(roman.upper(), 0)
    
    def parse(self) -> Dict:
        """
        Main parsing method - orchestrates all extraction steps.
        
        Returns:
            Complete structured syllabus data
        """
        print("\n" + "="*60)
        print("STEP 1: SYLLABUS STRUCTURE EXTRACTION")
        print("="*60 + "\n")
        
        # Step 1: Extract raw text
        self.extract_text()
        
        # Step 2: Parse course info
        self.parse_course_info()
        
        # Step 3: Parse units
        self.parse_units()
        
        # Step 4: Parse course outcomes
        self.parse_course_outcomes()
        
        # Combine everything
        structured_data = {
            "course_info": self.course_info,
            "units": self.units,
            "course_outcomes": self.course_outcomes,
            "metadata": {
                "num_units": len(self.units),
                "num_cos": len(self.course_outcomes),
                "total_topics": sum(len(u['topics']) for u in self.units),
            }
        }
        
        print("\n" + "="*60)
        print("✅ STEP 1 COMPLETE")
        print(f"   - {len(self.units)} units extracted")
        print(f"   - {len(self.course_outcomes)} COs extracted")
        print(f"   - {structured_data['metadata']['total_topics']} topics identified")
        print("="*60 + "\n")
        
        return structured_data
    
    def save_to_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save parsed data to JSON file.
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path where JSON was saved
        """
        if output_path is None:
            course_code = self.course_info.get('course_code', 'unknown')
            output_path = PROCESSED_DATA_DIR / f"{course_code}_structure.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Parse first if not already done
            if not self.course_info:
                self.parse()
            
            structured_data = {
                "course_info": self.course_info,
                "units": self.units,
                "course_outcomes": self.course_outcomes,
                "metadata": {
                    "num_units": len(self.units),
                    "num_cos": len(self.course_outcomes),
                    "total_topics": sum(len(u['topics']) for u in self.units),
                }
            }
            
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved structured data to: {output_path}")
        return output_path


def run_step1_demo(syllabus_filename: str):
    """
    Demo function to test Step 1 on AIML syllabus.
    
    Args:
        syllabus_filename: Name of syllabus PDF in data/raw/
    """
    # Path to syllabus PDF
    pdf_path = RAW_DATA_DIR / syllabus_filename
    
    if not pdf_path.exists():
        print(f"❌ Syllabus not found: {pdf_path}")
        print(f"   Please place '{syllabus_filename}' in: {RAW_DATA_DIR}")
        return
    
    # Parse syllabus
    parser = SyllabusParser(pdf_path)
    structured_data = parser.parse()
    
    # Save to JSON
    output_path = parser.save_to_json()
    
    print(f"\n📊 Preview of extracted data:")
    print(json.dumps(structured_data, indent=2)[:1000] + "...\n")
    
    return structured_data


if __name__ == "__main__":
    # Test Step 1 with AIML syllabus
    run_step1_demo("ArtificialIntelligence_Syllabus_2022Scheme.pdf")
