import React from 'react';
import { ArrowLeft, Sunrise, HeartHandshake, TrendingUp, CalendarCheck, Home } from 'lucide-react';
import './HealthierTomorrows.css';

interface HealthierTomorrowsProps {
  onBack: () => void;
  onHome: () => void;
}

const HealthierTomorrows: React.FC<HealthierTomorrowsProps> = ({ onBack, onHome }) => {
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
            Your cardiovascular journey doesn't end with a risk score. This is your roadmap to a sustained, healthier future based on your personalized clinical recommendations.
          </p>
        </div>

        <div className="journey-timeline fade-up" style={{ animationDelay: '0.2s' }}>
          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#0ea5e9' }}>
              <Sunrise size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Week 1 - The Beginning</div>
              <h3 className="step-title">Implementing the Action Plan</h3>
              <p className="step-desc">
                Start small. Focus on the first 1-2 biomarker changes recommended by your DiCE pathway. Adopt minor dietary adjustments and schedule your first follow-up.
              </p>
            </div>
          </div>

          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#8b5cf6' }}>
              <TrendingUp size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Month 3 - Building Habits</div>
              <h3 className="step-title">Measurable Progress</h3>
              <p className="step-desc">
                Your body begins to adapt. Blood pressure normalizes and lipid profiles show early signs of improvement. Maintain consistency in physical activity and medication adherence.
              </p>
            </div>
          </div>

          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#10b981' }}>
              <HeartHandshake size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Month 6 - Target Achieved</div>
              <h3 className="step-title">Risk Reduction Realized</h3>
              <p className="step-desc">
                Congratulations! By sticking to the optimized pathway, you have successfully lowered your 10-year cardiovascular risk beneath the critical clinical threshold.
              </p>
            </div>
          </div>

          <div className="timeline-step">
            <div className="step-icon-wrapper" style={{ color: '#f59e0b' }}>
              <CalendarCheck size={28} />
            </div>
            <div className="step-content">
              <div className="step-time">Year 1 & Beyond</div>
              <h3 className="step-title">Lifelong Vitality</h3>
              <p className="step-desc">
                A healthier heart means more time for what matters most. Continue annual check-ups, maintain your new lifestyle, and enjoy a thriving, active life.
              </p>
            </div>
          </div>
        </div>

        <div className="vision-board fade-up" style={{ animationDelay: '0.4s' }}>
          <div className="vision-quote">
            "The best time to plant a tree was 20 years ago. The second best time is today. Your heart health is no different."
          </div>
          <div className="vision-author">— CardioRecourse Philosophy</div>
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
