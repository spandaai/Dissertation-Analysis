import React, { useState, useEffect } from 'react';
import { Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import url from '../url'

// Protected route wrapper component
const ProtectedRoute = ({ children }) => { 
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();
  const apiUrl = url;
  
  useEffect(() => {
    const verifySession = async () => {
      try {
        const response = await axios.post(`${apiUrl}/dissertation/api/verify-session`, {}, {
          withCredentials: true // Important to include cookies in the request
        });
        
        setIsAuthenticated(response.data.isValid);
      } catch (error) {
        console.error('Session verification failed:', error);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, []);
  console.log("IS AUTHENTICATED",isAuthenticated)
  if (isLoading) {
    // You could return a loading spinner here
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;