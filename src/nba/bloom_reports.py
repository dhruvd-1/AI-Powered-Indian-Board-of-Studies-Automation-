"""
Step 18: Bloom's Taxonomy Distribution Reports

Generates detailed reports on Bloom level coverage for NBA compliance.
"""

from typing import Dict, List
from pathlib import Path
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from src.database.schema import QuestionBankDB


class BloomReportGenerator:
    """
    Generates Bloom's taxonomy distribution reports.
    
    Reports include:
    1. Overall Bloom distribution across question bank
    2. Bloom distribution per exam paper
    3. Bloom distribution per CO
    4. Visual charts (pie, bar)
    """
    
    def __init__(self, db: QuestionBankDB):
        """Initialize with database."""
        self.db = db
        
        self.bloom_names = {
            1: "Remember",
            2: "Understand",
            3: "Apply",
            4: "Analyze",
            5: "Evaluate",
            6: "Create"
        }
    
    def analyze_question_bank_bloom(
        self,
        course_code: str
    ) -> Dict:
        """
        Analyze Bloom distribution across entire question bank.
        
        Args:
            course_code: Course code to filter
            
        Returns:
            Dict with distribution data
        """
        questions = self.db.get_questions_by_filters(
            course_code=course_code,
            review_status='accepted'
        )
        
        return self._calculate_bloom_distribution(questions, 'Question Bank')
    
    def analyze_paper_bloom(
        self,
        paper_id: int
    ) -> Dict:
        """
        Analyze Bloom distribution for specific exam paper.
        
        Args:
            paper_id: Exam paper ID
            
        Returns:
            Dict with distribution data
        """
        paper = self.db.get_exam_paper(paper_id)
        
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        questions = [self.db.get_question(qid) for qid in paper.question_ids]
        questions = [q for q in questions if q]
        
        return self._calculate_bloom_distribution(
            questions,
            f"{paper.paper_name} ({paper.course_code})"
        )
    
    def analyze_co_bloom_distribution(
        self,
        course_code: str
    ) -> Dict:
        """
        Analyze Bloom distribution per Course Outcome.
        
        Shows which COs emphasize which cognitive levels.
        
        Args:
            course_code: Course code
            
        Returns:
            Dict with CO-wise Bloom distribution
        """
        questions = self.db.get_questions_by_filters(
            course_code=course_code,
            review_status='accepted'
        )
        
        # Group by CO
        co_groups = {}
        for q in questions:
            if q.primary_co not in co_groups:
                co_groups[q.primary_co] = []
            co_groups[q.primary_co].append(q)
        
        # Calculate distribution for each CO
        co_distributions = {}
        
        for co, co_questions in co_groups.items():
            co_distributions[co] = self._calculate_bloom_distribution(
                co_questions,
                f"{co}"
            )
        
        return {
            'course_code': course_code,
            'co_distributions': co_distributions
        }
    
    def _calculate_bloom_distribution(
        self,
        questions: List,
        context: str
    ) -> Dict:
        """Calculate Bloom distribution from questions."""
        
        if not questions:
            return {
                'context': context,
                'total_questions': 0,
                'total_marks': 0,
                'distribution_by_count': {},
                'distribution_by_marks': {},
                'distribution_percentage': {}
            }
        
        total_questions = len(questions)
        total_marks = sum(q.marks for q in questions)
        
        # Count and marks by Bloom level
        bloom_counts = {}
        bloom_marks = {}
        
        for q in questions:
            level = q.bloom_level
            bloom_counts[level] = bloom_counts.get(level, 0) + 1
            bloom_marks[level] = bloom_marks.get(level, 0) + q.marks
        
        # Calculate percentages
        bloom_percentages = {}
        for level, marks in bloom_marks.items():
            bloom_percentages[level] = (marks / total_marks * 100) if total_marks > 0 else 0
        
        return {
            'context': context,
            'total_questions': total_questions,
            'total_marks': total_marks,
            'distribution_by_count': bloom_counts,
            'distribution_by_marks': bloom_marks,
            'distribution_percentage': bloom_percentages
        }
    
    def generate_bloom_report_pdf(
        self,
        distribution_data: Dict,
        output_path: Path,
        include_charts: bool = True
    ) -> Path:
        """
        Generate Bloom distribution report as PDF.
        
        Args:
            distribution_data: Distribution data from analyze_*_bloom()
            output_path: Output path
            include_charts: Include visual charts
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        story.append(Paragraph("Bloom's Taxonomy Distribution Report", title_style))
        story.append(Paragraph(f"Context: {distribution_data['context']}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary
        story.append(Paragraph("<b>Summary:</b>", styles['Heading2']))
        summary_text = f"""
        Total Questions: {distribution_data['total_questions']}<br/>
        Total Marks: {distribution_data['total_marks']}
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Distribution table
        story.append(Paragraph("<b>Bloom Level Distribution:</b>", styles['Heading2']))
        
        table_data = [['Bloom Level', 'Questions', 'Marks', 'Percentage']]
        
        for level in sorted(distribution_data['distribution_by_count'].keys()):
            count = distribution_data['distribution_by_count'][level]
            marks = distribution_data['distribution_by_marks'][level]
            pct = distribution_data['distribution_percentage'][level]
            
            table_data.append([
                f"L{level} - {self.bloom_names[level]}",
                str(count),
                str(marks),
                f"{pct:.1f}%"
            ])
        
        bloom_table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1.2*inch])
        bloom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        story.append(bloom_table)
        story.append(Spacer(1, 0.3*inch))
        
        # NBA compliance check
        story.append(Paragraph("<b>NBA Compliance Analysis:</b>", styles['Heading2']))
        compliance_text = self._generate_compliance_text(distribution_data)
        story.append(Paragraph(compliance_text, styles['Normal']))
        
        # Charts (if requested)
        if include_charts:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("<b>Visual Distribution:</b>", styles['Heading2']))
            
            # Pie chart
            pie_chart = self._create_bloom_pie_chart(distribution_data)
            story.append(pie_chart)
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ Bloom report exported: {output_path}")
        
        return output_path
    
    def _generate_compliance_text(self, data: Dict) -> str:
        """Generate NBA compliance analysis text."""
        
        percentages = data['distribution_percentage']
        
        # NBA typically expects:
        # - Lower levels (L1-L2): 20-35%
        # - Middle levels (L3-L4): 40-50%
        # - Higher levels (L5-L6): 15-30%
        
        lower = percentages.get(1, 0) + percentages.get(2, 0)
        middle = percentages.get(3, 0) + percentages.get(4, 0)
        higher = percentages.get(5, 0) + percentages.get(6, 0)
        
        compliance_issues = []
        
        if lower < 20:
            compliance_issues.append("⚠️ Lower levels (Remember/Understand) below 20% - may need more foundational questions")
        elif lower > 35:
            compliance_issues.append("⚠️ Lower levels above 35% - assessment may be too basic")
        
        if middle < 40:
            compliance_issues.append("⚠️ Middle levels (Apply/Analyze) below 40% - core competency assessment insufficient")
        
        if higher < 15:
            compliance_issues.append("⚠️ Higher levels (Evaluate/Create) below 15% - lacks higher-order thinking assessment")
        
        if not compliance_issues:
            return "✅ <b>Bloom distribution meets NBA recommended guidelines</b><br/>" + \
                   f"Lower levels (L1-L2): {lower:.1f}%<br/>" + \
                   f"Middle levels (L3-L4): {middle:.1f}%<br/>" + \
                   f"Higher levels (L5-L6): {higher:.1f}%"
        else:
            return "<br/>".join(compliance_issues)
    
    def _create_bloom_pie_chart(self, data: Dict) -> Drawing:
        """Create pie chart for Bloom distribution."""
        
        drawing = Drawing(400, 200)
        
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 150
        pie.height = 150
        
        # Data
        levels = sorted(data['distribution_percentage'].keys())
        pie.data = [data['distribution_percentage'][l] for l in levels]
        pie.labels = [f"L{l}" for l in levels]
        
        # Colors
        colors_list = [
            colors.HexColor('#3498DB'),  # L1
            colors.HexColor('#2ECC71'),  # L2
            colors.HexColor('#F39C12'),  # L3
            colors.HexColor('#E74C3C'),  # L4
            colors.HexColor('#9B59B6'),  # L5
            colors.HexColor('#1ABC9C'),  # L6
        ]
        
        pie.slices.strokeWidth = 0.5
        for i, color in enumerate(colors_list[:len(levels)]):
            pie.slices[i].fillColor = color
        
        drawing.add(pie)
        
        return drawing