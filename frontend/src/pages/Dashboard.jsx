import React, { useState, useEffect } from 'react';
import { getHealth, getQuestions, getAnalytics } from '../api/backend';
import Loader from '../components/Loader';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [recentQuestions, setRecentQuestions] = useState([]);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadDashboard();
  }, []);
  
  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [analyticsData, questionsData] = await Promise.all([
        getAnalytics(),
        getQuestions({ limit: 5 })
      ]);
      
      setStats(analyticsData);
      setRecentQuestions(questionsData.questions || []);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) return <Loader message="Loading dashboard..." />;
  if (error) return <div className="text-red-600 text-center py-8">{error}</div>;
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <Link to="/generate" className="btn-primary">
          ✨ Generate New Question
        </Link>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-blue-50 border-l-4 border-blue-600">
          <div className="text-sm text-gray-600 mb-1">Total Questions</div>
          <div className="text-3xl font-bold text-blue-600">
            {stats?.total_questions || 0}
          </div>
        </div>
        
        <div className="card bg-green-50 border-l-4 border-green-600">
          <div className="text-sm text-gray-600 mb-1">Avg Compliance</div>
          <div className="text-3xl font-bold text-green-600">
            {stats?.average_compliance_score || 0}%
          </div>
        </div>
        
        <div className="card bg-purple-50 border-l-4 border-purple-600">
          <div className="text-sm text-gray-600 mb-1">Units Covered</div>
          <div className="text-3xl font-bold text-purple-600">
            {Object.keys(stats?.unit_distribution || {}).length}
          </div>
        </div>
        
        <div className="card bg-orange-50 border-l-4 border-orange-600">
          <div className="text-sm text-gray-600 mb-1">Course Outcomes</div>
          <div className="text-3xl font-bold text-orange-600">
            {Object.keys(stats?.co_distribution || {}).length}
          </div>
        </div>
      </div>
      
      {/* Distributions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Bloom Level Distribution</h3>
          <div className="space-y-2">
            {Object.entries(stats?.bloom_distribution || {}).map(([level, count]) => (
              <div key={level} className="flex justify-between items-center">
                <span className="text-gray-700">{level}</span>
                <div className="flex items-center gap-3">
                  <div className="w-48 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(count / stats.total_questions) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Difficulty Distribution</h3>
          <div className="space-y-2">
            {Object.entries(stats?.difficulty_distribution || {}).map(([diff, count]) => (
              <div key={diff} className="flex justify-between items-center">
                <span className="text-gray-700 capitalize">{diff}</span>
                <div className="flex items-center gap-3">
                  <div className="w-48 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        diff === 'easy' ? 'bg-green-600' :
                        diff === 'medium' ? 'bg-yellow-600' : 'bg-red-600'
                      }`}
                      style={{ width: `${(count / stats.total_questions) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Recent Questions */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Recent Questions</h3>
          <Link to="/questions" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            View All →
          </Link>
        </div>
        
        {recentQuestions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No questions generated yet. Start by generating your first question!
          </div>
        ) : (
          <div className="space-y-3">
            {recentQuestions.map((q) => (
              <Link 
                key={q.id}
                to={`/questions/${q.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <p className="text-gray-800 flex-1 line-clamp-2">{q.question_text}</p>
                  <span className="ml-4 text-xs text-gray-500">#{q.id}</span>
                </div>
                <div className="flex gap-2 text-xs">
                  <span className="badge badge-blue">Bloom L{q.bloom_level}</span>
                  <span className="badge badge-green">{q.unit_id}</span>
                  <span className="badge badge-yellow">{q.primary_co}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
