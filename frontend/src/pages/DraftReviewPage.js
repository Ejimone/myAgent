import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import assignmentService from '../services/assignmentService';
import classroomService from '../services/classroomService'; // To get assignment details

function DraftReviewPage() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [editableContent, setEditableContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false); // For button loading states
  const [notification, setNotification] = useState('');

  // Fetch assignment details and drafts on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError('');
      setNotification('');
      try {
        // Fetch assignment details (optional, but good for context)
        // Note: Backend endpoint /classroom/assignments/{id} needs to be implemented or adjusted
        // For now, we might skip fetching assignment details if not strictly needed for draft review
        // const fetchedAssignment = await classroomService.getAssignment(assignmentId);
        // setAssignment(fetchedAssignment);

        // Fetch drafts for this assignment
        // Note: Backend endpoint /assignments/assignments/{id}/drafts needs adjustment
        // Assuming it should be /assignments/{assignmentId}/drafts
        const fetchedDrafts = await assignmentService.getDraftsForAssignment(assignmentId);
        setDrafts(fetchedDrafts || []);
        
        // Select the first draft by default if available
        if (fetchedDrafts && fetchedDrafts.length > 0) {
          setSelectedDraft(fetchedDrafts[0]);
          setEditableContent(fetchedDrafts[0].content);
        }

      } catch (err) {
        console.error('Failed to load draft data:', err);
        setError('Failed to load assignment drafts. Please go back and try again.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [assignmentId]);

  // Update editable content when selected draft changes
  useEffect(() => {
    if (selectedDraft) {
      setEditableContent(selectedDraft.content);
    }
  }, [selectedDraft]);

  const handleDraftSelect = (draft) => {
    setSelectedDraft(draft);
    setNotification(''); // Clear notifications on selection change
  };

  const handleContentChange = (e) => {
    setEditableContent(e.target.value);
  };

  const handleSaveChanges = async () => {
    if (!selectedDraft) return;
    setActionLoading(true);
    setError('');
    setNotification('');
    try {
      const updatedDraft = await assignmentService.updateDraft(
        selectedDraft.id,
        editableContent,
        selectedDraft.status, // Keep existing status for now
        selectedDraft.feedback // Keep existing feedback
      );
      // Update local state
      setDrafts(drafts.map(d => d.id === updatedDraft.id ? updatedDraft : d));
      setSelectedDraft(updatedDraft);
      setNotification('Draft saved successfully!');
    } catch (err) {
      setError('Failed to save changes.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!selectedDraft) return;
    setActionLoading(true);
    setError('');
    setNotification('');
    try {
      await assignmentService.exportDraftToPdf(selectedDraft.id);
      setNotification('PDF export started. Check your downloads.');
    } catch (err) {
      setError('Failed to export PDF.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedDraft) return;
    setActionLoading(true);
    setError('');
    setNotification('');
    try {
      // TODO: Add confirmation step before submitting
      const result = await assignmentService.submitDraft(selectedDraft.id);
      // Update draft status locally
      const updatedDraft = { ...selectedDraft, status: 'submitted', submission_date: result.submission_date };
      setDrafts(drafts.map(d => d.id === updatedDraft.id ? updatedDraft : d));
      setSelectedDraft(updatedDraft);
      setNotification('Draft submitted successfully!');
    } catch (err) {
      setError('Failed to submit draft.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div>Loading drafts...</div>;
  }

  return (
    <div>
      <button onClick={() => navigate('/dashboard')} style={{ marginBottom: '15px' }}>Back to Dashboard</button>
      {/* Display assignment title if fetched */}
      {/* <h2>Drafts for: {assignment ? assignment.title : `Assignment ${assignmentId}`}</h2> */} 
      <h2>Drafts for Assignment {assignmentId}</h2>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {notification && <p style={{ color: 'green' }}>{notification}</p>}

      <div style={{ display: 'flex', marginTop: '20px' }}>
        {/* Draft List */}
        <div style={{ width: '30%', borderRight: '1px solid #ccc', paddingRight: '15px' }}>
          <h3>Available Drafts</h3>
          {drafts.length > 0 ? (
            <ul>
              {drafts.map((draft) => (
                <li 
                  key={draft.id} 
                  onClick={() => handleDraftSelect(draft)}
                  style={{
                    cursor: 'pointer', 
                    fontWeight: selectedDraft?.id === draft.id ? 'bold' : 'normal',
                    marginBottom: '5px'
                  }}
                >
                  Draft {draft.id} (Status: {draft.status})
                  <br />
                  <small>Created: {new Date(draft.created_at).toLocaleString()}</small>
                </li>
              ))}
            </ul>
          ) : (
            <p>No drafts found for this assignment.</p>
          )}
        </div>

        {/* Draft Editor/Viewer */}
        <div style={{ width: '70%', paddingLeft: '15px' }}>
          <h3>Draft Content</h3>
          {selectedDraft ? (
            <div>
              <textarea 
                value={editableContent}
                onChange={handleContentChange}
                rows={20}
                style={{ width: '100%', marginBottom: '10px' }}
                disabled={actionLoading || selectedDraft.status === 'submitted'}
              />
              <div>
                <button 
                  onClick={handleSaveChanges} 
                  disabled={actionLoading || selectedDraft.content === editableContent || selectedDraft.status === 'submitted'}
                  style={{ marginRight: '10px' }}
                >
                  {actionLoading ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  onClick={handleExportPdf} 
                  disabled={actionLoading}
                  style={{ marginRight: '10px' }}
                >
                  {actionLoading ? 'Exporting...' : 'Export as PDF'}
                </button>
                <button 
                  onClick={handleSubmit} 
                  disabled={actionLoading || selectedDraft.status === 'submitted'}
                >
                  {actionLoading ? 'Submitting...' : (selectedDraft.status === 'submitted' ? 'Submitted' : 'Submit to Classroom')}
                </button>
              </div>
              {selectedDraft.status === 'submitted' && 
                <p style={{ marginTop: '10px', color: 'green' }}>
                  Submitted on: {new Date(selectedDraft.submission_date).toLocaleString()}
                </p>
              }
            </div>
          ) : (
            <p>Select a draft from the list to view or edit.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default DraftReviewPage;