import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // Axios for API requests
import '../styles/Home.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFacebook, faTwitter, faLinkedin, faInstagram } from '@fortawesome/free-brands-svg-icons'; // Import social media icons
import { faBrain, faChartLine, faStar, faLightbulb, faBolt, faAddressCard, faPhone, faTasks, faLock, faGraduationCap, faBookOpen, faChalkboardTeacher } from '@fortawesome/free-solid-svg-icons';
import url from './url.js';

const HomePage = () => {

  const apiUrl = url;
  const toggleLogin = async () => {
    try {
      const response = await axios.get(`${apiUrl}/dissertation/api/login`, {
        responseType: 'json',
      });
  
      if (response.status === 200) {
        const encodedResponse = response.data;
  
        if (!encodedResponse) {
          console.error("The encoded_request is missing or undefined!");
          return;
        }
  
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = 'https://idp.bits-pilani.ac.in/idp/profile/SAML2/Redirect/SSO';
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'SAMLRequest';
        hiddenInput.value = encodedResponse;
        form.appendChild(hiddenInput);
        document.body.appendChild(form);
        form.submit(); // This triggers redirection, stopping any further execution
  
      } else {
        console.error("Login failed with status:", response.status);
      }
    } catch (error) {
      console.error("Error during login:", error);
    }
  };
  
  // Call this function **only after** the user has returned to the frontend

  
  return (
    <div className="home-page">
      <header className="header">
        <div className="container header-container">
          <div className="logo">
            <h1>GradEx </h1>
          </div>
          <nav className="main-nav">
            <ul>
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="https://www.spanda.ai/about">About</a></li>
            </ul>
          </nav>
          <button className="login-button" onClick={toggleLogin}>
            Login
          </button>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="container">
            <div className="hero-content">
              <h1>Streamline Your Dissertation Assessment Process</h1>
              <p>Comprehensive analysis tools to evaluate theses based on customizable rubrics.</p>
              <div className="hero-cta">
                <button className="cta-button">Get Started</button>
                <button className="secondary-button">Watch Demo</button>
              </div>
            </div>
            <div className="hero-image">
              {/* Replaced static image with FontAwesome icons and React styling */}
              <div className="dashboard-illustration">

                <div className="illustration-content">
                  <div className="illustration-section">
                    <FontAwesomeIcon icon={faChartLine} size="3x" />
                    <div className="illustration-bar-chart">
                      <div className="bar" style={{ height: '60%' }}></div>
                      <div className="bar" style={{ height: '80%' }}></div>
                      <div className="bar" style={{ height: '40%' }}></div>
                      <div className="bar" style={{ height: '90%' }}></div>
                      <div className="bar" style={{ height: '50%' }}></div>
                    </div>
                  </div>
                  <div className="illustration-section">
                    <FontAwesomeIcon icon={faBookOpen} size="3x" />
                    <div className="illustration-rubric">
                      <div className="rubric-item"></div>
                      <div className="rubric-item"></div>
                      <div className="rubric-item"></div>
                    </div>
                  </div>
                  <div className="illustration-section">
                    <FontAwesomeIcon icon={faChalkboardTeacher} size="3x" />
                    <div className="illustration-feedback"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="features">
          <div className="container">
            <h2 className="section-title">Powerful Features</h2>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="icon-analysis"></i>
                </div>
                <h3>Automated Analysis</h3>
                <p>Advanced algorithms analyze dissertations against standardized or custom rubrics.</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="icon-rubric"></i>
                </div>
                <h3>Rubric Management</h3>
                <p>Create, edit, and manage assessment criteria tailored to your institution's requirements.</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="icon-score"></i>
                </div>
                <h3>Score Management</h3>
                <p>Comprehensive scoring system with detailed breakdowns and historical comparisons.</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="icon-feedback"></i>
                </div>
                <h3>Actionable Feedback</h3>
                <p>Generate specific, constructive feedback based on assessment results.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="how-it-works">
          <div className="container">
            <h2 className="section-title">How It Works</h2>
            <div className="workflow">
              <div className="workflow-step">
                <div className="step-number">1</div>
                <h3>Upload Dissertation</h3>
                <p>Upload documents in various formats including PDF, DOCX, or LaTeX.</p>
              </div>
              <div className="workflow-divider"></div>
              <div className="workflow-step">
                <div className="step-number">2</div>
                <h3>Select Rubric</h3>
                <p>Choose from existing rubrics or create custom assessment criteria.</p>
              </div>
              <div className="workflow-divider"></div>
              <div className="workflow-step">
                <div className="step-number">3</div>
                <h3>Run Analysis</h3>
                <p>Our system evaluates the thesis against selected criteria.</p>
              </div>
              <div className="workflow-divider"></div>
              <div className="workflow-step">
                <div className="step-number">4</div>
                <h3>Review Results</h3>
                <p>Explore comprehensive reports with actionable insights.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="testimonials">
          <div className="container">
            <h2 className="section-title">What Our Users Say</h2>
            <div className="testimonial-slider">
              <div className="testimonial">
                <div className="testimonial-content">
                  <p>"GradEx  has revolutionized how our department evaluates dissertations. The customizable rubrics and detailed analysis save us countless hours."</p>
                </div>
                <div className="testimonial-author">
                  <div className="author-avatar"></div>
                  <div className="author-info">
                    <h4>Dr. Sarah Johnson</h4>
                    <p>Department Chair, University of Columbia</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

    <footer className="footer">
    <div className="footer-content">
        <div className="branding">
        <h2><span className="highlight">[</span>  Spanda<span className="highlight">.</span>AI  <span className="highlight">]</span></h2>
            <p>Empowering insights and intelligence through AI-driven solutions.</p>
            <hr className="divider" />
        </div>
        
        <div className="footer-links">
            <h3>Quick Links</h3>
            <ul>
                <li><FontAwesomeIcon icon={faAddressCard} className="link-icon" /><a href="https://www.spanda.ai/about"> About Us</a></li>
                <li><FontAwesomeIcon icon={faTasks} className="link-icon" /><a href="https://www.spanda.ai/"> Services</a></li>
                <li><FontAwesomeIcon icon={faPhone} className="link-icon" /><a href="https://www.spanda.ai/contact"> Contact</a></li>
                <li><FontAwesomeIcon icon={faLock} className="link-icon" /><a href="https://www.spanda.ai/"> Privacy Policy</a></li>
            </ul>
            <hr className="divider" />
        </div>
        
        <div className="social-media">
            <h3>Connect with Us</h3>
            <div className="social-icons">
                <a href="https://www.facebook.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faFacebook} />
                </a>
                <a href="https://www.twitter.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faTwitter} />
                </a>
                <a href="https://www.linkedin.com/company/spandaAI" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faLinkedin} />
                </a>
                <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer">
                    <FontAwesomeIcon icon={faInstagram} />
                </a>
            </div>
        </div>
    </div>
    
    <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Spanda.AI. All Rights Reserved.</p>
    </div>
    </footer>
    </div>
  );
};

export default HomePage;