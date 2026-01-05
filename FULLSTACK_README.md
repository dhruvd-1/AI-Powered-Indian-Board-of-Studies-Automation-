# 🎓 AI-Powered Indian Board of Studies Automation - Full Stack Application

## 🚀 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND (Vite)                        │
│                    http://localhost:5173                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Pages: Dashboard, Generate Question, Question Bank,      │  │
│  │        QuestionDetail, Analytics                          │  │
│  │ Components: Navbar, QuestionCard, Loader, MetadataPanel  │  │
│  │ API Layer: Axios (backend.js)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                       REST API (HTTP)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                                │
│                  http://localhost:8000                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Endpoints: /api/health, /api/generate-question,         │  │
│  │           /api/questions, /api/analytics, /api/syllabus  │  │
│  │ CORS enabled for React frontend                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              AI PIPELINE (Multi-Agent System)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Document Processing (PDF → Chunks)                    │  │
│  │ 2. Vector Database (ChromaDB with RAG)                   │  │
│  │ 3. Question Generator (Multi-Agent):                     │  │
│  │    - Drafter Agent                                        │  │
│  │    - Critic Agent                                         │  │
│  │    - Guardian Agent (NBA Compliance)                     │  │
│  │    - Pedagogy Agent                                       │  │
│  │ 4. Question Bank Database (SQLite)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls

### Backend
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **CORS Middleware** - Cross-origin support

### AI/ML Pipeline
- **Ollama (llama3.2:3b)** - Local LLM for question generation
- **ChromaDB** - Vector database for RAG
- **Sentence Transformers** - Embedding model (all-MiniLM-L6-v2)
- **SQLite** - Question bank storage

## 🎯 Features

### ✅ Frontend Features
1. **Dashboard**
   - Real-time analytics overview
   - Recent questions display
   - Distribution charts (Bloom, Difficulty, Units, COs)
   - NBA compliance metrics

2. **Question Generation**
   - Interactive form with validation
   - Bloom's Taxonomy level selection (L1-L6)
   - Course Outcome mapping
   - Difficulty and marks configuration
   - Real-time AI generation with progress feedback

3. **Question Bank**
   - Paginated question list
   - Advanced filtering (Bloom level, difficulty, unit, CO)
   - Quick preview cards with metadata badges
   - Search and filter capabilities

4. **Question Details**
   - Full question display with answer scheme
   - RAG context visualization
   - Multi-agent reasoning breakdown
   - NBA compliance score (circular progress)
   - Metadata panel with all attributes
   - Validation warnings display

5. **Analytics**
   - Comprehensive distribution charts
   - Key insights and recommendations
   - Unit coverage analysis
   - CO mapping statistics

### ✅ Backend Features
1. **Health Monitoring** (`GET /api/health`)
   - Component status checks
   - Timestamp tracking
   - Syllabus validation

2. **Question Generation** (`POST /api/generate-question`)
   - Multi-agent orchestration
   - RAG-based context retrieval
   - NBA compliance validation
   - Database persistence

3. **Question Retrieval** (`GET /api/questions`)
   - Pagination support
   - Multiple filter options
   - Sorted by creation date

4. **Question Details** (`GET /api/questions/{id}`)
   - Complete question data
   - Agent reasoning
   - Context used

5. **Analytics** (`GET /api/analytics`)
   - Distribution statistics
   - Compliance scores
   - Coverage metrics

6. **Syllabus** (`GET /api/syllabus`)
   - Course structure
   - Unit information
   - CO mappings

## 🚀 Quick Start

### 1. Start FastAPI Backend

```powershell
cd "c:\Users\Aditya\Desktop\AI-Powered-Indian-Board-of-Studies-Automation-"

# Start in new PowerShell window (stays open)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='$PWD'; python -m uvicorn src.api.main:app --port 8000"
```

**Backend URL:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

### 2. Start React Frontend

```powershell
cd "c:\Users\Aditya\Desktop\AI-Powered-Indian-Board-of-Studies-Automation-\frontend"
npm run dev
```

**Frontend URL:** http://localhost:5173

### 3. Verify Health

```powershell
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-06T03:08:45.206264",
  "components": {
    "database": "operational",
    "vector_store": "operational",
    "question_generator": "operational",
    "syllabus": "4 units loaded"
  }
}
```

## 📁 Project Structure

