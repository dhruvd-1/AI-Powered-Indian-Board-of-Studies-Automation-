import React, { useState, useEffect } from 'react';
import { generateQuestion, getSyllabus } from '../api/backend';
import { useNavigate } from 'react-router-dom';
import Loader from '../components/Loader';

const GenerateQuestion = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [syllabus, setSyllabus] = useState(null);
  const [loadingSyllabus, setLoadingSyllabus] = useState(true);
  const [formData, setFormData] = useState({
    unit_id: '',
    bloom_level: 3,
    co_id: '',
    difficulty: 'medium',
    faculty_id: 'default'
  });

  // Fetch syllabus on mount
  useEffect(() => {
    const fetchSyllabus = async () => {
      try {
        const data = await getSyllabus();
        setSyllabus(data);
      } catch (err) {
        console.error('Failed to load syllabus:', err);
        setError('Failed to load syllabus structure. Please ensure the backend is running.');
      } finally {
        setLoadingSyllabus(false);
      }
    };

    fetchSyllabus();
  }, []);
  
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

  if (loadingSyllabus) {
    return <Loader message="Loading syllabus..." />;
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
        {/* Course Info */}
        {syllabus && (
          <div className="p-4 bg-gradient-to-r from-indigo-50 to-violet-50 rounded-lg border border-indigo-200">
            <h3 className="font-semibold text-indigo-900">{syllabus.course_code} - {syllabus.course_name}</h3>
            <p className="text-sm text-indigo-700 mt-1">{syllabus.credits} Credits</p>
          </div>
        )}

        {/* Unit Selection */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Unit *
          </label>
          <select
            name="unit_id"
            value={formData.unit_id}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select a unit...</option>
            {syllabus?.units?.map((unit) => (
              <option key={unit.unit_id} value={unit.unit_id}>
                {unit.unit_name} ({unit.hours} hours)
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Select the syllabus unit for this question
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
          <select
            name="co_id"
            value={formData.co_id}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select a course outcome...</option>
            {syllabus?.course_outcomes?.map((co) => (
              <option key={co.co_id} value={co.co_id}>
                {co.co_id}: {co.description}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Select the learning outcome this question addresses
          </p>
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
