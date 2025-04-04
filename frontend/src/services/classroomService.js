import apiClient from './api';

const classroomService = {
  // Fetch all courses for the logged-in user
  getCourses: async () => {
    try {
      const response = await apiClient.get('/classroom/courses');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch courses:', error.response?.data || error.message);
      throw error;
    }
  },

  // Fetch details for a specific course
  getCourse: async (courseId) => {
    try {
      const response = await apiClient.get(`/classroom/courses/${courseId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch course ${courseId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Fetch assignments for a specific course
  getAssignments: async (courseId) => {
    try {
      const response = await apiClient.get(`/classroom/courses/${courseId}/assignments`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch assignments for course ${courseId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Fetch details for a specific assignment
  getAssignment: async (assignmentId) => {
    try {
      const response = await apiClient.get(`/classroom/assignments/${assignmentId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch assignment ${assignmentId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Fetch materials for a specific assignment
  getMaterials: async (assignmentId) => {
    try {
      const response = await apiClient.get(`/classroom/assignments/${assignmentId}/materials`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch materials for assignment ${assignmentId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Add other classroom-related API calls here as needed
  // e.g., getAnnouncements, submitAssignment (once backend supports it)
};

export default classroomService;