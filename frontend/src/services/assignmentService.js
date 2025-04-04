import apiClient from './api';

const assignmentService = {
  // Create a new draft manually
  createDraft: async (assignmentId, content, status = 'draft') => {
    try {
      const response = await apiClient.post('/assignments/drafts', {
        assignment_id: assignmentId,
        content,
        status,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create draft:', error.response?.data || error.message);
      throw error;
    }
  },

  // Get all drafts for a specific assignment
  getDraftsForAssignment: async (assignmentId) => {
    try {
      const response = await apiClient.get(`/assignments/assignments/${assignmentId}/drafts`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get drafts for assignment ${assignmentId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Get a specific draft by ID
  getDraft: async (draftId) => {
    try {
      const response = await apiClient.get(`/assignments/drafts/${draftId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get draft ${draftId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Update an existing draft
  updateDraft: async (draftId, content, status, feedback) => {
    try {
      const response = await apiClient.put(`/assignments/drafts/${draftId}`, {
        content,
        status,
        feedback,
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to update draft ${draftId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Trigger AI generation for an assignment
  generateAssignmentDraft: async (assignmentId, parameters = {}) => {
    try {
      const response = await apiClient.post(`/assignments/assignments/${assignmentId}/generate`, {
        assignment_id: assignmentId,
        parameters,
      });
      // This returns the initial draft object with status 'generating'
      return response.data; 
    } catch (error) {
      console.error(`Failed to trigger AI generation for assignment ${assignmentId}:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Export a draft as PDF
  exportDraftToPdf: async (draftId) => {
    try {
      const response = await apiClient.post(`/assignments/drafts/${draftId}/export-pdf`, {}, {
        responseType: 'blob', // Important to handle binary file data
      });
      // Create a URL for the blob object
      const file = new Blob([response.data], { type: 'application/pdf' });
      const fileURL = URL.createObjectURL(file);
      // Trigger download (or return URL for display/linking)
      // Example: Trigger download
      const link = document.createElement('a');
      link.href = fileURL;
      // Extract filename from content-disposition header if available, otherwise use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = `draft_${draftId}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      URL.revokeObjectURL(fileURL); // Clean up blob URL

      return { success: true, filename };
    } catch (error) {
      console.error(`Failed to export draft ${draftId} to PDF:`, error.response?.data || error.message);
      throw error;
    }
  },

  // Submit a draft to Google Classroom (currently mocked in backend)
  submitDraft: async (draftId) => {
    try {
      const response = await apiClient.post(`/assignments/drafts/${draftId}/submit`);
      return response.data;
    } catch (error) {
      console.error(`Failed to submit draft ${draftId}:`, error.response?.data || error.message);
      throw error;
    }
  },
};

export default assignmentService;