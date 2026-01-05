import React from 'react';

const MetadataPanel = ({ question }) => {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Metadata</h3>
      
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-600">Unit:</span>
          <span className="font-medium">{question.unit_name || question.unit_id}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Course Outcome:</span>
          <span className="font-medium">{question.primary_co}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Bloom Level:</span>
          <span className="font-medium">L{question.bloom_level}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Difficulty:</span>
          <span className="font-medium capitalize">{question.difficulty}</span>
        </div>
        
        {question.marks && (
          <div className="flex justify-between">
            <span className="text-gray-600">Marks:</span>
            <span className="font-medium">{question.marks}</span>
          </div>
        )}
        
        {question.compliance_score && (
          <div className="flex justify-between">
            <span className="text-gray-600">Compliance Score:</span>
            <span className="font-medium text-green-600">
              {question.compliance_score.toFixed(1)}%
            </span>
          </div>
        )}
        
        {question.created_at && (
          <div className="flex justify-between">
            <span className="text-gray-600">Generated:</span>
            <span className="font-medium text-sm">
              {new Date(question.created_at).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetadataPanel;
