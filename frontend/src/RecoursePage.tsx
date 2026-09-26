import { useMemo, useState, useEffect } from 'react';
import { ArrowLeft, ArrowRight, Printer, AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import './RecoursePage.css';
import type { RecourseResponse } from './api';

interface RecoursePageProps {
  recourse: RecourseResponse;
  selectedPathwayId?: number;
  onSelectPathway?: (pathwayId: number) => void;
  onBack: () => void;
  onNext: (selectedPathwayId?: number) => void;
}

export default function RecoursePage({
  recourse,
  selectedPathwayId: externalSelectedPathwayId,
  onSelectPathway,
  onBack,
  onNext,
}: RecoursePageProps) {
  const pathways = recourse.pathways || [];
  const baselineRisk = recourse.patient_baseline_risk ?? 0;
  const baselineRiskPct = (baselineRisk * 100).toFixed(1);
  const isHighRisk = baselineRisk >= 0.20;

  // Dynamically identify the "Optimal Pathway" by lowest projected_risk_score
  const optimalPathwayId = useMemo(() => {
    if (!pathways.length) return null;
    return pathways.reduce((best, curr) => 
      curr.projected_risk_score < best.projected_risk_score ? curr : best
    , pathways[0]).pathway_id;
  }, [pathways]);

  // Interactive selection state: defaults to optimal or external prop, but updates on user selection
  const [selectedPathwayId, setSelectedPathwayId] = useState<number>(() => {
    if (externalSelectedPathwayId !== undefined) return externalSelectedPathwayId;
    return optimalPathwayId || pathways[0]?.pathway_id || 1;
  });

  useEffect(() => {
    if (externalSelectedPathwayId !== undefined) {
      setSelectedPathwayId(externalSelectedPathwayId);
    } else if (optimalPathwayId && !pathways.some(p => p.pathway_id === selectedPathwayId)) {
      setSelectedPathwayId(optimalPathwayId);
    }
  }, [externalSelectedPathwayId, optimalPathwayId, pathways]);

  const handleSelectPathway = (id: number) => {
    setSelectedPathwayId(id);
    if (onSelectPathway) {
      onSelectPathway(id);
    }
  };

  const selectedPathway = pathways.find(p => p.pathway_id === selectedPathwayId) || pathways[0];

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
            Feasible, minimal-effort biomarker adjustments generated via Diverse Counterfactual Explanations (DiCE) to reduce cardiovascular risk below the critical threshold. Click any pathway to customize your actionable roadmap.
          </p>

          {recourse.is_fallback && (
            <div className="fallback-alert">
              <AlertCircle size={16} /> SLA Acceleration: Real-time randomized counterfactual search generated under 150ms.
            </div>
          )}
        </div>

        {pathways.length === 0 ? (
          !isHighRisk ? (
            <div className="info-box" style={{ maxWidth: '600px', margin: '2rem auto' }}>
              <CheckCircle2 size={24} color="#059669" />
              <div>
                <h4>Low Baseline Risk Profile ({baselineRiskPct}%)</h4>
                <p>Patient 10-year CHD risk is already below clinical intervention thresholds (&lt; 20%). Routine preventative wellness maintenance is advised.</p>
              </div>
            </div>
          ) : (
            <div className="info-box" style={{ maxWidth: '650px', margin: '2rem auto', borderColor: '#f87171', background: '#fef2f2' }}>
              <AlertTriangle size={24} color="#dc2626" />
              <div>
                <h4 style={{ color: '#b91c1c' }}>High Baseline Risk Profile ({baselineRiskPct}%) — Recourse Optimization Unavailable</h4>
                <p style={{ color: '#7f1d1d' }}>
                  The optimization engine was unable to compute feasible counterfactual target pathways within the safe clinical threshold. Immediate clinician review and manual guideline-directed medical therapy (GDMT) are required.
                </p>
              </div>
            </div>
          )
        ) : (
          <div className="pathways-grid">
            {pathways.map((pathway, idx) => {
              const isOptimal = pathway.pathway_id === optimalPathwayId;
              const isSelected = pathway.pathway_id === selectedPathwayId;
              const reduction = pathway.absolute_risk_reduction ?? 0;
              const formattedReduction = reduction > 0
                ? `-${reduction.toFixed(1)}%`
                : reduction < 0
                ? `+${Math.abs(reduction).toFixed(1)}%`
                : '0.0%';

              return (
                <div 
                  key={pathway.pathway_id || idx} 
                  className={`pathway-card ${isSelected ? 'selected' : ''} ${isOptimal ? 'highlight' : ''}`}
                  onClick={() => handleSelectPathway(pathway.pathway_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleSelectPathway(pathway.pathway_id);
                    }
                  }}
                  aria-pressed={isSelected}
                >
                  <div className="card-badges-wrapper">
                    {isOptimal && <div className="card-badge optimal">Optimal Pathway</div>}
                    {isSelected && (
                      <div className="card-badge selected">
                        <CheckCircle2 size={13} style={{ display: 'inline', verticalAlign: '-1px', marginRight: '3px' }} />
                        Selected
                      </div>
                    )}
                  </div>
                  
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
                      {formattedReduction}
                    </div>
                  </div>

                  <div className="deltas-list">
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                      Required Modifications
                    </span>
                    {(pathway.changes || []).map((change, cIdx) => (
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

                  <button
                    type="button"
                    className={`btn-select-pathway ${isSelected ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectPathway(pathway.pathway_id);
                    }}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle2 size={16} /> Selected Pathway
                      </>
                    ) : (
                      <>Choose This Pathway</>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <div className="actions-footer">
          <button className="btn-secondary" onClick={handlePrint}>
            <Printer size={18} className="mr-2" /> Export Action Plan (PDF)
          </button>
          <button className="btn-gradient-cta" onClick={() => onNext(selectedPathwayId)}>
            See Healthier Tomorrows {selectedPathway ? `(${selectedPathway.title})` : ''} <ArrowRight size={18} className="ml-2" />
          </button>
        </div>
      </main>

      <div className="bg-glow blue-glow-alt"></div>
      <div className="bg-glow purple-glow-alt"></div>
    </div>
  );
}
