import React from 'react';
import { Link } from 'react-router-dom';

const QuestionCard = ({ question }) => {
  const bloomColors = {
    1: 'bg-green-100 text-green-800',
    2: 'bg-blue-100 text-blue-800',
    3: 'bg-yellow-100 text-yellow-800',
    4: 'bg-orange-100 text-orange-800',
    5: 'bg-red-100 text-red-800',
    6: 'bg-purple-100 text-purple-800',
  };
  
  const difficultyColors = {
    easy: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    hard: 'bg-red-100 text-red-800',
  };
  
  return (
    <div className="card hover:scale-[1.01] transition-transform">
      <div className="flex justify-between items-start mb-3">
        <div className="flex gap-2">
          <span className={`badge ${bloomColors[question.bloom_level] || 'badge-blue'}`}>
            Bloom L{question.bloom_level}
          </span>
          <span className={`badge ${difficultyColors[question.difficulty] || 'badge-yellow'}`}>
            {question.difficulty}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          #{question.id}
        </span>
      </div>
      
      <p className="text-gray-800 mb-3 line-clamp-3">
        {question.question_text}
      </p>
      
      <div className="flex justify-between items-center text-sm text-gray-600">
        <div className="flex gap-3">
          <span>📚 {question.unit_id}</span>
          <span>🎯 {question.primary_co}</span>
          {question.marks && <span>📊 {question.marks} marks</span>}
        </div>
        <Link 
          to={`/questions/${question.id}`}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          View Details →
        </Link>
      </div>
      
      {question.compliance_score && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Compliance Score:</span>
            <span className="font-semibold text-green-600">
              {question.compliance_score.toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuestionCard;