```
AI-Powered-Indian-Board-of-Studies-Automation-/
├── src/
│   ├── api/                    # FastAPI REST API
│   │   ├── main.py            # API endpoints
│   │   └── __init__.py
│   ├── agents/                 # Multi-agent system
│   │   ├── base_agent.py
│   │   ├── drafter.py
│   │   ├── critic.py
│   │   ├── guardian.py
│   │   └── pedagogy.py
│   ├── data_processing/        # Document chunking
│   │   ├── chunker.py
│   │   ├── document_processor.py
│   │   └── syllabus_parser.py
│   ├── database/               # Question bank DB
│   │   ├── schema.py
│   │   └── question_bank.py
│   ├── orchestration/          # Question generation
│   │   ├── question_generator.py
│   │   └── question_pipeline.py
│   └── retrieval/              # RAG system
│       ├── vector_store.py
│       ├── embeddings.py
│       └── retriever.py
├── frontend/                   # React application
│   ├── src/
│   │   ├── api/
│   │   │   └── backend.js     # Axios API client
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Loader.jsx
│   │   │   ├── QuestionCard.jsx
│   │   │   └── MetadataPanel.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── GenerateQuestion.jsx
│   │   │   ├── QuestionBank.jsx
│   │   │   ├── QuestionDetail.jsx
│   │   │   └── Analytics.jsx
│   │   ├── App.jsx            # Main app with routing
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Tailwind styles
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── config/
│   ├── settings.py
│   └── prompts.py
├── data/
│   ├── raw/                   # PDF documents
│   ├── processed/             # Syllabus JSON
│   └── vector_dbs/           # ChromaDB persist
└── requirements.txt
```

## 🔧 Configuration

### Environment Variables (Optional)
```bash
PYTHONPATH=.
OLLAMA_HOST=http://localhost:11434
```

### Vite Proxy Configuration
File: `frontend/vite.config.js`
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### CORS Configuration
File: `src/api/main.py`
```python
allow_origins=[
  "http://localhost:5173",  # Vite dev server
  "http://localhost:3000"   # Alternative port
]
```

## 🎨 UI Screenshots

### Dashboard
- **Stats Cards:** Total questions, average NBA score, units covered, COs
- **Distribution Charts:** Bloom levels, difficulty, units, course outcomes
- **Recent Questions:** Quick access to latest generated questions

### Generate Question
- **Unit Selection:** Enter unit ID from syllabus
- **Bloom Level:** Radio buttons for L1-L6 with descriptions
- **Course Outcome:** CO mapping input
- **Difficulty:** Easy/Medium/Hard dropdown
- **Marks:** Number input (1-20)
- **Question Type:** Short answer, long answer, problem solving, case study

### Question Bank
- **Filters:** Bloom level, difficulty, unit ID, course outcome
- **Pagination:** Navigate through large question sets
- **Quick Cards:** Preview with badges for Bloom, difficulty, unit, CO
- **Search:** Filter questions by criteria

### Question Detail
- **Question Display:** Full text with formatting
- **Answer Scheme:** Detailed marking scheme
- **RAG Context:** Source material used
- **Agent Reasoning:** Breakdown by Drafter, Critic, Guardian, Pedagogy
- **NBA Score:** Circular progress indicator
- **Metadata:** All attributes in sidebar panel
- **Actions:** Copy, export PDF, generate similar

### Analytics
- **Distribution Charts:** Visual representation of all metrics
- **Key Insights:** Most used Bloom level, covered unit, common difficulty
- **NBA Compliance:** Overall compliance status and validation

## 📊 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /api/health
```
Response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-06T03:08:45",
  "components": {
    "database": "operational",
    "vector_store": "operational",
    "question_generator": "operational",
    "syllabus": "4 units loaded"
  }
}
```

#### 2. Generate Question
```http
POST /api/generate-question
Content-Type: application/json

{
  "unit_id": "unit_1",
  "bloom_level": 3,
  "course_outcome": "CO1",
  "difficulty": "medium",
  "marks": 5,
  "question_type": "short_answer"
}
```
Response:
```json
{
  "success": true,
  "message": "Question generated successfully",
  "question_id": 123,
  "question": {...}
}
```

#### 3. Get Questions
```http
GET /api/questions?page=1&limit=10&bloom_level=3&difficulty=medium
```
Response:
```json
{
  "questions": [...],
  "total": 50,
  "page": 1,
  "limit": 10
}
```

#### 4. Get Question Details
```http
GET /api/questions/123
```
Response:
```json
{
  "id": 123,
  "question_text": "...",
  "answer_scheme": "...",
  "bloom_level": 3,
  "difficulty": "medium",
  "context_used": "...",
  "agent_reasoning": {...},
  ...
}
```

