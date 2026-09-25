import { useEffect, useState } from 'react';
import './App.css';
import heartImg from './assets/shiny_tech_heart.png';
import { Activity, Brain, Search, Heart, Utensils, Dumbbell, Ban, GitMerge, HeartPulse, AlertTriangle, Home, ClipboardList, PieChart, Info, Map, User, Stethoscope, Sunrise } from 'lucide-react';
import RiskAssessment from './RiskAssessment';
import PredictionResult from './PredictionResult';
import ExplanationPage from './ExplanationPage';
import RecoursePage from './RecoursePage';
import DoctorLoginModal from './DoctorLoginModal';
import DoctorDashboardPage from './DoctorDashboardPage';
import HealthierTomorrows from './HealthierTomorrows';
import { assessPatient } from './api';
import type { PatientInput, AssessmentResponse } from './api';

const App = () => {
  const [mounted, setMounted] = useState(false);
  const [currentPage, setCurrentPage] = useState<'landing' | 'assessment' | 'prediction' | 'explanation' | 'recourse' | 'tomorrows' | 'doctor-dashboard'>('landing');
  const [assessmentData, setAssessmentData] = useState<AssessmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [doctorUser, setDoctorUser] = useState<{ id: string; name: string; email: string } | null>(null);
  const [isDoctorLoginOpen, setIsDoctorLoginOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleAnalyzePatient = async (patient: PatientInput) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await assessPatient(patient);
      setAssessmentData(response);
      setCurrentPage('prediction');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reach clinical decision engine';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAssessmentData(null);
    setErrorMessage(null);
    setCurrentPage('landing');
  };

  return (
    <>
      {/* Global Falling Leaves Animation */}
      {currentPage !== 'prediction' && currentPage !== 'doctor-dashboard' && (
        <div className="leaves-container global-leaves">
          {[...Array(7)].map((_, i) => {
            // On landing page, keep leaves on the right half
            // On other pages, let them fall everywhere
            const leftPos = (currentPage === 'landing') ? (55 + Math.random() * 40) : (5 + Math.random() * 90);
            return (
            <div key={i} className={`global-falling-leaf g-leaf-${(i % 4) + 1}`} style={{
              left: `${leftPos}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${7 + Math.random() * 5}s`
            }}></div>
          );
        })}
      </div>
      )}

      {/* Global Real-Time Loading Overlay */}
      {isLoading && (
        <div className="result-container flex-center" style={{ position: 'fixed', inset: 0, zIndex: 9999 }}>
          <div className="loading-state">
            <div className="loading-circles">
              <div className="circle-1"></div>
              <div className="circle-2"></div>
              <HeartPulse size={48} className="pulse-icon" />
            </div>
            <h2 className="loading-text">Computing Calibrated Risk &amp; Recourse...</h2>
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
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Enforcing sub-1.4s SLA across XGBoost, TreeSHAP, and DiCE
            </p>
          </div>
        </div>
      )}

      {/* Global Error Banner */}
      {errorMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 10000,
          background: '#fee2e2',
          border: '1px solid #fecaca',
          color: '#b91c1c',
          padding: '1rem 1.5rem',
          borderRadius: '0.75rem',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          maxWidth: '450px'
        }}>
          <AlertTriangle size={24} />
          <div>
            <div style={{ fontWeight: 700 }}>Inference Request Error</div>
            <div style={{ fontSize: '0.85rem' }}>{errorMessage}</div>
          </div>
          <button 
            onClick={() => setErrorMessage(null)} 
            style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
          >
            ✕
          </button>
        </div>
      )}

      <DoctorLoginModal 
        isOpen={isDoctorLoginOpen} 
        onClose={() => setIsDoctorLoginOpen(false)} 
        onLogin={(doc) => {
          setDoctorUser(doc);
          setCurrentPage('doctor-dashboard');
        }}
      />

      {/* Global Side Navigation Panel */}
      {!doctorUser && (
        <div className="side-nav-panel">
          <button 
            className={`side-nav-item ${currentPage === 'landing' ? 'active' : ''}`}
            data-tooltip="Home"
            onClick={() => setCurrentPage('landing')}
          >
            <Home size={20} />
          </button>
          <button 
            className={`side-nav-item ${currentPage === 'assessment' ? 'active' : ''}`}
            data-tooltip="Risk Assessment"
            onClick={() => setCurrentPage('assessment')}
          >
            <ClipboardList size={20} />
          </button>
          <button 
            className={`side-nav-item ${currentPage === 'prediction' ? 'active' : ''}`}
            data-tooltip="Prediction Results"
            onClick={() => {
              if (assessmentData) setCurrentPage('prediction');
              else setCurrentPage('assessment');
            }}
          >
            <PieChart size={20} />
          </button>
          <button 
            className={`side-nav-item ${currentPage === 'explanation' ? 'active' : ''}`}
            data-tooltip="AI Explanation (SHAP)"
            onClick={() => {
              if (assessmentData) setCurrentPage('explanation');
              else setCurrentPage('assessment');
            }}
          >
            <Info size={20} />
          </button>
          <button 
            className={`side-nav-item ${currentPage === 'recourse' ? 'active' : ''}`}
            data-tooltip="Action Plan (DiCE)"
            onClick={() => {
              if (assessmentData) setCurrentPage('recourse');
              else setCurrentPage('assessment');
            }}
          >
            <Map size={20} />
          </button>
          <button 
            className={`side-nav-item ${currentPage === 'tomorrows' ? 'active' : ''}`}
            data-tooltip="Healthier Tomorrows"
            onClick={() => {
              if (assessmentData) setCurrentPage('tomorrows');
              else setCurrentPage('assessment');
            }}
          >
            <Sunrise size={20} />
          </button>
        </div>
      )}

      {currentPage === 'landing' ? (
        <div className={`landing-container ${mounted ? 'mounted' : ''}`}>

          {/* Navigation */}
          <nav className="navbar fade-in-delay">
            <div className="nav-logo">
              <Heart className="logo-heart-nav" size={28} />
            </div>
            <div className="nav-actions">
              {doctorUser ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a', fontWeight: 600 }}>
                    <Stethoscope size={18} color="#0284c7" />
                    <span>{doctorUser.name}</span>
                  </div>
                  <button className="btn-login" onClick={() => { setDoctorUser(null); setCurrentPage('landing'); }}>Sign Out</button>
                  <button className="btn-signup" onClick={() => setCurrentPage('doctor-dashboard')}>Dashboard</button>
                </div>
              ) : (
                <button className="btn-signup" onClick={() => setIsDoctorLoginOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Stethoscope size={18} /> Doctor Portal
                </button>
              )}
            </div>
          </nav>

          {/* Background Soft Glows */}
          <div className="bg-glow blue-glow"></div>
          <div className="bg-glow teal-glow"></div>

          {/* Decorative Leaves */}
          <div className="leaf leaf-1"></div>
          <div className="leaf leaf-2"></div>
          <div className="leaf leaf-3"></div>

          {/* Road Graphic at the bottom */}
          <div className="road-container fade-in-delay">
            <svg viewBox="0 0 1440 400" preserveAspectRatio="none" className="road-svg">
              <path
                className="road-path"
                d="M 1440,400 C 1000,400 800,200 400,250 C 200,270 0,200 -100,150 L -100,400 Z"
                fill="url(#road-gradient)"
              />
              <path
                className="road-edge"
                d="M 1440,400 C 1000,400 800,200 400,250 C 200,270 0,200 -100,150"
                fill="none"
                stroke="#bae6fd"
                strokeWidth="4"
              />
              <path
                className="road-dashed"
                d="M 1440,420 C 1000,420 800,220 400,270 C 200,290 0,220 -100,170"
                fill="none"
                stroke="#ffffff"
                strokeWidth="4"
                strokeDasharray="20 25"
                filter="drop-shadow(0 0 6px rgba(255,255,255,0.8))"
              />
              <defs>
                <linearGradient id="road-gradient" x1="100%" y1="0%" x2="0%" y2="0%">
                  <stop offset="0%" stopColor="#7dd3fc" stopOpacity="0.8" />
                  <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.5" />
                  <stop offset="100%" stopColor="#a7f3d0" stopOpacity="0.8" />
                </linearGradient>
              </defs>
            </svg>

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
                  More than a risk score — a personalized, prescriptive path<br />to a healthier heart.
                </p>
              </div>

              <div className="cta-group fade-up-3">
                <button className="btn-primary" onClick={() => setCurrentPage('assessment')}>
                  Check My Risk <span className="arrow">→</span>
                </button>
              </div>

              <div className="features-row fade-up-4">
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

              <div className="credibility fade-up-5">
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
                <div className="heart-aura"></div>
                <div className="orbit-ring orbit-ring-1"></div>
                <div className="orbit-ring orbit-ring-2"></div>

                <div className="heart-wrapper heartbeat-anim">
                  <img src={heartImg} alt="CardioRecourse Heart" className="heart-img" />
                </div>

                <div className="accent-orb orb-1"></div>
                <div className="accent-orb orb-2"></div>
                <div className="accent-orb orb-3"></div>

                <div className="falling-leaf fall-1"></div>
                <div className="falling-leaf fall-2"></div>
                <div className="falling-leaf fall-3"></div>
                <div className="falling-leaf fall-4"></div>
                <div className="falling-leaf fall-5"></div>

                <svg className="ecg-trace" viewBox="0 0 300 60" preserveAspectRatio="none">
                  <path
                    d="M0,30 L60,30 L70,10 L80,50 L90,20 L100,40 L110,30 L300,30"
                    fill="none"
                    stroke="url(#ecg-gradient)"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="ecg-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#38bdf8" stopOpacity="0" />
                      <stop offset="30%" stopColor="#38bdf8" stopOpacity="0.6" />
                      <stop offset="60%" stopColor="#0891b2" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>

          <div className="footer-quote popup-anim">
            Smarter insights.<br />Healthier choices.<br />A safer you.
          </div>
        </div>
      ) : currentPage === 'assessment' ? (
        <RiskAssessment 
          onBack={() => setCurrentPage('landing')} 
          onAnalyze={handleAnalyzePatient} 
          isLoading={isLoading}
        />
      ) : currentPage === 'prediction' && assessmentData ? (
        <PredictionResult 
          prediction={assessmentData.prediction}
          latencyMs={assessmentData.total_latency_ms}
          onBack={() => setCurrentPage('assessment')} 
          onNext={() => setCurrentPage('explanation')}
        />
      ) : currentPage === 'explanation' && assessmentData ? (
        <ExplanationPage
          explanation={assessmentData.explanation}
          onBack={() => setCurrentPage('prediction')}
          onNext={() => setCurrentPage('recourse')}
        />
      ) : currentPage === 'recourse' && assessmentData ? (
        <RecoursePage 
          recourse={assessmentData.recourse}
          onBack={() => setCurrentPage('explanation')}
          onNext={() => setCurrentPage('tomorrows')}
        />
      ) : currentPage === 'tomorrows' ? (
        <HealthierTomorrows
          onBack={() => setCurrentPage('recourse')}
          onHome={handleReset}
        />
      ) : currentPage === 'doctor-dashboard' && doctorUser ? (
        <DoctorDashboardPage 
          doctor={doctorUser} 
          onLogout={() => { setDoctorUser(null); setCurrentPage('landing'); }}
          onNewAssessment={() => setCurrentPage('assessment')}
        />
      ) : (
        <RiskAssessment 
          onBack={() => setCurrentPage('landing')} 
          onAnalyze={handleAnalyzePatient} 
          isLoading={isLoading}
        />
      )}
    </>
  );
};

export default App;
