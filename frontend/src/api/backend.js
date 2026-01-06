/**
 * API Integration Layer
 * Communicates with FastAPI backend
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Generate question
export const generateQuestion = async (payload) => {
  const response = await api.post('/generate-question', payload);
  return response.data;
};

// Get all questions
export const getQuestions = async (filters = {}) => {
  const response = await api.get('/questions', { params: filters });
  return response.data;
};

// Get question by ID
export const getQuestionById = async (id) => {
  const response = await api.get(`/questions/${id}`);
  return response.data;
};

// Get analytics
export const getAnalytics = async () => {
  const response = await api.get('/analytics');
  return response.data;
};

// Get syllabus
export const getSyllabus = async () => {
  const response = await api.get('/syllabus');
  return response.data;
};

// File Management
export const getDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteDocument = async (docId) => {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
};

// Paper Generation
export const generatePaper = async (paperData) => {
  const response = await api.post('/papers/generate', paperData);
  return response.data;
};

export const getPapers = async () => {
  const response = await api.get('/papers');
  return response.data;
};

export const getPaperById = async (paperId) => {
  const response = await api.get(`/papers/${paperId}`);
  return response.data;
};

export default api;
