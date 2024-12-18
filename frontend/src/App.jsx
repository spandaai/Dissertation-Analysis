import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dissertation from './components/Dissertation';
import Dashboard from './components/Dashboard';

const App = () => {
  return (
    <div className="app-container">
      <Router>
        <Routes>
          <Route path="/" element={<Dissertation />} />
          <Route path="/Spanda_Dashboard" element={<Dashboard />} />
        </Routes>
      </Router>
    </div>
  );
};

export default App;