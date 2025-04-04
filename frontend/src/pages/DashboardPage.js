import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import classroomService from '../services/classroomService';
import assignmentService from '../services/assignmentService'; // Import assignment service

function DashboardPage() {
  const [user, setUser] = useState({ fullName: 'Loading...' }); // Initialize user state
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generatingDraftId, setGeneratingDraftId] = useState(null); // Track generating state
  const [notification, setNotification] = useState(''); // For user feedback
  const navigate = useNavigate();

  useEffect(() => {
    const loadDashboardData = async () => {
      setError('');
      setLoading(true);
      try {
        if (!authService.isAuthenticated()) {
          navigate('/login');
          return;
        }

        // Fetch user info (placeholder for now)
        // TODO: Replace with actual user fetching once backend /auth/me is ready
        setUser({ fullName: 'Demo User' }); 

        // Fetch courses
        const fetchedCourses = await classroomService.getCourses();
        setCourses(fetchedCourses || []);

      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to load data. Please try logging in again.');
        // Optional: Logout if fetching fails critically
        // authService.logout();
        // navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [navigate]);

  // Fetch assignments when a course is selected
  useEffect(() => {
    const loadAssignments = async () => {
      if (!selectedCourse) {
        setAssignments([]);
        return;
      }
      setError('');
      try {
        const fetchedAssignments = await classroomService.getAssignments(selectedCourse.id);
        setAssignments(fetchedAssignments || []);
      } catch (err) {
        console.error(`Failed to load assignments for course ${selectedCourse.id}:`, err);
        setError('Failed to load assignments for the selected course.');
      }
    };

    loadAssignments();
  }, [selectedCourse]);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleCourseSelect = (course) => {
    setSelectedCourse(course);
    setAssignments([]); // Clear assignments when changing course
    setNotification(''); // Clear notifications
  };

  const handleGenerateDraft = async (assignmentId) => {
    setGeneratingDraftId(assignmentId); // Set loading state for this assignment
    setNotification('Generating draft...');
    setError('');
    try {
      const draft = await assignmentService.generateAssignmentDraft(assignmentId);
      setNotification(`Draft generation started for assignment ${assignmentId}. Draft ID: ${draft.id}. Refresh or check drafts later.`);
      // TODO: Implement polling or WebSocket to update draft status automatically
      // For now, user needs to manually check/refresh
    } catch (err) {
      console.error(`Failed to generate draft for assignment ${assignmentId}:`, err);
      setError('Failed to start draft generation.');
      setNotification('');
    } finally {
      setGeneratingDraftId(null); // Reset loading state
    }
  };

  // Navigate to the draft review page for the assignment
  const handleViewDrafts = (assignmentId) => {
    navigate(`/assignments/${assignmentId}/drafts`);
  };

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Dashboard</h2>
        <div>
          <span>Welcome, {user.fullName}!</span>
          <button onClick={handleLogout} style={{ marginLeft: '10px' }}>Logout</button>
        </div>
      </header>
      
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {notification && <p style={{ color: 'blue' }}>{notification}</p>}

      <div style={{ display: 'flex', marginTop: '20px' }}>
        {/* Course List */}
        <div style={{ width: '30%', borderRight: '1px solid #ccc', paddingRight: '15px' }}>
          <h3>Your Courses</h3>
          {courses.length > 0 ? (
            <ul>
              {courses.map((course) => (
                <li 
                  key={course.id} 
                  onClick={() => handleCourseSelect(course)}
                  style={{
                    cursor: 'pointer', 
                    fontWeight: selectedCourse?.id === course.id ? 'bold' : 'normal'
                  }}
                >
                  {course.name}
                </li>
              ))}
            </ul>
          ) : (
            <p>No courses found or unable to load.</p>
          )}
        </div>

        {/* Assignment List */}
        <div style={{ width: '70%', paddingLeft: '15px' }}>
          <h3>Assignments for {selectedCourse ? selectedCourse.name : '...select a course'}</h3>
          {selectedCourse ? (
            assignments.length > 0 ? (
              <ul>
                {assignments.map((assignment) => (
                  <li key={assignment.id} style={{ marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                    <strong>{assignment.title}</strong>
                    <p>{assignment.description || 'No description.'}</p>
                    {assignment.due_date && <p>Due: {new Date(assignment.due_date).toLocaleString()}</p>}
                    <button 
                      onClick={() => handleGenerateDraft(assignment.id)}
                      disabled={generatingDraftId === assignment.id} // Disable button while generating
                      style={{ marginRight: '10px' }} // Add margin
                    >
                      {generatingDraftId === assignment.id ? 'Generating...' : 'Generate Draft'}
                    </button>
                    <button onClick={() => handleViewDrafts(assignment.id)}>
                      View Drafts
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No assignments found for {selectedCourse.name}.</p>
            )
          ) : (
            <p>Select a course to view assignments.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;