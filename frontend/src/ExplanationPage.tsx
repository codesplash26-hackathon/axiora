import { ArrowLeft, ArrowRight, Info, TrendingUp, TrendingDown } from 'lucide-react';
import './ExplanationPage.css';

interface ExplanationPageProps {
  onBack: () => void;
  onNext: () => void;
}

const factors = [
  { id: 1, name: 'Blood Pressure', value: '+5.2%', type: 'increase', modifiable: true },
  { id: 2, name: 'Cholesterol', value: '+3.1%', type: 'increase', modifiable: true },
  { id: 3, name: 'Age', value: '+2.4%', type: 'increase', modifiable: false },
  { id: 4, name: 'Physical Activity', value: '-1.5%', type: 'decrease', modifiable: true },
  { id: 5, name: 'Non-Smoker', value: '-2.0%', type: 'decrease', modifiable: true },
];

export default function ExplanationPage({ onBack, onNext }: ExplanationPageProps) {
  return (
    <div className="explanation-container">
      {/* Falling Leaves Animation */}
      <div className="leaves-container">
        {[...Array(15)].map((_, i) => (
          <div key={i} className={`leaf leaf-${(i % 4) + 1}`} style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${5 + Math.random() * 5}s`
          }}></div>
        ))}
      </div>

      <nav className="explanation-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Result
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="explanation-main">
        <div className="explanation-header fade-up">
          <h1 className="explanation-title">Your Risk, Explained</h1>
          <p className="explanation-subtitle">Understand the exact factors driving your AI risk prediction.</p>
        </div>

        <div className="explanation-grid fade-up-delay">
          {/* Left Column: SHAP Visualization */}
          <div className="shap-panel glass-card">
            <h2 className="panel-title">Top Contributing Factors</h2>
            
            <div className="shap-chart">
              <div className="chart-center-line"></div>
              
              {factors.map((factor, index) => (
                <div key={factor.id} className="shap-row" style={{ animationDelay: `${index * 0.15}s` }}>
                  <div className="shap-label">
                    <span className="factor-name">{factor.name}</span>
                    <span className={`factor-badge ${factor.modifiable ? 'mod' : 'non-mod'}`}>
                      {factor.modifiable ? 'Modifiable' : 'Fixed'}
                    </span>
                  </div>
                  
                  <div className="shap-bar-container">
                    {factor.type === 'decrease' && (
                      <div className="shap-bar-left">
                        <div className="shap-fill decrease-fill" style={{ width: '60%' }}>
                          <span className="shap-value">{factor.value}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="shap-center-point"></div>
                    
                    {factor.type === 'increase' && (
                      <div className="shap-bar-right">
                        <div className="shap-fill increase-fill" style={{ width: factor.value === '+5.2%' ? '80%' : factor.value === '+3.1%' ? '50%' : '35%' }}>
                          <span className="shap-value">{factor.value}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="chart-legend">
              <div className="legend-item">
                <div className="legend-color decrease-color"></div>
                <span>Reduces Risk</span>
              </div>
              <div className="legend-item">
                <div className="legend-color increase-color"></div>
                <span>Increases Risk</span>
              </div>
            </div>
          </div>

          {/* Right Column: Information & Actions */}
          <div className="info-panel">
            <div className="info-card glass-card fade-up-delay-2">
              <h3 className="info-title"><Info size={20} /> What does this mean?</h3>
              <p className="info-text">
                This visualization uses <strong>SHAP</strong> (SHapley Additive exPlanations) to show exactly how much each of your health details contributed to the final 18.7% risk prediction.
              </p>
              <p className="info-text">
                Factors extending to the <strong>right</strong> increased your risk, while factors extending to the <strong>left</strong> lowered it.
              </p>
            </div>

            <div className="impact-summary glass-card fade-up-delay-3">
              <h3 className="info-title">Your Biggest Opportunity</h3>
              <div className="opportunity-highlight">
                <TrendingUp size={24} className="text-red-500" />
                <div>
                  <h4>Blood Pressure</h4>
                  <p>This modifiable factor is currently adding <strong>5.2%</strong> to your overall risk score.</p>
                </div>
              </div>
            </div>

            <button className="btn-gradient-cta btn-pathways fade-up-delay-4" onClick={onNext}>
              Explore Personalized Pathways <ArrowRight size={20} className="ml-2" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
