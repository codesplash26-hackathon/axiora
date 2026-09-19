import React from 'react';
import './App.css';
import heartImg from './assets/3d_heart.png';
import { Activity, Brain, Search, Map, Heart } from 'lucide-react';

const App = () => {
  return (
    <div className="landing-container">
      {/* Left Column */}
      <div className="left-content">
        <header className="header">
          <div className="logo-icon">
            <Heart size={48} color="#0284c7" fill="#e0f2fe" strokeWidth={2} />
            <Activity size={24} color="#0284c7" className="logo-ecg" />
          </div>
          <div className="logo-text">
            <span className="brand-name">CardioRecourse</span>
            <span className="brand-subtitle">
              An Explainable AI (XAI) Clinical Decision Support<br/>
              System for Actionable Cardiovascular Risk Reduction
            </span>
          </div>
        </header>

        <div className="hero-text">
          <h1 className="tagline">Understand the <span className="highlight-why">why.</span><br/>Take the right steps.</h1>
          <p className="description">
            More than a risk score — a personalized path<br/>to a healthier heart.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-item">
            <div className="feature-icon bg-blue-100">
              <Brain size={28} color="#0284c7" />
            </div>
            <span>AI-Powered<br/>Risk Prediction</span>
          </div>
          <div className="feature-item">
            <div className="feature-icon bg-green-100">
              <Search size={28} color="#16a34a" />
            </div>
            <span>Transparent<br/>Explanations<br/>(SHAP)</span>
          </div>
          <div className="feature-item">
            <div className="feature-icon bg-purple-100">
              <Map size={28} color="#9333ea" />
            </div>
            <span>Personalized<br/>Action Plans<br/>(DICE)</span>
          </div>
          <div className="feature-item">
            <div className="feature-icon bg-red-100">
              <Heart size={28} color="#dc2626" />
            </div>
            <span>Healthier<br/>Tomorrows</span>
          </div>
        </div>

        <footer className="footer-info">
          A product of <strong>Axiora</strong><br/>
          <span className="uni">University of Moratuwa</span>
        </footer>
      </div>

      {/* Right Column */}
      <div className="right-content">
        <div className="heart-graphic-container">
          {/* Replace this with the actual 3D heart asset if you have it */}
          <img src={heartImg} alt="3D Heart Graphic" className="heart-img" />
          
          {/* Floating Cards */}
          <div className="floating-card card-risk-factors">
            <div className="card-header">
              <div className="card-icon"><Search size={24} color="#0284c7" /></div>
              <div>
                <h4>Why this risk?</h4>
                <p>Key factors contributing<br/>to your risk</p>
              </div>
            </div>
            <ul className="factors-list">
              <li><span className="dot red"></span> High Blood Pressure <span className="value">+32%</span></li>
              <li><span className="dot orange"></span> Cholesterol <span className="value">+24%</span></li>
              <li><span className="dot purple"></span> Age <span className="value">+18%</span></li>
              <li><span className="dot yellow"></span> Smoking <span className="value">+12%</span></li>
              <li><span className="dot green"></span> BMI <span className="value">+8%</span></li>
            </ul>
          </div>

          <div className="floating-card card-risk-level">
            <div className="card-header-center">
              <Heart size={24} color="#0ea5e9" className="card-icon-small" />
              <h4>Your Risk Level</h4>
            </div>
            <div className="gauge">
              <svg viewBox="0 0 100 50" className="gauge-svg">
                <path d="M 10 40 A 30 30 0 0 1 90 40" fill="none" stroke="#e5e7eb" strokeWidth="8" strokeLinecap="round" />
                <path d="M 10 40 A 30 30 0 0 1 90 40" fill="none" stroke="url(#gauge-gradient)" strokeWidth="8" strokeLinecap="round" strokeDasharray="95" strokeDashoffset="20" />
                <defs>
                  <linearGradient id="gauge-gradient">
                    <stop offset="0%" stopColor="#fcd34d" />
                    <stop offset="50%" stopColor="#f97316" />
                    <stop offset="100%" stopColor="#ef4444" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="gauge-value">High</div>
            </div>
            <div className="risk-text">10-year risk: 18.7%</div>
          </div>

          <div className="floating-card card-pathways">
             <div className="card-header">
              <div className="card-icon"><Activity size={24} color="#10b981" /></div>
              <div>
                <h4>Your Personalized<br/>Recourse Pathways</h4>
              </div>
            </div>
            <ul className="pathways-list">
              <li>
                <div className="pathway-icon bg-green"><Activity size={16} color="white"/></div>
                <div className="pathway-text">
                  <strong>Lower BP</strong>
                  <span>-6.2% risk reduction</span>
                </div>
                <span className="arrow">&gt;</span>
              </li>
              <li>
                <div className="pathway-icon bg-purple"><span>🍽️</span></div>
                <div className="pathway-text">
                  <strong>Improve Diet</strong>
                  <span>-4.8% risk reduction</span>
                </div>
                <span className="arrow">&gt;</span>
              </li>
              <li>
                <div className="pathway-icon bg-blue"><span>🏃</span></div>
                <div className="pathway-text">
                  <strong>Increase Activity</strong>
                  <span>-3.1% risk reduction</span>
                </div>
                <span className="arrow">&gt;</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-quote">
          Smarter insights.<br/>Healthier choices.<br/>A safer you.
        </div>
      </div>
    </div>
  );
};

export default App;
