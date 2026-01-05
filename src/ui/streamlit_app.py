"""
Step 20: Streamlit Web UI

Complete faculty interface for question generation, review, and paper creation.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import json
from datetime import datetime

from src.database.schema import QuestionBankDB
from src.retrieval.vector_store import VectorStoreManager
from src.orchestration.question_generator import QuestionGenerator
from src.paper.blueprint import PaperBlueprint, create_midterm_blueprint, create_final_blueprint
from src.paper.orchestrator import PaperOrchestrator
from src.nba.audit_report import NBAAuditReportGenerator
from src.preferences.learning import PreferenceLearner

from config.settings import DATA_DIR, PROCESSED_DATA_DIR


# Page config
st.set_page_config(
    page_title="AI Question Bank System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db' not in st.session_state:
    db_path = DATA_DIR / "question_bank.db"
    st.session_state.db = QuestionBankDB(db_path)

if 'faculty_id' not in st.session_state:
    st.session_state.faculty_id = 'faculty_demo'

if 'vector_manager' not in st.session_state:
    chunks_file = PROCESSED_DATA_DIR / "chunks.jsonl"
    if chunks_file.exists():
        st.session_state.vector_manager = VectorStoreManager(use_chromadb=False)
        st.session_state.vector_manager.build_from_chunks(chunks_file)
    else:
        st.session_state.vector_manager = None

if 'syllabus' not in st.session_state:
    structure_files = list(PROCESSED_DATA_DIR.glob("*_structure.json"))
    if structure_files:
        with open(structure_files[0], 'r') as f:
            st.session_state.syllabus = json.load(f)
    else:
        st.session_state.syllabus = None


def render_sidebar():
    """Render sidebar navigation."""
    
    with st.sidebar:
        st.title("🎓 AI Question Bank")
        
        st.markdown("---")
        
        # Faculty info
        st.write(f"**Faculty:** {st.session_state.faculty_id}")
        
        # Get preferences
        learner = PreferenceLearner(st.session_state.db)
        prefs = st.session_state.db.get_faculty_preferences(st.session_state.faculty_id)
        
        if prefs and prefs.total_reviews >= 20:
            st.success(f"✨ Personalization Active ({prefs.total_reviews} reviews)")
            st.caption(f"Acceptance rate: {prefs.acceptance_rate:.1%}")
        else:
            reviews_needed = 20 - (prefs.total_reviews if prefs else 0)
            st.info(f"📊 {reviews_needed} more reviews for personalization")
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            [
                "🏠 Dashboard",
                "➕ Generate Questions",
                "✅ Review Questions",
                "📄 Create Exam Paper",
                "📊 NBA Audit Reports",
                "⚙️ Settings"
            ]
        )
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("Quick Stats")
        
        pending = st.session_state.db.get_pending_questions()
        accepted = st.session_state.db.get_accepted_questions(st.session_state.faculty_id)
        
        col1, col2 = st.columns(2)
        col1.metric("Pending", len(pending))
        col2.metric("Accepted", len(accepted))
    
    return page


def render_dashboard():
    """Render main dashboard."""
    
    st.title("📊 Dashboard")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    all_questions = st.session_state.db.get_questions_by_filters(
        faculty_id=st.session_state.faculty_id
    )
    pending = st.session_state.db.get_pending_questions()
    accepted = st.session_state.db.get_accepted_questions(st.session_state.faculty_id)
    
    # Get papers count
    from sqlalchemy import text, func
    papers_count = st.session_state.db.session.execute(
        text("SELECT COUNT(*) FROM exam_papers")
    ).scalar()
    
    col1.metric("Total Questions", len(all_questions))
    col2.metric("Pending Review", len(pending))
    col3.metric("Accepted", len(accepted))
    col4.metric("Exam Papers", papers_count)
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("Recent Questions")
    
    recent = all_questions[:5]
    
    if recent:
        for q in recent:
            with st.expander(f"Q#{q.id} - {q.primary_co}, L{q.bloom_level}, {q.difficulty}"):
                st.write(q.question_text)
                
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Status:** {q.review_status}")
                col2.write(f"**Quality:** {q.quality_score:.0f}/100")
                col3.write(f"**Marks:** {q.marks}")
    else:
        st.info("No questions yet. Generate your first question!")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    if col1.button("➕ Generate Question", use_container_width=True):
        st.session_state.page = "➕ Generate Questions"
        st.rerun()
    
    if col2.button("✅ Review Questions", use_container_width=True):
        st.session_state.page = "✅ Review Questions"
        st.rerun()
    
    if col3.button("📄 Create Paper", use_container_width=True):
        st.session_state.page = "📄 Create Exam Paper"
        st.rerun()


def render_generate_questions():
    """Render question generation interface."""
    
    st.title("➕ Generate Questions")
    
    if not st.session_state.vector_manager or not st.session_state.syllabus:
        st.error("System not initialized. Please process syllabus and documents first.")
        return
    
    # Generation form
    with st.form("generate_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get units from syllabus
            units = [u['unit_id'] for u in st.session_state.syllabus['units']]
            unit_id = st.selectbox("Unit", units)
            
            cos = [co['co_id'] for co in st.session_state.syllabus['course_outcomes']]
            co_id = st.selectbox("Course Outcome", cos)
        
        with col2:
            bloom_level = st.selectbox("Bloom Level", [1, 2, 3, 4, 5, 6], index=1)
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        
        st.markdown("---")
        
        generate_count = st.number_input("Number of questions to generate", 1, 10, 1)
        
        submit = st.form_submit_button("🚀 Generate", use_container_width=True)
    
    if submit:
        # Initialize generator
        generator = QuestionGenerator(
            st.session_state.vector_manager,
            st.session_state.db,
            st.session_state.syllabus
        )
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i in range(generate_count):
            status_text.text(f"Generating question {i+1}/{generate_count}...")
            
            try:
                result = generator.generate_question(
                    unit_id=unit_id,
                    co_id=co_id,
                    bloom_level=bloom_level,
                    difficulty=difficulty,
                    faculty_id=st.session_state.faculty_id
                )
                
                results.append(result)
                
            except Exception as e:
                st.error(f"Error generating question {i+1}: {e}")
            
            progress_bar.progress((i + 1) / generate_count)
        
        status_text.text("✅ Generation complete!")
        
        # Show results
        st.success(f"Generated {len(results)} question(s)")
        
        for i, result in enumerate(results, 1):
            with st.expander(f"Question {i} - ID #{result['question_id']}", expanded=True):
                st.write(result['question_text'])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Quality Score", f"{result['quality_score']:.0f}/100")
                col2.metric("Compliance", f"{result['compliance_score']:.0f}/100")
                col3.metric("Status", "Pending Review")


def render_review_questions():
    """Render question review interface."""
    
    st.title("✅ Review Questions")
    
    pending = st.session_state.db.get_pending_questions()
    
    if not pending:
        st.success("🎉 No pending questions! All caught up.")
        return
    
    st.info(f"📝 {len(pending)} question(s) awaiting review")
    
    # Review interface
    for i, q in enumerate(pending):
        st.markdown("---")
        
        with st.container():
            st.subheader(f"Question #{q.id}")
            
            # Question details
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**Unit:** {q.unit_id}")
            col2.write(f"**CO:** {q.primary_co}")
            col3.write(f"**Bloom:** L{q.bloom_level}")
            col4.write(f"**Difficulty:** {q.difficulty}")
            
            # Question text
            st.markdown("### Question:")
            question_text = st.text_area(
                "Question text",
                value=q.question_text,
                key=f"q_text_{q.id}",
                height=150,
                label_visibility="collapsed"
            )
            
            # Metadata
            with st.expander("📊 View Metadata"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Quality Score:** {q.quality_score:.0f}/100")
                    st.write(f"**Compliance Score:** {q.compliance_score:.0f}/100")
                    st.write(f"**Type:** {q.question_type}")
                    st.write(f"**Marks:** {q.marks}")
                
                with col2:
                    st.write(f"**Refinements:** {q.refinement_count}")
                    st.write(f"**Created:** {q.created_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Sources
                    sources = json.loads(q.retrieval_sources) if isinstance(q.retrieval_sources, str) else q.retrieval_sources
                    st.write("**Sources:**")
                    for src in sources[:2]:
                        st.caption(f"• {src['file']} (p.{src['page']})")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
            
            if col1.button("✅ Accept", key=f"accept_{q.id}", use_container_width=True):
                st.session_state.db.update_question(q.id, {
                    'review_status': 'accepted',
                    'faculty_id': st.session_state.faculty_id,
                    'reviewed_at': datetime.now()
                })
                st.success("Question accepted!")
                st.rerun()
            
            if col2.button("✏️ Edit & Accept", key=f"edit_{q.id}", use_container_width=True):
                if question_text != q.question_text:
                    edits = {'type': 'text_modified', 'original': q.question_text, 'edited': question_text}
                    
                    st.session_state.db.update_question(q.id, {
                        'question_text': question_text,
                        'review_status': 'edited',
                        'faculty_id': st.session_state.faculty_id,
                        'faculty_edits': json.dumps(edits),
                        'reviewed_at': datetime.now()
                    })
                    st.success("Question edited and saved!")
                    st.rerun()
                else:
                    st.warning("No changes detected")
            
            if col3.button("❌ Reject", key=f"reject_{q.id}", use_container_width=True):
                st.session_state.db.update_question(q.id, {
                    'review_status': 'rejected',
                    'faculty_id': st.session_state.faculty_id,
                    'reviewed_at': datetime.now()
                })
                st.warning("Question rejected")
                st.rerun()


def render_create_paper():
    """Render exam paper creation interface."""
    
    st.title("📄 Create Exam Paper")
    
    # Mode selection
    mode = st.radio(
        "Generation Mode",
        ["Bank Only", "Fresh Generation", "Hybrid"],
        help="Bank Only: Use existing questions | Fresh: Generate new | Hybrid: Mix both"
    )
    
    st.markdown("---")
    
    # Paper configuration
    with st.form("paper_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            paper_name = st.text_input("Paper Name", "Midterm Examination")
            course_code = st.text_input("Course Code", "IS353IA")
            exam_type = st.selectbox("Exam Type", ["midterm", "final", "quiz", "assignment"])
        
        with col2:
            total_marks = st.number_input("Total Marks", 10, 100, 50, step=5)
            duration = st.number_input("Duration (minutes)", 30, 180, 90, step=15)
        
        st.markdown("### Blueprint")
        
        use_template = st.checkbox("Use template", value=True)
        
        if use_template:
            template = st.selectbox("Template", ["Midterm (50 marks)", "Final (100 marks)"])
        else:
            st.info("Manual blueprint configuration coming soon!")
        
        submit = st.form_submit_button("🚀 Generate Paper", use_container_width=True)
    
    if submit:
        with st.spinner("Generating exam paper..."):
            try:
                # Create blueprint
                if use_template:
                    if "Midterm" in template:
                        blueprint = create_midterm_blueprint(course_code)
                    else:
                        blueprint = create_final_blueprint(course_code)
                    
                    blueprint.paper_name = paper_name
                    blueprint.exam_type = exam_type
                
                # Initialize orchestrator
                if mode == "Fresh Generation" or mode == "Hybrid":
                    generator = QuestionGenerator(
                        st.session_state.vector_manager,
                        st.session_state.db,
                        st.session_state.syllabus
                    )
                    orchestrator = PaperOrchestrator(st.session_state.db, generator)
                else:
                    orchestrator = PaperOrchestrator(st.session_state.db)
                
                # Generate paper
                output_dir = DATA_DIR / "papers"
                output_dir.mkdir(exist_ok=True)
                
                if mode == "Bank Only":
                    pdf_path = orchestrator.generate_paper_from_bank(
                        blueprint=blueprint,
                        output_dir=output_dir,
                        faculty_id=st.session_state.faculty_id
                    )
                elif mode == "Fresh Generation":
                    pdf_path = orchestrator.generate_paper_fresh(
                        blueprint=blueprint,
                        output_dir=output_dir,
                        faculty_id=st.session_state.faculty_id
                    )
                else:  # Hybrid
                    pdf_path = orchestrator.generate_paper_hybrid(
                        blueprint=blueprint,
                        output_dir=output_dir,
                        faculty_id=st.session_state.faculty_id
                    )
                
                if pdf_path:
                    st.success("✅ Paper generated successfully!")
                    
                    # Download button
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            "📥 Download Paper",
                            f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf"
                        )
                else:
                    st.error("Failed to generate paper. Try a different mode or check question bank.")
            
            except Exception as e:
                st.error(f"Error: {e}")


def render_nba_reports():
    """Render NBA audit reports interface."""
    
    st.title("📊 NBA Audit Reports")
    
    # Get papers
    from sqlalchemy import text
    papers = st.session_state.db.session.execute(
        text("SELECT id, paper_name, course_code, total_marks FROM exam_papers ORDER BY created_at DESC")
    ).fetchall()
    
    if not papers:
        st.info("No exam papers yet. Create a paper first!")
        return
    
    # Select paper
    paper_options = {f"{p[1]} ({p[2]}) - {p[3]} marks": p[0] for p in papers}
    selected_paper_name = st.selectbox("Select Paper", list(paper_options.keys()))
    paper_id = paper_options[selected_paper_name]
    
    st.markdown("---")
    
    # Generate audit report
    if st.button("📄 Generate Complete NBA Audit Report", use_container_width=True):
        with st.spinner("Generating NBA audit report..."):
            try:
                generator = NBAAuditReportGenerator(st.session_state.db)
                
                output_dir = DATA_DIR / "nba_reports"
                output_dir.mkdir(exist_ok=True)
                
                output_path = output_dir / f"nba_audit_{paper_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generator.generate_complete_audit_report(
                    paper_id=paper_id,
                    output_path=output_path
                )
                
                st.success("✅ Audit report generated!")
                
                with open(output_path, 'rb') as f:
                    st.download_button(
                        "📥 Download NBA Audit Report",
                        f.read(),
                        file_name=output_path.name,
                        mime="application/pdf"
                    )
            
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Quick preview
    st.subheader("Quick Audit Preview")
    
    paper_obj = st.session_state.db.get_exam_paper(paper_id)
    
    if paper_obj:
        col1, col2, col3 = st.columns(3)
        
        # CO coverage
        with col1:
            st.write("**CO Coverage:**")
            co_coverage = json.loads(paper_obj.co_coverage) if isinstance(paper_obj.co_coverage, str) else paper_obj.co_coverage
            for co, marks in sorted(co_coverage.items()):
                st.write(f"• {co}: {marks} marks")
        
        # Bloom distribution
        with col2:
            st.write("**Bloom Distribution:**")
            bloom_dist = json.loads(paper_obj.bloom_distribution) if isinstance(paper_obj.bloom_distribution, str) else paper_obj.bloom_distribution
            bloom_names = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
            for level, marks in sorted(bloom_dist.items()):
                st.write(f"• L{level} ({bloom_names.get(int(level), 'Unknown')}): {marks} marks")
        
        # PO coverage
        with col3:
            st.write("**PO Coverage:**")
            po_coverage = json.loads(paper_obj.po_coverage) if isinstance(paper_obj.po_coverage, str) else paper_obj.po_coverage
            for po, marks in sorted(po_coverage.items())[:5]:
                st.write(f"• {po}: {marks} marks")


def render_settings():
    """Render settings interface."""
    
    st.title("⚙️ Settings")
    
    # Faculty preferences
    st.subheader("Faculty Preferences")
    
    prefs = st.session_state.db.get_faculty_preferences(st.session_state.faculty_id)
    
    if prefs:
        st.write(f"**Total Reviews:** {prefs.total_reviews}")
        st.write(f"**Acceptance Rate:** {prefs.acceptance_rate:.1%}")
        st.write(f"**Average Edits per Question:** {prefs.avg_edits_per_question:.1f}")
        
        if prefs.total_reviews >= 20:
            st.success("✨ Personalization is active!")
            
            # Show learned preferences
            with st.expander("View Learned Preferences"):
                learner = PreferenceLearner(st.session_state.db)
                summary = learner.get_preference_summary(st.session_state.faculty_id)
                st.code(summary)
        else:
            st.info(f"Review {20 - prefs.total_reviews} more questions to activate personalization")
    else:
        st.info("No preferences yet. Start reviewing questions to build your profile.")
    
    st.markdown("---")
    
    # System info
    st.subheader("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database:**")
        all_q = st.session_state.db.get_questions_by_filters()
        st.write(f"• Total questions: {len(all_q)}")
        
        from sqlalchemy import text
        papers_count = st.session_state.db.session.execute(text("SELECT COUNT(*) FROM exam_papers")).scalar()
        st.write(f"• Exam papers: {papers_count}")
    
    with col2:
        st.write("**Vector Store:**")
        if st.session_state.vector_manager:
            st.success("✅ Initialized")
        else:
            st.error("❌ Not initialized")
        
        st.write("**Syllabus:**")
        if st.session_state.syllabus:
            st.success(f"✅ Loaded ({len(st.session_state.syllabus['units'])} units)")
        else:
            st.error("❌ Not loaded")


def main():
    """Main app entry point."""
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "➕ Generate Questions":
        render_generate_questions()
    elif page == "✅ Review Questions":
        render_review_questions()
    elif page == "📄 Create Exam Paper":
        render_create_paper()
    elif page == "📊 NBA Audit Reports":
        render_nba_reports()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()
