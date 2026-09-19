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
        <svg viewBox="0 0 1440 400" preserveAspectRatio="none" className="road-svg">
          {/* Road Base */}
          <path 
            className="road-path"
            d="M 1440,400 C 1000,400 800,200 400,250 C 200,270 0,200 -100,150 L -100,400 Z" 
            fill="url(#road-gradient)"
          />
          {/* Road Top Edge */}
          <path 
            className="road-edge"
            d="M 1440,400 C 1000,400 800,200 400,250 C 200,270 0,200 -100,150" 
            fill="none"
            stroke="#bae6fd"
            strokeWidth="4"
          />
          {/* Dashed Center Line */}
          <path 
            className="road-dashed"
            d="M 1440,420 C 1000,420 800,220 400,270 C 200,290 0,220 -100,170" 
            fill="none"
            stroke="#ffffff"
            strokeWidth="4"
            strokeDasharray="20 25"
          />

          <defs>
            <linearGradient id="road-gradient" x1="100%" y1="0%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#7dd3fc" stopOpacity="0.8"/>
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.5"/>
              <stop offset="100%" stopColor="#a7f3d0" stopOpacity="0.8"/>
            </linearGradient>
          </defs>
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
                An Explainable AI (XAI) Clinical Decision Support<br/>
                System for Actionable Cardiovascular Risk Reduction
              </p>
            </div>
          </header>

          <div className="tagline-block fade-up-2">
            <h1 className="tagline-main">
              Understand the <span className="highlight-why">why.</span><br/>
              <span className="tagline-second">Take the right steps.</span>
              <svg className="swoosh" viewBox="0 0 300 30" preserveAspectRatio="none">
                <path d="M 10,20 Q 150,5 290,15" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round" />
              </svg>
            </h1>
            <p className="description">
              More than a risk score — a personalized path<br/>to a healthier heart.
            </p>
          </div>

          <div className="features-row fade-up-3">
            <div className="feat-col">
              <div className="feat-icon-round bg-blue-100"><Brain size={26} color="#0284c7" /></div>
              <span>AI-Powered<br/>Risk Prediction</span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-green-100"><Search size={26} color="#059669" /></div>
              <span>Transparent<br/>Explanations<br/><small>(SHAP)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-purple-100"><GitMerge size={26} color="#7e22ce" /></div>
              <span>Personalized<br/>Action Plans<br/><small>(DiCE)</small></span>
            </div>
            <div className="feat-col">
              <div className="feat-icon-round bg-red-100"><Heart size={26} color="#e11d48" /></div>
              <span>Healthier<br/>Tomorrows</span>
            </div>
          </div>

          <div className="credibility fade-up-4">
            <div className="cred-line"></div>
            <div>
              A product of <strong>Axiora</strong><br/>
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



          </div>
          
          <div className="footer-quote fade-up-5">
            Smarter insights.<br/>Healthier choices.<br/>A safer you.
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
