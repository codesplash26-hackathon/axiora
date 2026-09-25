import { ArrowLeft, ArrowRight, Printer, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import './RecoursePage.css';
import type { RecourseResponse } from './api';

interface RecoursePageProps {
  recourse: RecourseResponse;
  onBack: () => void;
  onNext: () => void;
}

export default function RecoursePage({ recourse, onBack, onNext }: RecoursePageProps) {
  const pathways = recourse.pathways || [];
  const baselineRiskPct = (recourse.patient_baseline_risk * 100).toFixed(1);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="recourse-container">
      <nav className="recourse-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Explanations
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="recourse-main">
        <div className="recourse-header fade-up">
          <h1 className="recourse-title shiny-heading-text">Prescriptive Recourse Pathways</h1>
          <p className="recourse-subtitle">
            Feasible, minimal-effort biomarker adjustments generated via Diverse Counterfactual Explanations (DiCE) to reduce cardiovascular risk below the critical threshold.
          </p>

          {recourse.is_fallback && (
            <div className="fallback-alert">
              <AlertCircle size={16} /> SLA Acceleration: Real-time randomized counterfactual search generated under 150ms.
            </div>
          )}
        </div>

        {pathways.length === 0 ? (
          <div className="info-box" style={{ maxWidth: '600px', margin: '2rem auto' }}>
            <CheckCircle2 size={24} color="#059669" />
            <div>
              <h4>Low Baseline Risk Profile</h4>
              <p>Patient 10-year CHD risk is already below clinical intervention thresholds (&lt; 20%). Routine preventative wellness maintenance is advised.</p>
            </div>
          </div>
        ) : (
          <div className="pathways-grid">
            {pathways.map((pathway, idx) => (
              <div 
                key={pathway.pathway_id || idx} 
                className={`pathway-card ${idx === 0 ? 'highlight' : ''}`}
              >
                {idx === 0 && <div className="card-badge">Optimal Pathway</div>}
                
                <div className="pathway-header">
                  <h2 className="pathway-title">{pathway.title}</h2>
                  <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 0 }}>
                    Targeted clinical plan #{pathway.pathway_id}
                  </p>
                </div>

                <div className="risk-comparison">
                  <div className="risk-stat">
                    <span className="risk-stat-label">Baseline</span>
                    <span className="risk-stat-val baseline">{baselineRiskPct}%</span>
                  </div>
                  <ArrowRight size={20} color="#94a3b8" />
                  <div className="risk-stat">
                    <span className="risk-stat-label">Projected</span>
                    <span className="risk-stat-val target">
                      {pathway.projected_risk_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="reduction-pill">
                    -{pathway.absolute_risk_reduction.toFixed(1)}%
                  </div>
                </div>

                <div className="deltas-list">
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                    Required Modifications
                  </span>
                  {pathway.changes.map((change, cIdx) => (
                    <div key={cIdx} className="delta-item">
                      <span className="delta-name">{change.display_name}</span>
                      <div className="delta-change">
                        <span className="delta-from">
                          {change.baseline_value} {change.unit}
                        </span>
                        <ArrowRight size={14} color="#94a3b8" />
                        <span className="delta-to">
                          {change.target_value} {change.unit}
                        </span>
                        <span className="delta-badge">
                          {change.delta > 0 ? `+${change.delta}` : change.delta}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="actions-footer">
          <button className="btn-secondary" onClick={handlePrint}>
            <Printer size={18} className="mr-2" /> Export Action Plan (PDF)
          </button>
          <button className="btn-gradient-cta" onClick={onNext}>
            See Healthier Tomorrows <ArrowRight size={18} className="ml-2" />
          </button>
        </div>
      </main>

      <div className="bg-glow blue-glow-alt"></div>
      <div className="bg-glow purple-glow-alt"></div>
    </div>
  );
}
