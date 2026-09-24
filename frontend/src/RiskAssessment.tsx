import { useState } from 'react';
import './RiskAssessment.css';
import { ArrowLeft, User, Activity, HeartPulse, ChevronRight, ActivitySquare, AlertCircle } from 'lucide-react';

interface RiskAssessmentProps {
  onBack: () => void;
  onAnalyze: () => void;
}

const steps = [
  { id: 1, title: 'Health Profile' },
  { id: 2, title: 'Risk Assessment' },
  { id: 3, title: 'Your Insights' }
];

export default function RiskAssessment({ onBack, onAnalyze }: RiskAssessmentProps) {
  const [currentStep, setCurrentStep] = useState(1);

  const nextStep = () => {
    if (currentStep < 3) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  return (
    <div className="assessment-container">
      {/* Navigation Bar */}
      <nav className="assessment-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={20} /> Back to Home
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      {/* Main Content Area */}
      <main className="assessment-main">
        <div className="assessment-header">
          <h1 className="assessment-title">Let's Understand Your Risk</h1>
          <p className="assessment-subtitle">
            Enter your health details to receive an AI-powered cardiovascular risk assessment.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="progress-container">
          <div className="progress-labels">
            {steps.map((step) => (
              <div 
                key={step.id} 
                className={`progress-label ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}
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

        {/* Form Container */}
        <div className="form-container">
          {currentStep === 1 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><User size={24} className="step-icon" /> Personal Information</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label>Age</label>
                  <input type="number" placeholder="e.g. 45" />
                </div>
                <div className="input-group">
                  <label>Sex</label>
                  <select>
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><Activity size={24} className="step-icon" /> Health Measurements</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label>Blood Pressure (mmHg)</label>
                  <input type="text" placeholder="e.g. 120/80" />
                </div>
                <div className="input-group">
                  <label>Cholesterol (mg/dL)</label>
                  <input type="number" placeholder="e.g. 180" />
                </div>
                <div className="input-group">
                  <label>BMI (kg/m²)</label>
                  <input type="number" placeholder="e.g. 22.5" />
                </div>
                <div className="input-group">
                  <label>HbA1c / Blood Glucose</label>
                  <input type="number" placeholder="e.g. 5.5" />
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="form-step slide-in">
              <h2 className="step-title"><HeartPulse size={24} className="step-icon" /> Lifestyle & Medical Factors</h2>
              <div className="input-grid">
                <div className="input-group">
                  <label>Smoking Status</label>
                  <select>
                    <option value="">Select...</option>
                    <option value="never">Never Smoked</option>
                    <option value="former">Former Smoker</option>
                    <option value="current">Current Smoker</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Physical Activity</label>
                  <select>
                    <option value="">Select...</option>
                    <option value="low">Low (Rarely exercise)</option>
                    <option value="moderate">Moderate (1-3 times/week)</option>
                    <option value="high">High (4+ times/week)</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Diabetes</label>
                  <select>
                    <option value="">Select...</option>
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Other Comorbidities</label>
                  <select>
                    <option value="">Select...</option>
                    <option value="none">None</option>
                    <option value="hypertension">Hypertension</option>
                    <option value="kidney_disease">Kidney Disease</option>
                  </select>
                </div>
              </div>
              
              <div className="info-box mt-2">
                <AlertCircle size={20} className="info-icon" />
                <p>Your information is used to generate your personalized risk assessment.</p>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          {currentStep > 1 && (
            <button className="btn-secondary" onClick={prevStep}>
              Previous Step
            </button>
          )}
          
          {currentStep < 3 ? (
            <button className="btn-primary" onClick={nextStep}>
              Next Step <ChevronRight size={20} />
            </button>
          ) : (
            <button className="btn-gradient-cta" onClick={onAnalyze}>
              Analyze My Risk <ActivitySquare size={20} className="ml-2" />
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
