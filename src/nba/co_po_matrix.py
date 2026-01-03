"""
Step 17: CO-PO Mapping Matrix Generator

Generates Course Outcome to Program Outcome mapping matrices
for NBA accreditation.
"""

from typing import Dict, List, Optional
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from src.database.schema import QuestionBankDB, Question, ExamPaper


class COPOMatrixGenerator:
    """
    Generates CO-PO mapping matrices for NBA audit.
    
    Matrices show:
    1. Course-level CO-PO mapping (design matrix)
    2. Assessment-level CO-PO coverage (actual attainment)
    3. Question-level mapping for transparency
    """
    
    def __init__(self, db: QuestionBankDB):
        """Initialize with database."""
        self.db = db
    
    def generate_course_co_po_matrix(
        self,
        course_code: str,
        co_definitions: List[Dict],
        po_definitions: List[Dict]
    ) -> Dict:
        """
        Generate course-level CO-PO mapping matrix.
        
        This is the DESIGN matrix showing which COs address which POs.
        Typically filled by course designer, but can be auto-suggested
        based on CO descriptions.
        
        Args:
            course_code: Course code
            co_definitions: List of COs with descriptions
            po_definitions: List of POs with descriptions
            
        Returns:
            Dict with matrix data
        """
        # Mapping strength: 0 (none), 1 (low), 2 (medium), 3 (high)
        
        # Default mapping based on common patterns
        # In production, this would be customized per course
        default_mapping = {
            'CO1': {'PO1': 2, 'PO2': 1},  # Typically basic concepts
            'CO2': {'PO1': 3, 'PO2': 2, 'PO3': 1},
            'CO3': {'PO2': 3, 'PO3': 2, 'PO4': 1},
            'CO4': {'PO3': 3, 'PO4': 2, 'PO5': 1},
            'CO5': {'PO4': 3, 'PO5': 2, 'PO12': 1},
        }
        
        matrix = {}
        
        for co in co_definitions:
            co_id = co['co_id']
            matrix[co_id] = default_mapping.get(co_id, {})
        
        return {
            'course_code': course_code,
            'cos': [co['co_id'] for co in co_definitions],
            'pos': [po['po_id'] for po in po_definitions],
            'mapping': matrix,
            'type': 'design'
        }
    
    def generate_assessment_co_po_matrix(
        self,
        paper_id: int
    ) -> Dict:
        """
        Generate assessment-level CO-PO matrix.
        
        This shows ACTUAL coverage in a specific exam paper.
        
        Args:
            paper_id: Exam paper ID
            
        Returns:
            Dict with matrix data
        """
        paper = self.db.get_exam_paper(paper_id)
        
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        # Load questions
        questions = [self.db.get_question(qid) for qid in paper.question_ids]
        questions = [q for q in questions if q]
        
        # Build CO-PO mapping from actual questions
        co_po_marks = {}  # {CO: {PO: marks}}
        
        for q in questions:
            co = q.primary_co
            
            if co not in co_po_marks:
                co_po_marks[co] = {}
            
            # Get POs for this question
            pos = json.loads(q.program_outcomes) if isinstance(q.program_outcomes, str) else q.program_outcomes
            
            for po in pos:
                co_po_marks[co][po] = co_po_marks[co].get(po, 0) + q.marks
        
        return {
            'paper_id': paper_id,
            'paper_name': paper.paper_name,
            'course_code': paper.course_code,
            'total_marks': paper.total_marks,
            'mapping': co_po_marks,
            'type': 'assessment'
        }
    
    def generate_question_level_mapping(
        self,
        paper_id: int
    ) -> List[Dict]:
        """
        Generate question-level CO-PO mapping.
        
        Most granular view showing each question's contribution.
        
        Args:
            paper_id: Exam paper ID
            
        Returns:
            List of question mappings
        """
        paper = self.db.get_exam_paper(paper_id)
        
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        questions = [self.db.get_question(qid) for qid in paper.question_ids]
        questions = [q for q in questions if q]
        
        mappings = []
        
        for i, q in enumerate(questions, 1):
            pos = json.loads(q.program_outcomes) if isinstance(q.program_outcomes, str) else q.program_outcomes
            
            mappings.append({
                'question_number': i,
                'question_id': q.id,
                'question_text': q.question_text[:100] + "...",
                'co': q.primary_co,
                'pos': pos,
                'bloom_level': q.bloom_level,
                'marks': q.marks
            })
        
        return mappings
    
    def export_matrix_to_pdf(
        self,
        matrix_data: Dict,
        output_path: Path,
        title: str = "CO-PO Mapping Matrix"
    ) -> Path:
        """
        Export CO-PO matrix as PDF table.
        
        Args:
            matrix_data: Matrix data from generate_*_matrix()
            output_path: Output path
            title: PDF title
            
        Returns:
            Path to generated PDF
        """
        # Use landscape for better matrix visibility
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'MatrixTitle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Course: {matrix_data['course_code']}", styles['Normal']))
        
        if matrix_data['type'] == 'assessment':
            story.append(Paragraph(f"Paper: {matrix_data['paper_name']}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Build table
        if matrix_data['type'] == 'design':
            table_data = self._build_design_matrix_table(matrix_data)
        else:
            table_data = self._build_assessment_matrix_table(matrix_data)
        
        # Create table
        col_widths = [1.2*inch] + [0.6*inch] * (len(table_data[0]) - 1)
        
        matrix_table = Table(table_data, colWidths=col_widths)
        matrix_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Row header styling
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ECF0F1')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            
            # Cell styling
            ('FONTSIZE', (1, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        story.append(matrix_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Legend
        if matrix_data['type'] == 'design':
            legend = """
            <b>Mapping Strength:</b><br/>
            0 = No correlation | 1 = Low | 2 = Medium | 3 = High
            """
        else:
            legend = """
            <b>Values:</b> Marks allocated for each CO-PO combination
            """
        
        story.append(Paragraph(legend, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ CO-PO matrix exported: {output_path}")
        
        return output_path
    
    def _build_design_matrix_table(self, matrix_data: Dict) -> List[List]:
        """Build table for design matrix."""
        
        cos = matrix_data['cos']
        pos = matrix_data['pos']
        mapping = matrix_data['mapping']
        
        # Header row
        header = ['CO / PO'] + pos
        
        # Data rows
        rows = [header]
        
        for co in cos:
            row = [co]
            
            for po in pos:
                strength = mapping.get(co, {}).get(po, 0)
                row.append(str(strength))
            
            rows.append(row)
        
        return rows
    
    def _build_assessment_matrix_table(self, matrix_data: Dict) -> List[List]:
        """Build table for assessment matrix."""
        
        mapping = matrix_data['mapping']
        
        # Get all unique COs and POs
        cos = sorted(mapping.keys())
        pos = set()
        for co_pos in mapping.values():
            pos.update(co_pos.keys())
        pos = sorted(pos)
        
        # Header row
        header = ['CO / PO'] + pos
        
        # Data rows
        rows = [header]
        
        for co in cos:
            row = [co]
            
            for po in pos:
                marks = mapping.get(co, {}).get(po, 0)
                row.append(str(marks) if marks > 0 else '-')
            
            rows.append(row)
        
        # Total row
        total_row = ['Total']
        for po in pos:
            total = sum(mapping.get(co, {}).get(po, 0) for co in cos)
            total_row.append(str(total) if total > 0 else '-')
        
        rows.append(total_row)
        
        return rows