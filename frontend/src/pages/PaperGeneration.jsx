import React, { useState, useEffect } from 'react';
import { getSyllabus, generatePaper } from '../api/backend';
import Loader from '../components/Loader';

const PaperGeneration = () => {
  const [syllabus, setSyllabus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [formData, setFormData] = useState({
    paperName: '',
    examType: 'midterm',
    totalMarks: 100,
    duration: 180,
    academicYear: new Date().getFullYear().toString(),
    semester: '1',
    mode: 'bank', // bank, fresh, or hybrid
    bloomDistribution: {
      L1: 10,
      L2: 20,
      L3: 30,
      L4: 20,
      L5: 15,
      L6: 5
    }
  });

  useEffect(() => {
    loadSyllabus();
  }, []);

  const loadSyllabus = async () => {
    try {
      setLoading(true);
      const data = await getSyllabus();
      setSyllabus(data);
      setError(null);
    } catch (err) {
      setError('Failed to load syllabus');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await generatePaper(formData);
      setSuccess(`Paper "${formData.paperName}" generated successfully!`);
      // Reset form
      setFormData({ ...formData, paperName: '' });
    } catch (err) {
      setError('Failed to generate paper: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleBloomChange = (level, value) => {
    setFormData(prev => ({
      ...prev,
      bloomDistribution: { ...prev.bloomDistribution, [level]: parseInt(value) || 0 }
    }));
  };

  const getTotalBloomPercentage = () => {
    return Object.values(formData.bloomDistribution).reduce((a, b) => a + b, 0);
  };

  if (loading) return <Loader message="Loading syllabus..." />;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="section-header">Create Exam Paper</h1>
        <p className="text-gray-600">
          Generate exam papers from question bank with customizable constraints
        </p>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Paper Details */}
        <div className="card">
          <h2 className="section-subheader">Paper Details</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Paper Name *</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., Midterm Exam 2024"
                value={formData.paperName}
                onChange={(e) => handleChange('paperName', e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label">Exam Type *</label>
              <select
                className="select"
                value={formData.examType}
                onChange={(e) => handleChange('examType', e.target.value)}
              >
                <option value="midterm">Midterm</option>
                <option value="final">Final</option>
                <option value="quiz">Quiz</option>
                <option value="assignment">Assignment</option>
              </select>
            </div>

            <div>
              <label className="label">Total Marks *</label>
              <input
                type="number"
                className="input"
                min="1"
                max="200"
                value={formData.totalMarks}
                onChange={(e) => handleChange('totalMarks', parseInt(e.target.value))}
                required
              />
            </div>

            <div>
              <label className="label">Duration (minutes) *</label>
              <input
                type="number"
                className="input"
                min="30"
                max="300"
                value={formData.duration}
                onChange={(e) => handleChange('duration', parseInt(e.target.value))}
                required
              />
            </div>

            <div>
              <label className="label">Academic Year *</label>
              <input
                type="text"
                className="input"
                placeholder="2024"
                value={formData.academicYear}
                onChange={(e) => handleChange('academicYear', e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label">Semester *</label>
              <select
                className="select"
                value={formData.semester}
                onChange={(e) => handleChange('semester', e.target.value)}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
                  <option key={sem} value={sem}>{sem}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Generation Mode */}
        <div className="card">
          <h2 className="section-subheader">Generation Mode</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className={`card-hover cursor-pointer border-2 ${formData.mode === 'bank' ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200'}`}>
              <input
                type="radio"
                name="mode"
                value="bank"
                checked={formData.mode === 'bank'}
                onChange={(e) => handleChange('mode', e.target.value)}
                className="hidden"
              />
              <div className="text-center">
                <div className="text-4xl mb-2">📚</div>
                <h3 className="font-semibold text-gray-900 mb-1">From Bank</h3>
                <p className="text-sm text-gray-600">Use existing questions only (2-3 sec)</p>
              </div>
            </label>

            <label className={`card-hover cursor-pointer border-2 ${formData.mode === 'fresh' ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200'}`}>
              <input
                type="radio"
                name="mode"
                value="fresh"
                checked={formData.mode === 'fresh'}
                onChange={(e) => handleChange('mode', e.target.value)}
                className="hidden"
              />
              <div className="text-center">
                <div className="text-4xl mb-2">✨</div>
                <h3 className="font-semibold text-gray-900 mb-1">Fresh Generation</h3>
                <p className="text-sm text-gray-600">Generate all new questions (30-60 sec)</p>
              </div>
            </label>

            <label className={`card-hover cursor-pointer border-2 ${formData.mode === 'hybrid' ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200'}`}>
              <input
                type="radio"
                name="mode"
                value="hybrid"
                checked={formData.mode === 'hybrid'}
                onChange={(e) => handleChange('mode', e.target.value)}
                className="hidden"
              />
              <div className="text-center">
                <div className="text-4xl mb-2">🔄</div>
                <h3 className="font-semibold text-gray-900 mb-1">Hybrid</h3>
                <p className="text-sm text-gray-600">Mix of bank + fresh (15-30 sec)</p>
              </div>
            </label>
          </div>
        </div>

        {/* Bloom's Taxonomy Distribution */}
        <div className="card">
          <h2 className="section-subheader">Bloom's Taxonomy Distribution</h2>

          <div className="space-y-4">
            {Object.entries(formData.bloomDistribution).map(([level, percentage]) => (
              <div key={level}>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">{level}</label>
                  <span className="text-sm text-gray-600">{percentage}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={percentage}
                  onChange={(e) => handleBloomChange(level, e.target.value)}
                  className="w-full"
                />
              </div>
            ))}

            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <span className="font-semibold">Total:</span>
              <span className={`font-bold ${getTotalBloomPercentage() === 100 ? 'text-green-600' : 'text-red-600'}`}>
                {getTotalBloomPercentage()}%
              </span>
            </div>

            {getTotalBloomPercentage() !== 100 && (
              <div className="alert alert-warning">
                Bloom distribution must total 100%
              </div>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-4">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => window.location.reload()}
          >
            Reset
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={generating || getTotalBloomPercentage() !== 100 || !formData.paperName}
          >
            {generating ? (
              <>
                <span className="loading-spinner-sm mr-2"></span>
                Generating...
              </>
            ) : (
              <>
                <span className="mr-2">🚀</span>
                Generate Paper
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PaperGeneration;
