import React, { useState, useEffect } from 'react';
import { getAnalytics } from '../api/backend';
import Loader from '../components/Loader';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadAnalytics();
  }, []);
  
  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const result = await getAnalytics();
      setData(result);
      setError(null);
    } catch (err) {
      setError('Failed to load analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) return <Loader message="Loading analytics..." />;
  if (error) return <div className="text-red-600 text-center py-8">{error}</div>;
  if (!data) return null;
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Analytics & Reports</h1>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-l-4 border-blue-600">
          <div className="text-sm text-gray-600 mb-1">Total Questions</div>
          <div className="text-4xl font-bold text-blue-700">{data.total_questions}</div>
        </div>
        
        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-l-4 border-green-600">
          <div className="text-sm text-gray-600 mb-1">Avg NBA Score</div>
          <div className="text-4xl font-bold text-green-700">
            {data.average_compliance_score}%
          </div>
        </div>
        
        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-l-4 border-purple-600">
          <div className="text-sm text-gray-600 mb-1">Units</div>
          <div className="text-4xl font-bold text-purple-700">
            {Object.keys(data.unit_distribution || {}).length}
          </div>
        </div>
        
        <div className="card bg-gradient-to-br from-orange-50 to-orange-100 border-l-4 border-orange-600">
          <div className="text-sm text-gray-600 mb-1">Course Outcomes</div>
          <div className="text-4xl font-bold text-orange-700">
            {Object.keys(data.co_distribution || {}).length}
          </div>
        </div>
      </div>
      
      {/* Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bloom Level Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4">Bloom's Taxonomy Distribution</h3>
          <div className="space-y-3">
            {Object.entries(data.bloom_distribution || {}).map(([level, count]) => {
              const percentage = (count / data.total_questions) * 100;
              return (
                <div key={level}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">Level {level}</span>
                    <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Difficulty Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4">Difficulty Distribution</h3>
          <div className="space-y-3">
            {Object.entries(data.difficulty_distribution || {}).map(([diff, count]) => {
              const percentage = (count / data.total_questions) * 100;
              const color = diff === 'easy' ? 'green' : diff === 'medium' ? 'yellow' : 'red';
              return (
                <div key={diff}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700 capitalize">{diff}</span>
                    <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`bg-${color}-600 h-3 rounded-full transition-all duration-500`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Unit Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4">Unit Coverage</h3>
          <div className="space-y-3">
            {Object.entries(data.unit_distribution || {})
              .sort(([, a], [, b]) => b - a)
              .map(([unit, count]) => {
                const percentage = (count / data.total_questions) * 100;
                return (
                  <div key={unit}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{unit}</span>
                      <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-purple-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
        
        {/* CO Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4">Course Outcome Mapping</h3>
          <div className="space-y-3">
            {Object.entries(data.co_distribution || {})
              .sort(([, a], [, b]) => b - a)
              .map(([co, count]) => {
                const percentage = (count / data.total_questions) * 100;
                return (
                  <div key={co}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{co}</span>
                      <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-orange-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>
      
      {/* NBA Compliance Overview */}
      <div className="card bg-gradient-to-r from-green-50 to-emerald-50">
        <h3 className="text-xl font-semibold mb-4 text-green-900">
          NBA Compliance Overview
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-5xl font-bold text-green-700 mb-2">
              {data.average_compliance_score}%
            </div>
            <div className="text-sm text-gray-700">Average Compliance Score</div>
          </div>
          
          <div className="text-center">
            <div className="text-5xl font-bold text-blue-700 mb-2">
              {data.total_questions}
            </div>
            <div className="text-sm text-gray-700">Questions Validated</div>
          </div>
          
          <div className="text-center">
            <div className="text-5xl font-bold text-purple-700 mb-2">
              {Object.keys(data.bloom_distribution || {}).length}
            </div>
            <div className="text-sm text-gray-700">Bloom Levels Covered</div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-white rounded-lg border border-green-200">
          <h4 className="font-semibold text-green-900 mb-2">✅ Compliance Status</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• All questions validated against NBA standards</li>
            <li>• Multi-agent verification (Drafter, Critic, Guardian, Pedagogy)</li>
            <li>• Bloom's Taxonomy alignment verified</li>
            <li>• Course Outcome mapping validated</li>
          </ul>
        </div>
      </div>
      
      {/* Insights */}
      <div className="card">
        <h3 className="text-xl font-semibold mb-4">📊 Key Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="font-semibold text-blue-900 mb-2">Most Used Bloom Level</div>
            <div className="text-2xl font-bold text-blue-700">
              Level {Object.entries(data.bloom_distribution || {})
                .sort(([, a], [, b]) => b - a)[0]?.[0] || 'N/A'}
            </div>
          </div>
          
          <div className="p-4 bg-purple-50 rounded-lg">
            <div className="font-semibold text-purple-900 mb-2">Most Covered Unit</div>
            <div className="text-2xl font-bold text-purple-700">
              {Object.entries(data.unit_distribution || {})
                .sort(([, a], [, b]) => b - a)[0]?.[0] || 'N/A'}
            </div>
          </div>
          
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="font-semibold text-green-900 mb-2">Most Common Difficulty</div>
            <div className="text-2xl font-bold text-green-700 capitalize">
              {Object.entries(data.difficulty_distribution || {})
                .sort(([, a], [, b]) => b - a)[0]?.[0] || 'N/A'}
            </div>
          </div>
          
          <div className="p-4 bg-orange-50 rounded-lg">
            <div className="font-semibold text-orange-900 mb-2">Primary CO Focus</div>
            <div className="text-2xl font-bold text-orange-700">
              {Object.entries(data.co_distribution || {})
                .sort(([, a], [, b]) => b - a)[0]?.[0] || 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
