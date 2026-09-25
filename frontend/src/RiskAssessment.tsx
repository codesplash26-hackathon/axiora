import { useState } from 'react';
import './RiskAssessment.css';
import { ArrowLeft, User, Activity, HeartPulse, ChevronRight, ActivitySquare, AlertCircle } from 'lucide-react';
import type { PatientInput } from './api';

interface RiskAssessmentProps {
  onBack: () => void;
  onAnalyze: (patient: PatientInput) => void;
  isLoading?: boolean;
}

const steps = [
  { id: 1, title: 'Personal Profile' },
  { id: 2, title: 'Vitals & Labs' },
  { id: 3, title: 'Medical & Lifestyle' }
];

export default function RiskAssessment({ onBack, onAnalyze, isLoading }: RiskAssessmentProps) {
  const [currentStep, setCurrentStep] = useState(1);

  const [formData, setFormData] = useState<PatientInput>({
    male: 1,
    age: 52,
    currentSmoker: 1,
    cigsPerDay: 15,
    BPMeds: 0,
    prevalentStroke: 0,
    prevalentHyp: 1,
    diabetes: 0,
    totChol: 240,
    sysBP: 145,
    diaBP: 92,
    BMI: 28.4,
    heartRate: 76,
    glucose: 96,
  });

  const updateField = <K extends keyof PatientInput>(key: K, value: PatientInput[K]) => {
    setFormData((prev) => {
      const updated = { ...prev, [key]: value };

      // Enforce bidirectional smoking coherence rules
      if (key === 'currentSmoker') {
        if (value === 0) {
          updated.cigsPerDay = 0;
        } else if (value === 1 && prev.cigsPerDay === 0) {
          updated.cigsPerDay = 10;
        }
      } else if (key === 'cigsPerDay') {
        const cigs = Number(value);
        if (cigs <= 0) {
          updated.currentSmoker = 0;
          updated.cigsPerDay = 0;
        } else {
          updated.currentSmoker = 1;
          updated.cigsPerDay = Math.min(70, Math.max(0, cigs));
        }
      }

      return updated;
    });
  };

  const handleNext = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (currentStep < 3) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleAnalyze = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (currentStep === 3 && !isLoading) {
      // Final client-side sanitization to guarantee Pydantic schema compliance
      const sanitized = { ...formData };
      if (sanitized.currentSmoker === 0) {
        sanitized.cigsPerDay = 0;
      } else if (sanitized.cigsPerDay <= 0) {
        sanitized.currentSmoker = 0;
        sanitized.cigsPerDay = 0;
      }
      onAnalyze(sanitized);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (currentStep < 3) {
        handleNext();
      } else {
        handleAnalyze();
      }
    }
  };

  return (
    <div className="assessment-container" onKeyDown={handleKeyDown}>
      {/* Navigation Bar */}
      <nav className="assessment-nav">
        <button type="button" className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Home
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      {/* Main Content Area */}
      <main className="assessment-main">
        <div className="assessment-header">
          <h1 className="assessment-title shiny-heading-text">Clinical Risk Assessment</h1>
          <p className="assessment-subtitle">
            Provide patient biomarkers and history for calibrated 10-year CHD prediction and prescriptive recourse.
          </p>
        </div>

        {/* Progress Bar (Clickable steps) */}
        <div className="progress-container">
          <div className="progress-labels">
            {steps.map((step) => (
              <div 
                key={step.id} 
                className={`progress-label ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}
                onClick={() => setCurrentStep(step.id)}
                style={{ cursor: 'pointer' }}
                title={`Go to step ${step.id}: ${step.title}`}
              >
                <span className="step-num">0{step.id}</span> {step.title}
              </div>
            ))}
          </div>
          <div className="progress-track">
            <div 
              className="progress-fill" 
              style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Step Content Container (Pure DIV to prevent accidental HTML form submit) */}
        <div className="form-container">
          {/* STEP 1: Personal Profile */}
          {currentStep === 1 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><User size={24} className="step-icon" /> Step 1: Personal &amp; Biometrics</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label htmlFor="input-age">Age (years)</label>
                  <input 
                    id="input-age"
                    type="number" 
                    min="18" 
                    max="120" 
                    value={formData.age} 
                    onChange={(e) => updateField('age', parseFloat(e.target.value) || 18)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-sex">Biological Sex</label>
                  <select 
                    id="input-sex"
                    value={formData.male} 
                    onChange={(e) => updateField('male', parseInt(e.target.value, 10))}
                  >
                    <option value={1}>Male</option>
                    <option value={0}>Female</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="input-bmi">Body Mass Index (BMI, kg/m²)</label>
                  <input 
                    id="input-bmi"
                    type="number" 
                    step="0.1" 
                    min="15" 
                    max="55" 
                    value={formData.BMI} 
                    onChange={(e) => updateField('BMI', parseFloat(e.target.value) || 20)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-hr">Resting Heart Rate (bpm)</label>
                  <input 
                    id="input-hr"
                    type="number" 
                    min="40" 
                    max="180" 
                    value={formData.heartRate} 
                    onChange={(e) => updateField('heartRate', parseFloat(e.target.value) || 70)} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Vitals & Labs */}
          {currentStep === 2 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><Activity size={24} className="step-icon" /> Step 2: Blood Pressure &amp; Labs</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label htmlFor="input-sysbp">Systolic Blood Pressure (sysBP, mmHg)</label>
                  <input 
                    id="input-sysbp"
                    type="number" 
                    min="95" 
                    max="295" 
                    value={formData.sysBP} 
                    onChange={(e) => updateField('sysBP', parseFloat(e.target.value) || 120)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-diabp">Diastolic Blood Pressure (diaBP, mmHg)</label>
                  <input 
                    id="input-diabp"
                    type="number" 
                    min="50" 
                    max="160" 
                    value={formData.diaBP} 
                    onChange={(e) => updateField('diaBP', parseFloat(e.target.value) || 80)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-chol">Total Serum Cholesterol (totChol, mg/dL)</label>
                  <input 
                    id="input-chol"
                    type="number" 
                    min="100" 
                    max="600" 
                    value={formData.totChol} 
                    onChange={(e) => updateField('totChol', parseFloat(e.target.value) || 180)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-glucose">Fasting Blood Glucose (glucose, mg/dL)</label>
                  <input 
                    id="input-glucose"
                    type="number" 
                    min="40" 
                    max="400" 
                    value={formData.glucose} 
                    onChange={(e) => updateField('glucose', parseFloat(e.target.value) || 90)} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Medical & Lifestyle */}
          {currentStep === 3 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><HeartPulse size={24} className="step-icon" /> Step 3: Medical History &amp; Lifestyle</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label htmlFor="input-smoker">Smoking Status</label>
                  <select 
                    id="input-smoker"
                    value={formData.currentSmoker} 
                    onChange={(e) => updateField('currentSmoker', parseInt(e.target.value, 10))}
                  >
                    <option value={0}>Non-Smoker</option>
                    <option value={1}>Current Smoker</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="input-cigs">Cigarettes Smoked / Day</label>
                  <input 
                    id="input-cigs"
                    type="number" 
                    min="0" 
                    max="70" 
                    disabled={formData.currentSmoker === 0}
                    value={formData.cigsPerDay} 
                    onChange={(e) => updateField('cigsPerDay', parseFloat(e.target.value) || 0)} 
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="input-bpmeds">Blood Pressure Medication</label>
                  <select 
                    id="input-bpmeds"
                    value={formData.BPMeds} 
                    onChange={(e) => updateField('BPMeds', parseFloat(e.target.value))}
                  >
                    <option value={0}>No (Not taking BP meds)</option>
                    <option value={1}>Yes (Taking BP meds)</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="input-hyp">Prevalent Hypertension</label>
                  <select 
                    id="input-hyp"
                    value={formData.prevalentHyp} 
                    onChange={(e) => updateField('prevalentHyp', parseInt(e.target.value, 10))}
                  >
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="input-diabetes">Diagnosed Diabetes</label>
                  <select 
                    id="input-diabetes"
                    value={formData.diabetes} 
                    onChange={(e) => updateField('diabetes', parseInt(e.target.value, 10))}
                  >
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="input-stroke">History of Stroke</label>
                  <select 
                    id="input-stroke"
                    value={formData.prevalentStroke} 
                    onChange={(e) => updateField('prevalentStroke', parseInt(e.target.value, 10))}
                  >
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
              </div>
              
              <div className="info-box mt-2">
                <AlertCircle size={20} className="info-icon" />
                <p>HIPAA Safe Harbor Compliance: All patient inputs are evaluated in-memory with zero disk persistence.</p>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons (Separated from form-container to preserve layout) */}
        <div className="form-actions" style={{ marginTop: '2rem' }}>
          {currentStep > 1 && (
            <button 
              type="button" 
              className="btn-secondary" 
              onClick={handlePrev} 
              disabled={isLoading}
            >
              Previous Step
            </button>
          )}
          
          {currentStep < 3 ? (
            <button 
              type="button" 
              className="btn-primary" 
              onClick={handleNext}
            >
              Next Step <ChevronRight size={20} />
            </button>
          ) : (
            <button 
              type="button" 
              className="btn-gradient-cta" 
              onClick={handleAnalyze} 
              disabled={isLoading}
            >
              {isLoading ? 'Processing In Real-Time...' : 'Analyze Patient Risk'} 
              <ActivitySquare size={20} className="ml-2" />
            </button>
          )}
        </div>
      </main>
      
      {/* Decorative Background Elements */}
      <div className="bg-glow blue-glow-alt"></div>
      <div className="bg-glow purple-glow-alt"></div>
    </div>
  );
}
