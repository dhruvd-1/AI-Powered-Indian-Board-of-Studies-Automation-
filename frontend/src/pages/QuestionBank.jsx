import React, { useState, useEffect } from 'react';
import { getQuestions } from '../api/backend';
import { Link } from 'react-router-dom';
import Loader from '../components/Loader';
import QuestionCard from '../components/QuestionCard';

const QuestionBank = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    bloom_level: '',
    difficulty: '',
    unit_id: '',
    course_outcome: ''
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0
  });
  
  useEffect(() => {
    loadQuestions();
  }, [filters, pagination.page]);
  
  const loadQuestions = async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        limit: pagination.limit,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      };
      
      const data = await getQuestions(params);
      setQuestions(data.questions || []);
      setPagination(prev => ({ ...prev, total: data.total || 0 }));
      setError(null);
    } catch (err) {
      setError('Failed to load questions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  };
  
  const clearFilters = () => {
    setFilters({
      bloom_level: '',
      difficulty: '',
      unit_id: '',
      course_outcome: ''
    });
  };
  
  const totalPages = Math.ceil(pagination.total / pagination.limit);
  
  if (loading && questions.length === 0) {
    return <Loader message="Loading question bank..." />;
  }
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Question Bank</h1>
          <p className="text-gray-600 mt-1">
            Total: {pagination.total} question{pagination.total !== 1 ? 's' : ''}
          </p>
        </div>
        <Link to="/generate" className="btn-primary">
          ✨ Generate New
        </Link>
      </div>
      
      {/* Filters */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bloom Level
            </label>
            <select
              name="bloom_level"
              value={filters.bloom_level}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="">All Levels</option>
              <option value="1">L1 - Remember</option>
              <option value="2">L2 - Understand</option>
              <option value="3">L3 - Apply</option>
              <option value="4">L4 - Analyze</option>
              <option value="5">L5 - Evaluate</option>
              <option value="6">L6 - Create</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Difficulty
            </label>
            <select
              name="difficulty"
              value={filters.difficulty}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Unit ID
            </label>
            <input
              type="text"
              name="unit_id"
              value={filters.unit_id}
              onChange={handleFilterChange}
              placeholder="e.g., unit_1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Course Outcome
            </label>
            <input
              type="text"
              name="course_outcome"
              value={filters.course_outcome}
              onChange={handleFilterChange}
              placeholder="e.g., CO1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
        </div>
        
        {Object.values(filters).some(v => v !== '') && (
          <button
            onClick={clearFilters}
            className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear Filters
          </button>
        )}
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-600 text-red-800">
          {error}
        </div>
      )}
      
      {/* Questions List */}
      {loading ? (
        <div className="text-center py-8">
          <Loader message="Filtering questions..." />
        </div>
      ) : questions.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">📝</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            No questions found
          </h3>
          <p className="text-gray-600 mb-4">
            {Object.values(filters).some(v => v !== '')
              ? 'Try adjusting your filters'
              : 'Start by generating your first question'}
          </p>
          <Link to="/generate" className="btn-primary inline-block">
            Generate Question
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((question) => (
            <QuestionCard key={question.id} question={question} />
          ))}
        </div>
      )}
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-6">
          <button
            onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          
          <div className="flex gap-1">
            {[...Array(totalPages)].map((_, idx) => {
              const pageNum = idx + 1;
              const isCurrentPage = pageNum === pagination.page;
              const showPage = 
                pageNum === 1 ||
                pageNum === totalPages ||
                Math.abs(pageNum - pagination.page) <= 1;
              
              if (!showPage && pageNum === 2) {
                return <span key={pageNum} className="px-2">...</span>;
              }
              if (!showPage && pageNum === totalPages - 1) {
                return <span key={pageNum} className="px-2">...</span>;
              }
              if (!showPage) return null;
              
              return (
                <button
                  key={pageNum}
                  onClick={() => setPagination(prev => ({ ...prev, page: pageNum }))}
                  className={`px-4 py-2 rounded-lg ${
                    isCurrentPage
                      ? 'bg-blue-600 text-white'
                      : 'border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => setPagination(prev => ({ ...prev, page: Math.min(totalPages, prev.page + 1) }))}
            disabled={pagination.page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default QuestionBank;
