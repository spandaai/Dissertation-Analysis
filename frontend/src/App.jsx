import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dissertation from './components/Dissertation';
import Dashboard from './components/Dashboard';
import RubricManagementApp from './components/RubricPage';
import ScoreManagement from './components/ScoreManagement';
import BatchProcess from './components/BatchProcess';
import HomePage from './components/Home';
import ProtectedRoute from './components/utils/ProtectedRoute'; // Import the new component

const App = () => {
  return (
    <div className="app-container">
      <Router>
        <Routes>
          {/* Public route */}
          <Route path="/" element={<HomePage />} />
          
          {/* Protected routes */}
          <Route 
            path="/HomePage" 
            element={
              <ProtectedRoute>
                <Dissertation />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/RubricPage" 
            element={
              <ProtectedRoute>
                <RubricManagementApp />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/ScoreManagement" 
            element={
              <ProtectedRoute>
                <ScoreManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/BatchProcess" 
            element={
              <ProtectedRoute>
                <BatchProcess />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </div>
  );
};

export default App;