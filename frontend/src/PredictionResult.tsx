import { useEffect, useState } from 'react';
import { ArrowLeft, ActivitySquare, ShieldAlert, HeartPulse } from 'lucide-react';
import './PredictionResult.css';
import heartImg from './assets/shiny_tech_heart.png';

interface PredictionResultProps {
  onBack: () => void;
  onNext: () => void; // To proceed to SHAP explanations
}

export default function PredictionResult({ onBack, onNext }: PredictionResultProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [riskScore, setRiskScore] = useState(0);
  
  // Mock API Call delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsAnalyzing(false);
      // Animate score from 0 to 18.7
      let current = 0;
      const target = 18.7;
      const interval = setInterval(() => {
        current += 0.5;
        if (current >= target) {
          setRiskScore(target);
          clearInterval(interval);
        } else {
          setRiskScore(Number(current.toFixed(1)));
        }
      }, 30);
    }, 3000); // 3 seconds loading

    return () => clearTimeout(timer);
  }, []);

  if (isAnalyzing) {
    return (
      <div className="result-container flex-center">
        <div className="loading-state">
          <div className="loading-circles">
            <div className="circle-1"></div>
            <div className="circle-2"></div>
            <HeartPulse size={48} className="pulse-icon" />
          </div>
          <h2 className="loading-text">Analyzing Your Health Profile...</h2>
          <div className="ecg-line-loader">
             <svg width="200" height="60" viewBox="0 0 200 60">
              <path
                className="ecg-path"
                d="M 0,30 L 40,30 L 50,10 L 60,50 L 70,20 L 80,40 L 90,30 L 200,30"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="result-container">
      {/* Navigation */}
      <nav className="result-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Dashboard
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="result-main">
        <div className="result-grid">
          
          {/* Left Column: Gauge */}
          <div className="result-left fade-up">
            <h1 className="result-title">Your Cardiovascular Risk</h1>
            <p className="result-subtitle">Based on your provided health profile.</p>

            <div className="gauge-container">
              <svg className="risk-gauge" viewBox="0 0 200 200">
                {/* Background Track */}
                <circle cx="100" cy="100" r="80" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                {/* Progress Fill */}
                <circle 
                  cx="100" 
                  cy="100" 
                  r="80" 
                  fill="none" 
                  stroke="var(--color-accent-blue)" 
                  strokeWidth="12" 
                  strokeLinecap="round"
                  className="gauge-fill"
                  style={{ strokeDasharray: 502, strokeDashoffset: 502 - (502 * riskScore) / 100 }}
                />
              </svg>
              <div className="gauge-center">
                <span className="gauge-value">{riskScore}%</span>
                <span className="gauge-label">10-Year Risk</span>
              </div>
            </div>

            <div className="risk-band moderate-risk">
              <ShieldAlert size={20} />
              <span>Moderate Risk</span>
            </div>
            
            <p className="disclaimer">
              * This is a risk prediction, not a diagnosis.
            </p>

            <button className="btn-gradient-cta mt-4" onClick={onNext}>
              Explain My Risk <ActivitySquare size={20} className="ml-2" />
            </button>
          </div>

          {/* Right Column: Visualization */}
          <div className="result-right fade-up-delay">
            <div className="visual-centerpiece-result">
              <div className="heart-aura-result"></div>
              <div className="orbit-ring-result r1"></div>
              <div className="orbit-ring-result r2"></div>
              
              <div className="heart-wrapper-result">
                <img src={heartImg} alt="AI Heart" className="heart-img-result heartbeat-anim-result" />
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* Background soft glows */}
      <div className="bg-glow blue-glow-result"></div>
      <div className="bg-glow purple-glow-result"></div>
    </div>
  );
}
