import React, { useState, useEffect } from 'react';
import { getDocuments, uploadDocument, deleteDocument } from '../api/backend';
import Loader from '../components/Loader';

const ContentHub = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await getDocuments();
      setDocuments(data.documents || []);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      for (const file of files) {
        await uploadDocument(file);
      }
      await loadDocuments();
    } catch (err) {
      setError('Failed to upload file: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(docId);
      await loadDocuments();
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(Array.from(e.dataTransfer.files));
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getFileIcon = (filename) => {
    if (filename.endsWith('.pdf')) return '📄';
    if (filename.endsWith('.doc') || filename.endsWith('.docx')) return '📝';
    if (filename.endsWith('.txt')) return '📃';
    if (filename.endsWith('.json')) return '🔧';
    return '📎';
  };

  if (loading) return <Loader message="Loading documents..." />;

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-header">Content Hub</h1>
          <p className="text-gray-600">
            Manage your syllabus documents and course materials
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Upload Zone */}
      <div
        className={`upload-zone ${dragActive ? 'upload-zone-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.json"
          className="hidden"
          onChange={(e) => handleFileUpload(Array.from(e.target.files))}
        />

        <div className="text-6xl mb-4">{uploading ? '⏳' : '📁'}</div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          {uploading ? 'Uploading...' : 'Upload Documents'}
        </h3>
        <p className="text-gray-500 mb-4">
          Drag and drop files here, or click to browse
        </p>
        <p className="text-sm text-gray-400">
          Supported formats: PDF, DOC, DOCX, TXT, JSON
        </p>
      </div>

      {/* Documents List */}
      <div className="card">
        <h2 className="section-subheader">Uploaded Documents ({documents.length})</h2>

        {documents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📂</div>
            <h3 className="empty-state-title">No documents yet</h3>
            <p className="empty-state-text">
              Upload your syllabus PDFs and course materials to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="card-hover border-2 border-gray-100 p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="text-4xl">{getFileIcon(doc.filename)}</div>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="btn-icon text-red-500 hover:bg-red-50"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>

                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                  {doc.filename}
                </h3>

                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex items-center justify-between">
                    <span>Size:</span>
                    <span className="font-medium">{formatFileSize(doc.size)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Type:</span>
                    <span className="font-medium">{doc.type || 'Document'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Uploaded:</span>
                    <span className="font-medium">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {doc.processed && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <span className="badge badge-green">✓ Processed</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Processing Instructions */}
      <div className="card bg-indigo-50 border-indigo-200">
        <h3 className="font-semibold text-indigo-900 mb-2 flex items-center gap-2">
          <span>ℹ️</span>
          How it works
        </h3>
        <ol className="space-y-2 text-sm text-indigo-800">
          <li><strong>1. Upload:</strong> Upload your syllabus PDF files</li>
          <li><strong>2. Processing:</strong> System extracts content and creates embeddings</li>
          <li><strong>3. Ready:</strong> Generate AI questions based on uploaded content</li>
        </ol>
      </div>
    </div>
  );
};

export default ContentHub;
