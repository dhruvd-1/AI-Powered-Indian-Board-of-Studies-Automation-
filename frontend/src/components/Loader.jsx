import React from 'react';

const Loader = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="loading-spinner"></div>
      <p className="mt-4 text-gray-600">{message}</p>
    </div>
  );
};

export default Loader;
