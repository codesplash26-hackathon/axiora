import { useEffect, useState } from 'react';
import { ArrowLeft, ActivitySquare, ShieldAlert, ShieldCheck, AlertTriangle, Clock } from 'lucide-react';
import './PredictionResult.css';
import heartImg from './assets/shiny_tech_heart.png';
import type { PredictionResponse } from './api';

interface PredictionResultProps {
  prediction: PredictionResponse;
  onBack: () => void;
  onNext: () => void;
  latencyMs?: number;
}

export default function PredictionResult({ prediction, onBack, onNext, latencyMs }: PredictionResultProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Smooth entry animation from 0 up to actual predicted risk percentage
  useEffect(() => {
    const target = prediction.risk_percentage;
    let current = 0;
    const step = Math.max(0.1, target / 25);
    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        setAnimatedScore(target);
        clearInterval(interval);
      } else {
        setAnimatedScore(Number(current.toFixed(1)));
      }
    }, 20);

    return () => clearInterval(interval);
  }, [prediction.risk_percentage]);

  const riskBand = prediction.risk_band;
  const isHigh = riskBand === 'High';
  const isBorderline = riskBand === 'Borderline';

  const gaugeStrokeColor = isHigh 
    ? '#ef4444' 
    : isBorderline 
    ? '#f59e0b' 
    : '#10b981';

  return (
    <div className="result-container">
      {/* Navigation */}
      <nav className="result-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Health Profile
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="result-main">
        <div className="result-grid">
          
          {/* Left Column: Gauge & Clinical Band */}
          <div className="result-left fade-up">
            <h1 className="result-title">10-Year ASCVD Risk</h1>
            <p className="result-subtitle">
              Calibrated probability based on Framingham Risk Engine.
            </p>

            <div className="gauge-container">
              <svg className="risk-gauge" viewBox="0 0 200 200">
                <defs>
                  <filter id="gauge-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComponentTransfer in="blur" result="glow">
                      <feFuncA type="linear" slope="1.5"/>
                    </feComponentTransfer>
                    <feMerge>
                      <feMergeNode in="glow"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                {/* Background Track */}
                <circle cx="100" cy="100" r="80" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                {/* Dynamic Progress Fill */}
                <circle 
                  cx="100" 
                  cy="100" 
                  r="80" 
                  fill="none" 
                  stroke={gaugeStrokeColor}
                  strokeWidth="12" 
                  strokeLinecap="round"
                  className="gauge-fill"
                  style={{ strokeDasharray: 502, strokeDashoffset: 502 - (502 * Math.min(100, animatedScore)) / 100 }}
                  filter="url(#gauge-glow)"
                />
              </svg>
              <div className="gauge-center">
                <span className="gauge-value">{animatedScore.toFixed(1)}%</span>
                <span className="gauge-label">10-Year Probability</span>
              </div>
            </div>

            {/* Dynamic Risk Band Badge */}
            <div className={`risk-band ${isHigh ? 'high-risk' : isBorderline ? 'moderate-risk' : 'low-risk'}`}>
              {isHigh ? (
                <ShieldAlert size={22} />
              ) : isBorderline ? (
                <AlertTriangle size={22} />
              ) : (
                <ShieldCheck size={22} />
              )}
              <span>{riskBand} Risk Category</span>
            </div>
            
            <p className="disclaimer">
              {prediction.requires_recourse 
                ? '⚠ Risk threshold ≥ 20.0% met. Prescriptive counterfactual recourse generation active.' 
                : '✓ Risk threshold within guideline boundaries. Preventive lifestyle guidance recommended.'}
            </p>

            {latencyMs !== undefined && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: '#64748b', marginBottom: '1.5rem' }}>
                <Clock size={16} /> Server Pipeline Latency: <strong>{latencyMs}ms</strong> (SLA &lt; 1400ms)
              </div>
            )}

            <button className="btn-gradient-cta" onClick={onNext}>
              Explain Risk Attribution (SHAP) <ActivitySquare size={20} className="ml-2" />
            </button>
          </div>

          {/* Right Column: Heart Visualization */}
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
