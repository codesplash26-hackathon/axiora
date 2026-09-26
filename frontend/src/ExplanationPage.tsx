import { ArrowLeft, ArrowRight, Info, TrendingUp, Sparkles } from 'lucide-react';
import './ExplanationPage.css';
import type { ExplanationResponse } from './api';

interface ExplanationPageProps {
  explanation: ExplanationResponse;
  onBack: () => void;
  onNext: () => void;
}

const NON_MODIFIABLE_FEATURES = new Set(['age', 'male', 'prevalentStroke', 'prevalentHyp', 'diabetes']);

export default function ExplanationPage({ explanation, onBack, onNext }: ExplanationPageProps) {
  const attributions = explanation.attributions || [];
  
  // Find maximum attribution magnitude to scale chart bars dynamically
  const maxAbsVal = Math.max(...attributions.map((a) => Math.abs(a.attribution_value)), 0.01);

  // Identify top modifiable factor driving risk for actionable clinical opportunity
  const topModifiableRisk = [...attributions]
    .filter((a) => !NON_MODIFIABLE_FEATURES.has(a.feature) && a.direction === 'risk_increasing')
    .sort((a, b) => b.attribution_value - a.attribution_value)[0];

  const riskPctDisplay = (explanation.risk_score * 100).toFixed(1);
  const baselinePctDisplay = (explanation.base_value * 100).toFixed(1);

  return (
    <div className="explanation-container">
      <nav className="explanation-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Result
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="explanation-main">
        <div className="explanation-header fade-up">
          <h1 className="explanation-title shiny-heading-text">Diagnostic Risk Attribution</h1>
          <p className="explanation-subtitle">
            Local TreeSHAP attributions in margin space (Base: {explanation.base_log_odds !== undefined ? `${explanation.base_log_odds.toFixed(2)} log-odds` : `${baselinePctDisplay}%`} → Patient: {riskPctDisplay}% calibrated risk).
          </p>
        </div>

        <div className="explanation-grid fade-up-delay">
          {/* Left Column: SHAP Visualization */}
          <div className="shap-panel glass-card">
            <h2 className="panel-title">Feature Attribution Waterfall</h2>
            
            <div className="shap-chart">
              <div className="chart-center-line"></div>
              
              {attributions.map((factor, index) => {
                const isModifiable = !NON_MODIFIABLE_FEATURES.has(factor.feature);
                const absVal = Math.abs(factor.attribution_value);
                const barWidth = Math.min(100, Math.max(14, Math.round((absVal / maxAbsVal) * 88)));
                const pctDelta = factor.marginal_percentage_impact !== undefined && factor.marginal_percentage_impact !== null
                  ? ` (${factor.marginal_percentage_impact >= 0 ? '+' : ''}${factor.marginal_percentage_impact.toFixed(1)}% risk)`
                  : '';
                const formattedVal = `${factor.attribution_value >= 0 ? '+' : ''}${factor.attribution_value.toFixed(2)} log-odds${pctDelta}`;
                const isIncrease = factor.direction === 'risk_increasing';
                const isSmall = barWidth < 25;

                return (
                  <div key={factor.feature || index} className="shap-row" style={{ animationDelay: `${index * 0.08}s` }}>
                    <div className="shap-label">
                      <span className="factor-name">{factor.display_name}</span>
                      <span className={`factor-badge ${isModifiable ? 'mod' : 'non-mod'}`}>
                        {isModifiable ? 'Modifiable' : 'Fixed'}
                      </span>
                    </div>
                    
                    <div className="shap-bar-container">
                      {!isIncrease && (
                        <div className="shap-bar-left">
                          <div className="shap-fill decrease-fill" style={{ width: `${barWidth}%` }}>
                            <span className={`shap-value ${isSmall ? 'shap-value-outside-left' : ''}`}>
                              {formattedVal}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      <div className="shap-center-point"></div>
                      
                      {isIncrease && (
                        <div className="shap-bar-right">
                          <div className="shap-fill increase-fill" style={{ width: `${barWidth}%` }}>
                            <span className={`shap-value ${isSmall ? 'shap-value-outside-right' : ''}`}>
                              {formattedVal}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="chart-legend">
              <div className="legend-item">
                <div className="legend-color decrease-color"></div>
                <span>Protective Factor (Reduces ASCVD Log-Odds)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color increase-color"></div>
                <span>Risk Driver (Elevates ASCVD Log-Odds)</span>
              </div>
            </div>
          </div>

          {/* Right Column: Information & Actions */}
          <div className="info-panel">
            <div className="info-card glass-card fade-up-delay-2">
              <h3 className="info-title"><Info size={20} /> Model Explainability</h3>
              <p className="info-text">
                The TreeExplainer decomposed your individual <strong>{riskPctDisplay}%</strong> risk score relative to the population expectation of <strong>{baselinePctDisplay}%</strong>.
              </p>
              <p className="info-text">
                Factors extending to the <strong>right</strong> increase cardiovascular log-odds risk, while bars to the <strong>left</strong> indicate protective features.
              </p>
            </div>

            {topModifiableRisk ? (
              <div className="impact-summary glass-card fade-up-delay-3">
                <h3 className="info-title">Primary Clinical Target</h3>
                <div className="opportunity-highlight">
                  <TrendingUp size={24} className="text-red-500" />
                  <div>
                    <h4>{topModifiableRisk.display_name}</h4>
                    <p>
                      This modifiable biomarker currently contributes{' '}
                      <strong>+{topModifiableRisk.attribution_value.toFixed(2)} log-odds</strong> to the patient&apos;s overall risk profile.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="impact-summary glass-card fade-up-delay-3">
                <h3 className="info-title">Profile Summary</h3>
                <div className="opportunity-highlight">
                  <Sparkles size={24} className="text-green-500" />
                  <div>
                    <h4>Optimized Biomarkers</h4>
                    <p>No critical modifiable biomarkers currently exceed normal physiological thresholds.</p>
                  </div>
                </div>
              </div>
            )}

            <button className="btn-gradient-cta btn-pathways fade-up-delay-4" onClick={onNext}>
              Explore Prescriptive Recourse (DiCE) <ArrowRight size={20} className="ml-2" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
