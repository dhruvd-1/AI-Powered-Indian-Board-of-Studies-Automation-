import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getQuestionById } from '../api/backend';
import Loader from '../components/Loader';
import MetadataPanel from '../components/MetadataPanel';

const QuestionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [question, setQuestion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadQuestion();
  }, [id]);
  
  const loadQuestion = async () => {
    try {
      setLoading(true);
      const data = await getQuestionById(id);
      setQuestion(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load question');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) return <Loader message="Loading question details..." />;
  
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4 text-xl">⚠️ {error}</div>
        <Link to="/questions" className="btn-secondary">
          ← Back to Question Bank
        </Link>
      </div>
    );
  }
  
  if (!question) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-600 mb-4 text-xl">Question not found</div>
        <Link to="/questions" className="btn-secondary">
          ← Back to Question Bank
        </Link>
      </div>
    );
  }
  
  const metadata = {
    id: question.id,
    bloom_level: question.bloom_level,
    difficulty: question.difficulty,
    marks: question.marks,
    unit_id: question.unit_id,
    primary_co: question.primary_co,
    secondary_co: question.secondary_co,
    question_type: question.question_type,
    nba_compliance_score: question.nba_compliance_score,
    created_at: question.created_at
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Back
        </button>
        <span className="text-sm text-gray-500">Question #{question.id}</span>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Question Text */}
          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Question</h2>
              <div className="flex gap-2">
                <span className={`badge ${
                  question.difficulty === 'easy' ? 'badge-green' :
                  question.difficulty === 'medium' ? 'badge-yellow' : 'badge-red'
                }`}>
                  {question.difficulty}
                </span>
                <span className="badge badge-blue">
                  Bloom L{question.bloom_level}
                </span>
              </div>
            </div>
            
            <div className="prose max-w-none">
              <p className="text-gray-800 text-lg leading-relaxed whitespace-pre-wrap">
                {question.question_text}
              </p>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-sm text-gray-600">
              <span>Marks: <strong>{question.marks}</strong></span>
              <span className="capitalize">{question.question_type?.replace('_', ' ')}</span>
            </div>
          </div>
          
          {/* Answer Scheme */}
          {question.answer_scheme && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Answer Scheme</h3>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {question.answer_scheme}
                </p>
              </div>
            </div>
          )}
          
          {/* Context Used */}
          {question.context_used && (
            <div className="card bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                📚 Context Used (RAG Retrieval)
              </h3>
              <div className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-4 rounded border border-gray-200 max-h-64 overflow-y-auto">
                {question.context_used}
              </div>
            </div>
          )}
          
          {/* Agent Reasoning */}
          {question.agent_reasoning && (
            <div className="card bg-blue-50">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                🤖 Agent Reasoning
              </h3>
              <div className="space-y-2">
                {Object.entries(JSON.parse(question.agent_reasoning)).map(([agent, reasoning]) => (
                  <details key={agent} className="bg-white rounded border border-blue-200">
                    <summary className="px-4 py-2 cursor-pointer hover:bg-blue-50 font-medium text-gray-800">
                      {agent.charAt(0).toUpperCase() + agent.slice(1)} Agent
                    </summary>
                    <div className="px-4 py-3 text-sm text-gray-700 border-t border-blue-200">
                      {reasoning}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          )}
          
          {/* Validation Errors */}
          {question.validation_errors && (
            <div className="card border-l-4 border-orange-500 bg-orange-50">
              <h3 className="text-lg font-semibold text-orange-900 mb-3">
                ⚠️ Validation Warnings
              </h3>
              <ul className="list-disc list-inside text-sm text-orange-800 space-y-1">
                {question.validation_errors.split('\n').map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Sidebar - Metadata */}
        <div className="lg:col-span-1">
          <MetadataPanel metadata={metadata} />
          
          {/* NBA Compliance */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              NBA Compliance
            </h3>
            <div className="flex items-center justify-center">
              <div className="relative w-32 h-32">
                <svg className="transform -rotate-90 w-32 h-32">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="#10b981"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${(question.nba_compliance_score / 100) * 351.86} 351.86`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-3xl font-bold text-gray-800">
                    {question.nba_compliance_score}%
                  </span>
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-600 text-center mt-3">
              Alignment with NBA standards
            </p>
          </div>
          
          {/* Actions */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Actions</h3>
            <div className="space-y-2">
              <button className="w-full btn-secondary text-sm">
                📋 Copy Question
              </button>
              <button className="w-full btn-secondary text-sm">
                📄 Export as PDF
              </button>
              <button className="w-full btn-secondary text-sm">
                🔄 Generate Similar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionDetail;
