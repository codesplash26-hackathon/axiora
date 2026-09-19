import { useEffect, useState } from 'react';
import './App.css';
import heartImg from './assets/shiny_tech_heart.jpg';
import { Activity, Brain, Search, Map, Heart, ArrowRight, Play, ChevronRight, Droplets, Target, Zap, ActivitySquare } from 'lucide-react';

const App = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={`landing-container ${mounted ? 'mounted' : ''}`}>
      {/* Abstract Pathway Background */}
      <div className="path-background">
        <svg viewBox="0 0 1440 800" preserveAspectRatio="none" className="path-svg">
          <path 
            className="path-line" 
            d="M -100,700 C 300,700 500,400 900,350 C 1200,300 1400,100 1600,50" 
          />
          <path 
            className="path-line glow" 
            d="M -100,700 C 300,700 500,400 900,350 C 1200,300 1400,100 1600,50" 
          />
        </svg>
      </div>

      <div className="hero-content">
        {/* LEFT COLUMN */}
        <div className="hero-left">
          <header className="brand-header fade-up-1">
            <div className="logo-icon-wrapper">
              <Heart className="logo-heart" size={32} />
              <Activity className="logo-ecg" size={16} />
            </div>
            <div className="brand-text">
              <span className="brand-name">CardioRecourse</span>
            </div>
          </header>

          <div className="hero-text-block">
            <h2 className="subtitle fade-up-2">
              Explainable AI for Smarter Cardiovascular Risk Reduction
            </h2>
            <h1 className="main-headline fade-up-3">
              Your Risk, <span className="highlight-text">Explained.</span>
            </h1>
            <p className="description fade-up-4">
              Understand what drives cardiovascular risk. Explore personalized pathways to reduce it.
            </p>

            <div className="cta-group fade-up-5">
              <button className="btn-primary">
                Explore CardioRecourse <ArrowRight size={18} className="btn-icon" />
              </button>
              <button className="btn-secondary">
                <Play size={18} fill="currentColor" className="btn-icon-play" /> View Demo
              </button>
            </div>

            <div className="credibility fade-up-6">
              A product of <strong>Axiora</strong> <span className="dot-separator">·</span> University of Moratuwa
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="hero-right fade-in-delay">
          <div className="visual-centerpiece">
            
            {/* Heart 3D Visual */}
            <div className="heart-wrapper heartbeat-anim">
              <img src={heartImg} alt="CardioRecourse Heart" className="heart-img" />
            </div>

            {/* Floating Card 1: Explainability */}
            <div className="glass-card card-explain floating-anim-1">
              <div className="card-header">
                <div className="card-icon blue-bg"><Search size={16} /></div>
                <h4 className="card-title">Your Risk, Explained</h4>
              </div>
              <div className="factor-bars">
                <div className="factor">
                  <div className="factor-info"><span>Blood Pressure</span><span className="val">+32%</span></div>
                  <div className="bar-bg"><div className="bar-fill red" style={{width: '75%'}}></div></div>
                </div>
                <div className="factor">
                  <div className="factor-info"><span>Cholesterol</span><span className="val">+24%</span></div>
                  <div className="bar-bg"><div className="bar-fill orange" style={{width: '60%'}}></div></div>
                </div>
                <div className="factor">
                  <div className="factor-info"><span>Age</span><span className="val">+18%</span></div>
                  <div className="bar-bg"><div className="bar-fill teal" style={{width: '45%'}}></div></div>
                </div>
                <div className="factor">
                  <div className="factor-info"><span>Smoking</span><span className="val">+12%</span></div>
                  <div className="bar-bg"><div className="bar-fill purple" style={{width: '30%'}}></div></div>
                </div>
                <div className="factor">
                  <div className="factor-info"><span>BMI</span><span className="val">+8%</span></div>
                  <div className="bar-bg"><div className="bar-fill blue" style={{width: '20%'}}></div></div>
                </div>
              </div>
            </div>

            {/* Floating Card 2: Risk Overview */}
            <div className="glass-card card-risk floating-anim-2">
              <h4 className="card-title text-center">10-Year Cardiovascular Risk</h4>
              <div className="gauge-container">
                <svg viewBox="0 0 100 55" className="gauge-svg">
                  <path d="M 10 45 A 35 35 0 0 1 90 45" fill="none" stroke="#f1f5f9" strokeWidth="8" strokeLinecap="round" />
                  <path 
                    className="gauge-fill" 
                    d="M 10 45 A 35 35 0 0 1 90 45" 
                    fill="none" 
                    stroke="url(#risk-grad)" 
                    strokeWidth="8" 
                    strokeLinecap="round" 
                  />
                  <defs>
                    <linearGradient id="risk-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#06b6d4" />
                      <stop offset="60%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#f43f5e" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="gauge-text">
                  <span className="gauge-value">18.7%</span>
                  <span className="gauge-label elevated">Elevated Risk</span>
                </div>
              </div>
            </div>

            {/* Floating Card 3: Pathways */}
            <div className="glass-card card-pathways floating-anim-3">
              <div className="card-header">
                <div className="card-icon teal-bg"><Map size={16} /></div>
                <h4 className="card-title">Personalized Pathways</h4>
              </div>
              <div className="pathway-list">
                <div className="pathway-item">
                  <div className="path-icon red-light"><Target size={16}/></div>
                  <div className="path-text">Improve Blood Pressure</div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon teal-light"><Droplets size={16}/></div>
                  <div className="path-text">Improve Lifestyle</div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon purple-light"><Zap size={16}/></div>
                  <div className="path-text">Increase Physical Activity</div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* XAI FEATURE STRIP */}
      <div className="feature-strip-wrapper fade-up-7">
        <div className="feature-strip">
          <div className="feat-item">
            <div className="feat-icon-wrapper blue-outline">
              <Brain size={20} className="feat-icon" />
            </div>
            <div className="feat-text">
              <strong>AI-Powered Risk Prediction</strong>
              <span>Risk stratification using machine learning</span>
            </div>
          </div>
          <div className="feat-divider"></div>
          <div className="feat-item">
            <div className="feat-icon-wrapper teal-outline">
              <Search size={20} className="feat-icon" />
            </div>
            <div className="feat-text">
              <strong>Transparent Explanations</strong>
              <span>SHAP-based explanation of contributing factors</span>
            </div>
          </div>
          <div className="feat-divider"></div>
          <div className="feat-item">
            <div className="feat-icon-wrapper purple-outline">
              <Map size={20} className="feat-icon" />
            </div>
            <div className="feat-text">
              <strong>Personalized Recourse</strong>
              <span>DiCE-based alternative pathways</span>
            </div>
          </div>
          <div className="feat-divider"></div>
          <div className="feat-item">
            <div className="feat-icon-wrapper sky-outline">
              <ActivitySquare size={20} className="feat-icon" />
            </div>
            <div className="feat-text">
              <strong>Actionable Plans</strong>
              <span>Turn insights into practical next steps</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
