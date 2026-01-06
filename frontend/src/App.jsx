import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ContentHub from './pages/ContentHub';
import GenerateQuestion from './pages/GenerateQuestion';
import QuestionBank from './pages/QuestionBank';
import QuestionDetail from './pages/QuestionDetail';
import PaperGeneration from './pages/PaperGeneration';
import Analytics from './pages/Analytics';

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/content" element={<ContentHub />} />
            <Route path="/generate" element={<GenerateQuestion />} />
            <Route path="/questions" element={<QuestionBank />} />
            <Route path="/questions/:id" element={<QuestionDetail />} />
            <Route path="/paper" element={<PaperGeneration />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
