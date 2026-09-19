import { useEffect, useState } from 'react';
import './App.css';
import heartImg from './assets/shiny_tech_heart.png';
import { Activity, Brain, Search, Heart, Utensils, Dumbbell, Ban, ArrowDown, ActivitySquare, GitMerge, ChevronRight } from 'lucide-react';

const App = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={`landing-container ${mounted ? 'mounted' : ''}`}>

      {/* Background Soft Glows */}
      <div className="bg-glow blue-glow"></div>
      <div className="bg-glow teal-glow"></div>

      {/* Decorative Leaves (Abstract) */}
      <div className="leaf leaf-1"></div>
      <div className="leaf leaf-2"></div>
      <div className="leaf leaf-3"></div>

      {/* Road Graphic at the bottom */}
      <div className="road-container fade-in-delay">
        <svg viewBox="0 0 1440 600" preserveAspectRatio="none" className="road-svg">
          <defs>
            <linearGradient id="road-gradient" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6ee7b7" stopOpacity="0.9"/>
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.9"/>
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.9"/>
            </linearGradient>
          </defs>

          {/* Road Outer Edge (White Border) */}
          <path 
            d="M -50,550 C 200,550 300,400 550,400 C 800,400 800,200 1050,200 C 1300,200 1350,80 1450,50" 
            fill="none"
            stroke="#ffffff"
            strokeWidth="110"
            strokeLinecap="round"
          />
          {/* Road Surface (Gradient) */}
          <path 
            d="M -50,550 C 200,550 300,400 550,400 C 800,400 800,200 1050,200 C 1300,200 1350,80 1450,50" 
            fill="none"
            stroke="url(#road-gradient)"
            strokeWidth="100"
            strokeLinecap="round"
          />
          {/* Dashed Center Line */}
          <path 
            className="road-dashed"
            d="M -50,550 C 200,550 300,400 550,400 C 800,400 800,200 1050,200 C 1300,200 1350,80 1450,50" 
            fill="none"
            stroke="#ffffff"
            strokeWidth="6"
            strokeDasharray="30 40"
            strokeLinecap="round"
            filter="drop-shadow(0 0 6px rgba(255,255,255,0.8))"
          />
        </svg>

        {/* Map Pins on the road */}
        <div className="road-pin pin-diet">
          <div className="pin-head bg-green"><Utensils size={18} color="white" /></div>
          <div className="pin-point bg-green"></div>
        </div>
        <div className="road-pin pin-exercise">
          <div className="pin-head bg-purple"><Dumbbell size={18} color="white" /></div>
          <div className="pin-point bg-purple"></div>
        </div>
        <div className="road-pin pin-smoking">
          <div className="pin-head bg-blue"><Ban size={18} color="white" /></div>
          <div className="pin-point bg-blue"></div>
        </div>
      </div>

      <div className="hero-content">
        {/* LEFT COLUMN */}
        <div className="hero-left">

          <header className="brand-header fade-up-1">
            <div className="logo-icon-wrapper">
              <Heart className="logo-heart" size={44} />
              <Activity className="logo-ecg" size={24} />
            </div>
            <div className="brand-text-col">
              <span className="brand-name">CardioRecourse</span>
              <p className="brand-subtitle">
                An Explainable AI (XAI) Clinical Decision Support<br />
                System for Actionable Cardiovascular Risk Reduction
              </p>
            </div>
          </header>

          <div className="tagline-block fade-up-2">
            <h1 className="tagline-main">
              Understand the <span className="highlight-why">why.</span><br />
              <span className="tagline-second">Take the right steps.</span>
              <svg className="swoosh" viewBox="0 0 300 30" preserveAspectRatio="none">
                <path d="M 10,20 Q 150,5 290,15" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round" />
              </svg>
            </h1>
            <p className="description">
              More than a risk score — a personalized path<br />to a healthier heart.
            </p>
          </div>

          <div className="features-row fade-up-3">
            <div className="feat-col">
              <div className="feat-icon-round bg-blue-100"><Brain size={26} color="#0284c7" /></div>
              <span>AI-Powered<br />Risk Prediction</span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-green-100"><Search size={26} color="#059669" /></div>
              <span>Transparent<br />Explanations<br /><small>(SHAP)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-purple-100"><GitMerge size={26} color="#7e22ce" /></div>
              <span>Personalized<br />Action Plans<br /><small>(DiCE)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-red-100"><Heart size={26} color="#e11d48" /></div>
              <span>Healthier<br />Tomorrows</span>
            </div>
          </div>

          <div className="credibility fade-up-4">
            <div className="cred-line"></div>
            <div>
              A product of <strong>Axiora</strong><br />
              <span className="uni-name">University of Moratuwa</span>
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
              <div className="card-header-clean">
                <div className="icon-circle bg-blue-light"><Search size={18} color="#0284c7" /></div>
                <div>
                  <h4 className="card-title">Why this risk?</h4>
                  <span className="card-subtitle">Key factors contributing<br/>to your risk</span>
                </div>
              </div>
              <div className="factor-list">
                <div className="factor-item">
                  <div className="f-label"><span className="dot bg-red"></span> High Blood Pressure</div>
                  <span className="f-val">+32%</span>
                </div>
                <div className="factor-item">
                  <div className="f-label"><span className="dot bg-orange"></span> Cholesterol</div>
                  <span className="f-val">+24%</span>
                </div>
                <div className="factor-item">
                  <div className="f-label"><span className="dot bg-purple"></span> Age</div>
                  <span className="f-val">+18%</span>
                </div>
                <div className="factor-item">
                  <div className="f-label"><span className="dot bg-yellow"></span> Smoking</div>
                  <span className="f-val">+12%</span>
                </div>
                <div className="factor-item">
                  <div className="f-label"><span className="dot bg-teal"></span> BMI</div>
                  <span className="f-val">+8%</span>
                </div>
              </div>
            </div>

            {/* Floating Card 2: Risk Level */}
            <div className="glass-card card-risk floating-anim-2">
              <div className="card-header-clean center">
                <div className="icon-circle bg-blue-light"><Heart size={16} color="#0284c7" /></div>
                <h4 className="card-title">Your Risk Level</h4>
              </div>
              <div className="gauge-container">
                <svg viewBox="0 0 100 55" className="gauge-svg">
                  <path d="M 10 45 A 35 35 0 0 1 90 45" fill="none" stroke="#f1f5f9" strokeWidth="12" strokeLinecap="round" />
                  <path 
                    className="gauge-fill" 
                    d="M 10 45 A 35 35 0 0 1 90 45" 
                    fill="none" 
                    stroke="url(#risk-grad)" 
                    strokeWidth="12" 
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
              <div className="card-header-clean center">
                <div className="icon-circle bg-green-light"><ActivitySquare size={16} color="#059669" /></div>
                <h4 className="card-title">Your Personalized<br/>Recourse Pathways</h4>
              </div>
              <div className="pathway-list">
                <div className="pathway-item">
                  <div className="path-icon bg-teal"><ArrowDown size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Lower BP</strong>
                    <span>+6.2% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon bg-purple"><Utensils size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Improve Diet</strong>
                    <span>+4.8% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
                <div className="pathway-item">
                  <div className="path-icon bg-blue"><Activity size={16} color="white"/></div>
                  <div className="path-text">
                    <strong>Increase Activity</strong>
                    <span>+3.1% risk reduction</span>
                  </div>
                  <ChevronRight size={16} className="path-arrow" />
                </div>
              </div>
            </div>
          </div>

          <div className="footer-quote fade-up-5">
            Smarter insights.<br />Healthier choices.<br />A safer you.
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
