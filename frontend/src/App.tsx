import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { SharedRoutePage } from './pages/SharedRoutePage';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/shared/:token" element={<SharedRoutePage />} />
      </Routes>
    </Router>
  );
}

export default App;
