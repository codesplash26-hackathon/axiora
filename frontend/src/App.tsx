import { useEffect, useState } from 'react';
import './App.css';
import heartImg from './assets/shiny_tech_heart.jpg';
import { Activity, Brain, Search, Map, Heart, ChevronRight, Droplets, Target, Zap, MapPin } from 'lucide-react';

const App = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={`landing-container ${mounted ? 'mounted' : ''}`}>
      {/* Background elements */}
      <div className="bg-glow blue-glow"></div>
      <div className="bg-glow teal-glow"></div>

      {/* Road Graphic at the bottom */}
      <div className="road-container fade-in-delay">
        <svg viewBox="0 0 1440 300" preserveAspectRatio="none" className="road-svg">
          {/* Road Base */}
          <path 
            className="road-path"
            d="M 0,300 C 400,300 600,200 900,250 C 1200,300 1300,100 1440,150 L 1440,300 Z" 
            fill="url(#road-gradient)"
          />
          {/* Road Top Edge */}
          <path 
            className="road-edge"
            d="M 0,300 C 400,300 600,200 900,250 C 1200,300 1300,100 1440,150" 
            fill="none"
            stroke="#e0f2fe"
            strokeWidth="4"
          />
          {/* Dashed Center Line */}
          <path 
            className="road-dashed"
            d="M 0,320 C 400,320 620,230 920,270 C 1220,310 1320,120 1440,170" 
            fill="none"
            stroke="#ffffff"
            strokeWidth="3"
            strokeDasharray="15 20"
          />

          <defs>
            <linearGradient id="road-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#bae6fd" stopOpacity="0.8"/>
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.4"/>
              <stop offset="100%" stopColor="#bae6fd" stopOpacity="0.8"/>
            </linearGradient>
          </defs>
        </svg>

        {/* Map Pins */}
        <div className="pin pin-1">
          <div className="pin-icon-wrap"><MapPin size={24} fill="#0ea5e9" color="white" /></div>
          <div className="pin-pulse"></div>
        </div>
        <div className="pin pin-2">
          <div className="pin-icon-wrap"><MapPin size={28} fill="#0ea5e9" color="white" /></div>
          <div className="pin-pulse"></div>
        </div>
        <div className="pin pin-3">
          <div className="pin-icon-wrap"><MapPin size={20} fill="#0ea5e9" color="white" /></div>
          <div className="pin-pulse"></div>
        </div>
      </div>

      <div className="hero-content">
        {/* LEFT COLUMN */}
        <div className="hero-left">
          <header className="brand-header fade-up-1">
            <div className="logo-icon-wrapper">
              <Heart className="logo-heart" size={40} />
              <Activity className="logo-ecg" size={20} />
            </div>
            <div className="brand-text">
              <span className="brand-name">CardioRecourse</span>
            </div>
          </header>
          
          <p className="brand-subtitle fade-up-2">
            An Explainable AI (XAI) Clinical Decision Support<br/>
            System for Actionable Cardiovascular Risk Reduction
          </p>

          <div className="tagline-block fade-up-3">
            <div className="tagline-line1">Not just a risk score...</div>
            <div className="tagline-line2">
              but a roadmap to a healthier heart
              <svg className="underline-swoosh" viewBox="0 0 400 20" preserveAspectRatio="none">
                <path d="M 0,15 Q 200,0 400,10" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          <div className="features-row fade-up-4">
            <div className="feat-col">
              <div className="feat-icon-round bg-blue-100"><Brain size={28} color="#0284c7" /></div>
              <span>AI-Powered<br/>Risk Prediction</span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-teal-100"><Search size={28} color="#0d9488" /></div>
              <span>Transparent<br/>Explanations<br/><small>(SHAP)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-purple-100"><Map size={28} color="#7e22ce" /></div>
              <span>Personalized<br/>Action Plans<br/><small>(DiCE)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-red-100"><Heart size={28} color="#e11d48" /></div>
              <span>Healthier<br/>Tomorrows</span>
            </div>
          </div>

          <div className="credibility fade-up-5">
            A product of <strong>Axiora</strong><br/>
            <span className="uni-name">University of Moratuwa</span>
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
              <div className="card-header-clean">
                <h4 className="card-title">Why this risk?</h4>
              </div>
              <div className="factor-bars">
                <div className="factor">
                  <div className="factor-info">
                    <div className="factor-label"><span className="dot bg-red"></span> High Blood Pressure</div>
                    <span className="val">+32%</span>
                  </div>
                </div>
                <div className="factor">
                  <div className="factor-info">
                    <div className="factor-label"><span className="dot bg-orange"></span> High Cholesterol</div>
                    <span className="val">+24%</span>
                  </div>
                </div>
                <div className="factor">
                  <div className="factor-info">
                    <div className="factor-label"><span className="dot bg-blue"></span> Age</div>
                    <span className="val">+18%</span>
                  </div>
                </div>
                <div className="factor">
                  <div className="factor-info">
                    <div className="factor-label"><span className="dot bg-yellow"></span> Smoking</div>
                    <span className="val">+12%</span>
                  </div>
                </div>
                <div className="factor">
                  <div className="factor-info">
                    <div className="factor-label"><span className="dot bg-teal"></span> BMI</div>
                    <span className="val">+8%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Card 2: Risk Overview */}
            <div className="glass-card card-risk floating-anim-2">
              <h4 className="card-title text-center">Your Risk Level</h4>
              <div className="gauge-container">
                <svg viewBox="0 0 100 55" className="gauge-svg">
                  <path d="M 10 45 A 35 35 0 0 1 90 45" fill="none" stroke="#f1f5f9" strokeWidth="10" strokeLinecap="round" />
                  <path 
                    className="gauge-fill" 
                    d="M 10 45 A 35 35 0 0 1 90 45" 
                    fill="none" 
                    stroke="url(#risk-grad)" 
                    strokeWidth="10" 
                    strokeLinecap="round" 
                  />
                  <defs>
                    <linearGradient id="risk-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#f59e0b" />
                      <stop offset="50%" stopColor="#f97316" />
                      <stop offset="100%" stopColor="#ef4444" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="gauge-text">
                  <span className="gauge-value">High</span>
                </div>
              </div>
              <div className="gauge-subtext">10-year risk: 18.7%</div>
            </div>

            {/* Floating Card 3: Pathways */}
            <div className="glass-card card-pathways floating-anim-3">
              <div className="card-header-clean">
                <h4 className="card-title">Personalized Recourse Pathways</h4>
              </div>
              <div className="pathway-list">
                <div className="pathway-item">
                  <div className="path-icon green-bg"><Target size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Lower BP</strong>
                    <span>+6.2% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon purple-bg"><Droplets size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Improve Diet</strong>
                    <span>+4.8% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon blue-bg"><Zap size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Increase Activity</strong>
                    <span>+3.1% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
              </div>
            </div>

          </div>
          
          <div className="footer-quote">
            Smarter insights.<br/>Healthier choices.<br/>A safer you.
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
