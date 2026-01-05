# Setup Instructions for Collaborators

## First Time Setup (For Your Friend)

### 1. Clone Repository
```bash
git clone <REPO_URL>
cd AI-Board-of-Studies-Automation
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Environment Setup
```bash
# Copy example env file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env if needed (default values work fine)
```

### 5. Download Ollama
- Install from: https://ollama.ai
- Pull model:
```bash
ollama pull llama3.2:3b
```

### 6. Initialize Database
```bash
# Add a sample PDF in data/raw/ folder
python build_vector_db.py
```

### 7. Run Application

**Terminal 1 (Backend):**
```bash
venv\Scripts\activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

**Access at:** http://localhost:5173

---

## Daily Workflow

### Before Starting Work:
```bash
# Pull latest changes
git pull origin main

# Activate venv
venv\Scripts\activate

# Install any new dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### After Making Changes:
```bash
# Check status
git status

# Add changes
git add .

# Commit with message
git commit -m "your message"

# Push
git push origin main
```

---

## Common Issues

### "Module not found" error:
```bash
pip install -r requirements.txt
```

### Frontend not loading:
```bash
cd frontend
npm install
```

### Ollama timeout:
- Check if Ollama is running
- Restart Ollama service

### Port already in use:
- Backend: Change port in command
- Frontend: Change in vite.config.ts

---

## Project Structure Quick Reference

```
src/api/main.py          → Backend API
frontend/src/App.jsx     → Frontend routes
config/settings.py       → Configuration
data/                    → Databases (not in git)
```

---

## Tips for Collaboration

1. **Always pull before starting work**
2. **Don't push data/ folder** (in .gitignore)
3. **Don't push venv/** (in .gitignore)
4. **Communicate before major changes**
5. **Test before pushing**

---

**Need Help?** Check README.md or contact project lead
