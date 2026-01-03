"""
Step 16: Exam Paper PDF Formatter

Formats selected questions into professional exam paper PDF.
"""

from typing import List
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

from src.database.schema import Question, QuestionBankDB
from src.paper.blueprint import PaperBlueprint


class ExamPaperFormatter:
    """
    Formats exam paper as professional PDF.
    
    Includes:
    - Institution header
    - Exam metadata
    - Instructions
    - Questions with proper spacing
    - Marks allocation
    """
    
    def __init__(self, db: QuestionBankDB):
        """Initialize formatter with database."""
        self.db = db
    
    def generate_pdf(
        self,
        question_ids: List[int],
        blueprint: PaperBlueprint,
        output_path: Path,
        institution_name: str = "RV College of Engineering",
        department: str = "Department of Information Science and Engineering",
        include_marking_scheme: bool = True
    ) -> Path:
        """
        Generate exam paper PDF.
        
        Args:
            question_ids: List of question IDs to include
            blueprint: Paper blueprint with metadata
            output_path: Where to save PDF
            institution_name: Institution name for header
            department: Department name
            include_marking_scheme: If True, add marking scheme page
            
        Returns:
            Path to generated PDF
        """
        print(f"\n{'='*60}")
        print("GENERATING EXAM PAPER PDF")
        print(f"{'='*60}\n")
        
        # Load questions
        questions = [self.db.get_question(qid) for qid in question_ids]
        questions = [q for q in questions if q]  # Filter None
        
        if not questions:
            raise ValueError("No valid questions found!")
        
        print(f"Formatting {len(questions)} questions...")
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=3,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # Header
        story.append(Paragraph(institution_name, title_style))
        story.append(Paragraph(department, subtitle_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Exam details
        marks_constraint = blueprint.get_constraint('marks_total')
        duration_constraint = blueprint.get_constraint('duration')
        
        exam_details = f"""
        <b>{blueprint.paper_name}</b><br/>
        <b>Course:</b> {blueprint.course_code}<br/>
        <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
        <b>Duration:</b> {duration_constraint.value if duration_constraint else 'TBD'} minutes | 
        <b>Max Marks:</b> {marks_constraint.value if marks_constraint else 'TBD'}
        """
        
        story.append(Paragraph(exam_details, subtitle_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Horizontal line
        story.append(self._create_horizontal_line())
        story.append(Spacer(1, 0.15*inch))
        
        # Instructions
        instructions = """
        <b>Instructions:</b><br/>
        1. Answer all questions.<br/>
        2. Write your answers in the space provided or on separate sheets as instructed.<br/>
        3. All questions carry equal marks unless otherwise mentioned.<br/>
        4. Use of non-programmable calculators is permitted.
        """
        story.append(Paragraph(instructions, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(self._create_horizontal_line())
        story.append(Spacer(1, 0.2*inch))
        
        # Questions
        total_marks = sum(q.marks for q in questions)
        
        for i, q in enumerate(questions, 1):
            # Question number and marks
            q_header = f"<b>Q{i}.</b> ({q.marks} marks) "
            q_text = f"{q_header}{q.question_text}"
            
            story.append(Paragraph(q_text, question_style))
            
            # Answer space indicator
            if q.expected_answer_length:
                space_text = f"<i>[Answer space: {q.expected_answer_length}]</i>"
                story.append(Paragraph(space_text, styles['Italic']))
            
            story.append(Spacer(1, 0.3*inch))
        
        # End of paper
        story.append(Spacer(1, 0.3*inch))
        story.append(self._create_horizontal_line())
        story.append(Paragraph(f"<b>Total Marks: {total_marks}</b>", subtitle_style))
        
        # Marking scheme (optional, on new page)
        if include_marking_scheme:
            story.append(PageBreak())
            story.extend(self._create_marking_scheme(questions, blueprint))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF saved to: {output_path}")
        print(f"   Questions: {len(questions)}")
        print(f"   Total marks: {total_marks}")
        print(f"{'='*60}\n")
        
        return output_path
    
    def _create_horizontal_line(self):
        """Create a horizontal line for visual separation."""
        return Table(
            [['']], 
            colWidths=[6.5*inch],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
            ])
        )
    
    def _create_marking_scheme(
        self,
        questions: List[Question],
        blueprint: PaperBlueprint
    ) -> List:
        """Create marking scheme page."""
        
        styles = getSampleStyleSheet()
        content = []
        
        # Title
        title_style = ParagraphStyle(
            'SchemeTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        content.append(Paragraph("MARKING SCHEME", title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # CO-PO mapping table
        content.append(Paragraph("<b>Course Outcome Mapping:</b>", styles['Heading2']))
        content.append(Spacer(1, 0.1*inch))
        
        co_table_data = [['Question', 'CO', 'Bloom Level', 'Difficulty', 'Marks']]
        
        for i, q in enumerate(questions, 1):
            co_table_data.append([
                f'Q{i}',
                q.primary_co,
                f'L{q.bloom_level}',
                q.difficulty.capitalize(),
                str(q.marks)
            ])
        
        co_table = Table(co_table_data, colWidths=[1*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch])
        co_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        content.append(co_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Bloom distribution
        content.append(Paragraph("<b>Bloom's Taxonomy Distribution:</b>", styles['Heading2']))
        content.append(Spacer(1, 0.1*inch))
        
        bloom_counts = {}
        bloom_marks = {}
        
        for q in questions:
            bloom_counts[q.bloom_level] = bloom_counts.get(q.bloom_level, 0) + 1
            bloom_marks[q.bloom_level] = bloom_marks.get(q.bloom_level, 0) + q.marks
        
        bloom_names = {
            1: "Remember",
            2: "Understand",
            3: "Apply",
            4: "Analyze",
            5: "Evaluate",
            6: "Create"
        }
        
        bloom_text = []
        for level in sorted(bloom_counts.keys()):
            bloom_text.append(
                f"L{level} ({bloom_names[level]}): {bloom_counts[level]} question(s), {bloom_marks[level]} marks"
            )
        
        content.append(Paragraph("<br/>".join(bloom_text), styles['Normal']))
        content.append(Spacer(1, 0.3*inch))
        
        # CO coverage
        content.append(Paragraph("<b>Course Outcome Coverage:</b>", styles['Heading2']))
        content.append(Spacer(1, 0.1*inch))
        
        co_coverage = {}
        for q in questions:
            co_coverage[q.primary_co] = co_coverage.get(q.primary_co, 0) + q.marks
        
        co_text = []
        for co in sorted(co_coverage.keys()):
            co_text.append(f"{co}: {co_coverage[co]} marks")
        
        content.append(Paragraph("<br/>".join(co_text), styles['Normal']))
        
        return content


class MarkingSchemeGenerator:
    """Generate detailed marking scheme with model answers."""
    
    def __init__(self, db: QuestionBankDB):
        """Initialize with database."""
        self.db = db
    
    def generate_scheme_pdf(
        self,
        question_ids: List[int],
        output_path: Path
    ) -> Path:
        """
        Generate marking scheme PDF with expected answers.
        
        Args:
            question_ids: Question IDs
            output_path: Output path
            
        Returns:
            Path to generated PDF
        """
        # Load questions
        questions = [self.db.get_question(qid) for qid in question_ids]
        questions = [q for q in questions if q]
        
        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        story.append(Paragraph("<b>MARKING SCHEME</b>", styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        for i, q in enumerate(questions, 1):
            story.append(Paragraph(f"<b>Q{i}. ({q.marks} marks)</b>", styles['Heading2']))
            story.append(Paragraph(q.question_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # Expected answer framework
            story.append(Paragraph("<b>Marking Guidelines:</b>", styles['Heading3']))
            
            # Source references (for instructor)
            import json
            sources = json.loads(q.retrieval_sources) if isinstance(q.retrieval_sources, str) else q.retrieval_sources
            source_text = "Sources: " + ", ".join([f"{s['file']} (p.{s['page']})" for s in sources[:3]])
            story.append(Paragraph(f"<i>{source_text}</i>", styles['Italic']))
            
            story.append(Spacer(1, 0.3*inch))
        
        doc.build(story)
        return output_path