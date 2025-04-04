import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import GoogleCallbackPage from './pages/GoogleCallbackPage';
import DraftReviewPage from './pages/DraftReviewPage'; // Import the new page
import authService from './services/authService';
import './App.css';

// Simple Protected Route component
function ProtectedRoute({ children }) {
  const isAuthenticated = authService.isAuthenticated();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>OpenCoder</h1>
        </header>
        <main>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            {/* The path here should match the redirect URI configured in Google Cloud Console and backend */}
            <Route path="/auth/google/callback" element={<GoogleCallbackPage />} /> 
            <Route 
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            {/* Add route for Draft Review Page */}
            <Route 
              path="/assignments/:assignmentId/drafts"
              element={
                <ProtectedRoute>
                  <DraftReviewPage />
                </ProtectedRoute>
              }
            />
            {/* Default route: Redirect to dashboard if logged in, else to login */}
            <Route 
              path="/"
              element={authService.isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
            />
            {/* Add other routes as needed */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
