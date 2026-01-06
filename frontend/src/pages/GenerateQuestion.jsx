import React, { useState } from 'react';
import { generateQuestion } from '../api/backend';
import { useNavigate } from 'react-router-dom';
import Loader from '../components/Loader';

const GenerateQuestion = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    unit_id: '',
    bloom_level: 3,
    co_id: '',
    difficulty: 'medium',
    faculty_id: 'default'
  });
  
  const bloomLevels = [
    { value: 1, label: 'L1 - Remember', desc: 'Recall facts and basic concepts' },
    { value: 2, label: 'L2 - Understand', desc: 'Explain ideas or concepts' },
    { value: 3, label: 'L3 - Apply', desc: 'Use information in new situations' },
    { value: 4, label: 'L4 - Analyze', desc: 'Draw connections among ideas' },
    { value: 5, label: 'L5 - Evaluate', desc: 'Justify a stand or decision' },
    { value: 6, label: 'L6 - Create', desc: 'Produce new or original work' }
  ];
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'bloom_level' || name === 'marks' ? parseInt(value) : value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const result = await generateQuestion(formData);
      
      if (result.success && result.question_id) {
        navigate(`/questions/${result.question_id}`);
      } else {
        setError(result.message || 'Failed to generate question');
      }
    } catch (err) {
      setError(err.message || 'An error occurred while generating the question');
      console.error('Generation error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return <Loader message="Generating question with AI agents..." />;
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Generate New Question</h1>
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-600 text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Unit Selection */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Unit ID *
          </label>
          <input
            type="text"
            name="unit_id"
            value={formData.unit_id}
            onChange={handleChange}
            required
            placeholder="e.g., unit_1, unit_2"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the unit identifier from the syllabus
          </p>
        </div>
        
        {/* Bloom Level Selection */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Bloom's Taxonomy Level *
          </label>
          <div className="space-y-2">
            {bloomLevels.map((level) => (
              <label 
                key={level.value}
                className={`flex items-start p-3 border rounded-lg cursor-pointer transition-all ${
                  formData.bloom_level === level.value
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="bloom_level"
                  value={level.value}
                  checked={formData.bloom_level === level.value}
                  onChange={handleChange}
                  className="mt-1 mr-3"
                />
                <div>
                  <div className="font-medium text-gray-800">{level.label}</div>
                  <div className="text-xs text-gray-600">{level.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>
        
        {/* Course Outcome */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Course Outcome (CO) *
          </label>
          <input
            type="text"
            name="co_id"
            value={formData.co_id}
            onChange={handleChange}
            required
            placeholder="e.g., CO1, CO2"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        {/* Difficulty */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Difficulty *
          </label>
          <select
            name="difficulty"
            value={formData.difficulty}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        
        {/* Submit Button */}
        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary flex-1"
          >
            {loading ? 'Generating...' : '✨ Generate Question'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary px-6"
          >
            Cancel
          </button>
        </div>
      </form>
      
      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">💡 How it works</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• AI agents analyze your syllabus and unit content</li>
          <li>• RAG retrieval finds relevant course material</li>
          <li>• Multiple agents collaborate (Drafter, Critic, Guardian, Pedagogy)</li>
          <li>• Questions are validated against NBA and compliance standards</li>
        </ul>
      </div>
    </div>
  );
};

export default GenerateQuestion;