#### 5. Get Analytics
```http
GET /api/analytics
```
Response:
```json
{
  "total_questions": 50,
  "average_compliance_score": 85,
  "bloom_distribution": {...},
  "difficulty_distribution": {...},
  "unit_distribution": {...},
  "co_distribution": {...}
}
```

#### 6. Get Syllabus
```http
GET /api/syllabus
```
Response:
```json
{
  "course_code": "AIML353",
  "course_title": "...",
  "units": [...]
}
```

## 🐛 Troubleshooting

### FastAPI Server Issues
1. **Server shuts down immediately**
   - Ensure syllabus JSON exists in `data/processed/`
   - Check Ollama is running: `ollama list`
   - Verify ChromaDB persistence directory exists

2. **Import errors**
   - Set PYTHONPATH: `$env:PYTHONPATH='.'`
   - Check all dependencies installed: `pip install -r requirements.txt`

3. **Port already in use**
   - Change port: `--port 8001`
   - Kill existing process: `Get-Process -Name python | Stop-Process`

### React Frontend Issues
1. **Cannot connect to API**
   - Verify backend is running on port 8000
   - Check vite.config.js proxy settings
   - Test API directly: `curl http://localhost:8000/api/health`

2. **Tailwind classes not working**
   - Run `npm install` to install dependencies
   - Verify tailwind.config.js and postcss.config.js exist
   - Check index.css has `@tailwind` directives

3. **Routing not working**
   - Verify React Router is installed: `npm list react-router-dom`
   - Check App.jsx has BrowserRouter wrapper
   - Ensure all page components are imported

### Common Errors
1. **"No syllabus JSON files found"**
   - Run chunking first: `python run_chunker.py`
   - Ensure PDFs in `data/raw/`

2. **"Vector store not found"**
   - Create vector DB: `python src/retrieval/vector_store.py`
   - Check `data/vector_dbs/` directory exists

3. **Ollama connection refused**
   - Start Ollama: `ollama serve`
   - Pull model: `ollama pull llama3.2:3b`

## 🎯 Testing the Full Stack

### End-to-End Test
1. Open browser to http://localhost:5173
2. Navigate to "Generate Question"
3. Fill form:
   - Unit ID: `unit_1`
   - Bloom Level: `L3 - Apply`
   - Course Outcome: `CO1`
   - Difficulty: `medium`
   - Marks: `5`
4. Click "Generate Question"
5. Wait for AI processing (multi-agent collaboration)
6. View generated question with all details
7. Check Dashboard for updated analytics
8. Browse Question Bank with filters

### API Test
```powershell
# Health check
curl http://localhost:8000/api/health

# Generate question
curl -X POST http://localhost:8000/api/generate-question `
  -H "Content-Type: application/json" `
  -d '{"unit_id":"unit_1","bloom_level":3,"course_outcome":"CO1","difficulty":"medium","marks":5,"question_type":"short_answer"}'

# Get questions
curl http://localhost:8000/api/questions

# Get analytics
curl http://localhost:8000/api/analytics
```

## 📝 Key Implementation Details

### 1. Lazy Initialization
- Backend components initialized on first API call
- Prevents startup failures from missing data
- Graceful error handling with HTTPException

### 2. CORS Configuration
- Allows React frontend to access FastAPI backend
- Configured for both common dev ports (5173, 3000)
- Credentials and all HTTP methods enabled

### 3. Component-Based Architecture
- Reusable React components for consistency
- Props-based data flow
- Single responsibility principle

### 4. API Layer Abstraction
- Axios client in `backend.js`
- Centralized error handling
- Consistent response format

### 5. State Management
- React useState for local component state
- useEffect for data fetching
- Loading and error states for all async operations

### 6. Tailwind CSS Utilities
- Custom utility classes in index.css
- Consistent badge and button styles
- Responsive grid layouts

## 🚀 Deployment Considerations

### Production Build
```bash
# Frontend
cd frontend
npm run build
# Outputs to frontend/dist/

# Backend
# Use gunicorn instead of uvicorn for production
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Variables
```bash
# Production
export PYTHONPATH=/app
export OLLAMA_HOST=http://ollama-server:11434
export DATABASE_PATH=/data/questions.db
export VECTOR_DB_PATH=/data/vector_dbs
```

## 🎓 Credits

**Full-Stack Implementation:** AI-powered with human verification  
**Backend Pipeline:** Multi-agent question generation system  
**Frontend:** Modern React with Tailwind CSS  
**AI/ML:** Ollama + ChromaDB + Sentence Transformers

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

**Status:** ✅ Fully Operational  
**Backend:** http://localhost:8000 ✅  
**Frontend:** http://localhost:5173 ✅  
**Last Updated:** January 6, 2026
