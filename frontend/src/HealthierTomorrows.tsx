import React from 'react';
import { ArrowLeft, Sunrise, HeartHandshake, TrendingUp, CalendarCheck, Home, Target } from 'lucide-react';
import './HealthierTomorrows.css';
import type { RecourseResponse } from './api';

interface HealthierTomorrowsProps {
  recourse?: RecourseResponse;
  selectedPathwayId?: number;
  onBack: () => void;
  onHome: () => void;
}

const HealthierTomorrows: React.FC<HealthierTomorrowsProps> = ({ recourse, selectedPathwayId, onBack, onHome }) => {
  const activePathway = (selectedPathwayId !== undefined
    ? recourse?.pathways?.find((p) => p.pathway_id === selectedPathwayId)
    : null) || recourse?.pathways?.[0];

  const baselinePct = recourse?.patient_baseline_risk ? (recourse.patient_baseline_risk * 100).toFixed(1) : null;
  const projectedPct = activePathway?.projected_risk_percentage.toFixed(1);
  const reductionPct = activePathway?.absolute_risk_reduction.toFixed(1);

  const bpChange = activePathway?.changes?.find((c) => c.feature === 'sysBP');
  const smokeChange = activePathway?.changes?.find((c) => c.feature === 'cigsPerDay');
  const lipidChange = activePathway?.changes?.find((c) => c.feature === 'totChol');
  const glucoseChange = activePathway?.changes?.find((c) => c.feature === 'glucose');
  const bmiChange = activePathway?.changes?.find((c) => c.feature === 'BMI');

  return (
    <div className="tomorrows-container">
      <nav className="tomorrows-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Action Plan
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      <main className="tomorrows-main">
        <div className="tomorrows-header fade-up">
          <h1 className="tomorrows-title shiny-heading-text">Healthier Tomorrows</h1>
          <p className="tomorrows-subtitle">
            Your cardiovascular journey doesn't end with a risk score. This is your personalized, clinically optimized milestone roadmap to sustained longevity.
          </p>
        </div>

        {activePathway && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.8)',
            border: '1px solid #bae6fd',
            borderRadius: '1rem',
            padding: '1.25rem 1.75rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            boxShadow: '0 4px 15px rgba(2, 132, 199, 0.08)'
          }} className="fade-up">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ background: '#e0f2fe', color: '#0284c7', padding: '0.6rem', borderRadius: '0.5rem' }}>
                <Target size={24} />
              </div>
              <div>
                <div style={{ fontWeight: 700, color: '#0f172a' }}>Personalized Clinical Target Vector</div>
                <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                  Following <strong>{activePathway.title}</strong> ({activePathway.changes.length} actionable modifications)
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>10-Yr ASCVD Risk</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0284c7' }}>
                  {baselinePct}% <span style={{ color: '#94a3b8', fontWeight: 400 }}>→</span> {projectedPct}%
                </div>
              </div>
              <span style={{
                background: '#dcfce7',
                color: '#15803d',
                padding: '0.4rem 0.8rem',
                borderRadius: '9999px',
                fontWeight: 700,
                fontSize: '0.85rem'
              }}>
                -{reductionPct}% Drop
              </span>
            </div>
          </div>
        )}

        <div className="journey-timeline fade-up" style={{ animationDelay: '0.2s' }}>
          {/* Week 1 */}
          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#0ea5e9' }}>
              <Sunrise size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Week 1 - The Beginning</div>
              <h3 className="step-title">Immediate Hemodynamic &amp; Lifestyle Action</h3>
              <p className="step-desc">
                {smokeChange && smokeChange.delta < 0 ? (
                  <><strong>Immediate Smoking Cessation:</strong> Eliminate cigarette consumption (target: 0 cigs/day). </>
                ) : null}
                {bpChange ? (
                  <>Begin sodium restriction and guideline medication to target Systolic BP of <strong>{bpChange.target_value} mmHg</strong> ({bpChange.delta > 0 ? `+${bpChange.delta}` : bpChange.delta} mmHg). </>
                ) : (
                  <>Begin daily blood pressure monitoring and adopt dietary sodium restrictions. </>
                )}
                Establish your baseline adherence log with your primary care physician.
              </p>
            </div>
          </div>

          {/* Month 3 */}
          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#8b5cf6' }}>
              <TrendingUp size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Month 3 - Building Habits</div>
              <h3 className="step-title">Metabolic &amp; Lipid Stabilization</h3>
              <p className="step-desc">
                {lipidChange ? (
                  <><strong>Lipid Target:</strong> Total serum cholesterol goal of <strong>{lipidChange.target_value} mg/dL</strong> ({lipidChange.delta} mg/dL). </>
                ) : null}
                {glucoseChange ? (
                  <><strong>Glycemic Control:</strong> Maintain fasting glucose beneath <strong>{glucoseChange.target_value} mg/dL</strong>. </>
                ) : null}
                Your cardiovascular vascular compliance begins to regenerate. Schedule your 90-day clinical panel to verify lipid response.
              </p>
            </div>
          </div>

          {/* Month 6 */}
          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#10b981' }}>
              <HeartHandshake size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Month 6 - Target Achieved</div>
              <h3 className="step-title">Risk Reduction Realized</h3>
              <p className="step-desc">
                {bmiChange ? (
                  <><strong>Body Mass Index:</strong> Achieve target BMI of <strong>{bmiChange.target_value} kg/m²</strong> ({bmiChange.delta} kg/m² drop through regular exercise). </>
                ) : null}
                By adhering to this personalized pathway, your projected 10-year risk has dropped beneath the clinical threshold to <strong>{projectedPct || 'low-risk target'}%</strong>.
              </p>
            </div>
          </div>

          {/* Year 1 */}
          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#f59e0b' }}>
              <CalendarCheck size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Year 1 &amp; Beyond</div>
              <h3 className="step-title">Lifelong Cardiovascular Vitality</h3>
              <p className="step-desc">
                Sustained cardiovascular risk protection of <strong>-{reductionPct || '10'}%</strong> achieved. Continue annual ASCVD surveillance, maintain your healthy biomarker levels, and enjoy a thriving, active life.
              </p>
            </div>
          </div>
        </div>

        <div className="vision-board fade-up" style={{ animationDelay: '0.4s' }}>
          <div className="vision-quote">
            "The best time to plant a tree was 20 years ago. The second best time is today. Your heart health is no different."
          </div>
          <div className="vision-author">— CardioRecourse Clinical CDSS Philosophy</div>
        </div>

        <div className="tomorrows-footer fade-up" style={{ animationDelay: '0.5s' }}>
          <button className="btn-gradient-cta" onClick={onHome}>
            <Home size={18} className="mr-2" /> Return to Home
          </button>
        </div>
      </main>
      
      <div className="bg-glow blue-glow-alt"></div>
      <div className="bg-glow teal-glow"></div>
    </div>
  );
};

export default HealthierTomorrows;
