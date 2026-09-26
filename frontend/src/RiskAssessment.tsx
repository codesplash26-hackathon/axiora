import { useEffect, useState } from 'react';
import './RiskAssessment.css';
import { ArrowLeft, User, Activity, HeartPulse, ChevronRight, ActivitySquare, AlertCircle, Stethoscope, Lock, Scale, Calculator } from 'lucide-react';
import type { PatientInput } from './api';

interface RiskAssessmentProps {
  onBack: () => void;
  onAnalyze: (patient: PatientInput) => void;
  isLoading?: boolean;
  initialValues?: Partial<PatientInput>;
  lockedFields?: (keyof PatientInput)[];
  patientHeader?: {
    patientId: string;
    fullName?: string;
  };
}

const steps = [
  { id: 1, title: 'Personal Profile' },
  { id: 2, title: 'Vitals & Labs' },
  { id: 3, title: 'Medical & Lifestyle' }
];

export default function RiskAssessment({
  onBack,
  onAnalyze,
  isLoading,
  initialValues,
  lockedFields,
  patientHeader,
}: RiskAssessmentProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [bmiMode, setBmiMode] = useState<'direct' | 'calculate'>('calculate');
  const [heightCm, setHeightCm] = useState<string>('');
  const [weightKg, setWeightKg] = useState<string>('');

  const [formData, setFormData] = useState<PatientInput>(() => ({
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
    ...(initialValues || {}),
  }));

  useEffect(() => {
    if (initialValues) {
      setFormData((prev) => ({
        ...prev,
        ...initialValues,
      }));
    }
  }, [initialValues]);

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

  const calculateAndSetBmi = (hStr: string, wStr: string) => {
    const h = parseFloat(hStr);
    const w = parseFloat(wStr);
    if (h > 50 && h < 250 && w > 20 && w < 300) {
      const heightM = h / 100;
      const calculatedBmi = Number((w / (heightM * heightM)).toFixed(1));
      updateField('BMI', calculatedBmi);
    }
  };

  const handleHeightChange = (val: string) => {
    setHeightCm(val);
    calculateAndSetBmi(val, weightKg);
  };

  const handleWeightChange = (val: string) => {
    setWeightKg(val);
    calculateAndSetBmi(heightCm, val);
  };

  const getBmiCategory = (bmi: number | undefined | null) => {
    if (!bmi || isNaN(bmi) || bmi <= 0) return null;
    if (bmi < 18.5) {
      return {
        label: 'Underweight',
        categoryClass: 'underweight',
      };
    }
    if (bmi <= 24.9) {
      return {
        label: 'Normal Weight',
        categoryClass: 'normal',
      };
    }
    if (bmi <= 29.9) {
      return {
        label: 'Overweight',
        categoryClass: 'overweight',
      };
    }
    return {
      label: 'Obese',
      categoryClass: 'obese',
    };
  };

  const bmiCategory = getBmiCategory(formData.BMI);

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
          <ArrowLeft size={20} /> {patientHeader ? 'Back to Patient Roster' : 'Back to Home'}
        </button>
        <div className="nav-brand">CardioRecourse</div>
      </nav>

      {/* Main Content Area */}
      <main className="assessment-main">
        {patientHeader && (
          <div className="patient-assessment-badge" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            padding: '0.75rem 1.25rem',
            borderRadius: '0.75rem',
            marginBottom: '1.5rem',
          }}>
            <Stethoscope size={20} color="#0284c7" />
            <span style={{ color: '#0369a1', fontWeight: 600 }}>
              Assessing Patient: <strong>{patientHeader.fullName || 'Patient'}</strong> ({patientHeader.patientId})
            </span>
            <span style={{ fontSize: '0.8rem', color: '#0284c7', background: '#e0f2fe', padding: '0.2rem 0.6rem', borderRadius: '9999px', marginLeft: 'auto' }}>
              Demographics Locked
            </span>
          </div>
        )}

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
                  <div className="label-with-locked">
                    <label htmlFor="input-age">Age</label>
                    {lockedFields?.includes('age') && (
                      <span className="locked-registry-badge" title="Demographic locked to patient registry record">
                        <Lock size={11} /> Locked
                      </span>
                    )}
                  </div>
                  <span className="input-micro-hint">Adult screening baseline (18 – 120 yrs)</span>
                  <div className="input-with-suffix">
                    <input 
                      id="input-age"
                      type="number" 
                      min="18" 
                      max="120" 
                      value={formData.age} 
                      disabled={lockedFields?.includes('age')}
                      title={lockedFields?.includes('age') ? 'Demographic locked to patient registry record' : undefined}
                      style={lockedFields?.includes('age') ? { cursor: 'not-allowed', color: '#64748b' } : undefined}
                      onChange={(e) => updateField('age', parseFloat(e.target.value) || 18)} 
                    />
                    <span className="input-suffix">yrs</span>
                  </div>
                </div>

                <div className="input-group">
                  <div className="label-with-locked">
                    <label htmlFor="input-sex">Biological Sex</label>
                    {lockedFields?.includes('male') && (
                      <span className="locked-registry-badge" title="Demographic locked to patient registry record">
                        <Lock size={11} /> Locked
                      </span>
                    )}
                  </div>
                  <span className="input-micro-hint">Baseline demographic profile</span>
                  <select 
                    id="input-sex"
                    value={formData.male} 
                    disabled={lockedFields?.includes('male')}
                    title={lockedFields?.includes('male') ? 'Demographic locked to patient registry record' : undefined}
                    style={lockedFields?.includes('male') ? { cursor: 'not-allowed', color: '#64748b' } : undefined}
                    onChange={(e) => updateField('male', parseInt(e.target.value, 10))}
                  >
                    <option value={1}>Male</option>
                    <option value={0}>Female</option>
                  </select>
                </div>

                {/* Condensed Single-Card BMI Calculator Widget */}
                <div className="bmi-streamlined-widget">
                  <div className="bmi-widget-header">
                    <div className="bmi-widget-title-area">
                      <div className="bmi-widget-heading">
                        <Scale size={15} className="bmi-widget-icon" />
                        <span>Body Mass Index (BMI)</span>
                      </div>
                      <span className="input-micro-hint">Auto-calculate from height &amp; weight or enter directly</span>
                    </div>

                    {/* Mode Tabs / Pill Selector */}
                    <div className="bmi-mode-pills" role="tablist" aria-label="BMI Entry Mode">
                      <button
                        type="button"
                        role="tab"
                        id="tab-bmi-calc"
                        aria-selected={bmiMode === 'calculate'}
                        className={`bmi-mode-pill ${bmiMode === 'calculate' ? 'active' : ''}`}
                        onClick={() => setBmiMode('calculate')}
                      >
                        <Calculator size={13} />
                        <span>Calculate</span>
                      </button>
                      <button
                        type="button"
                        role="tab"
                        id="tab-bmi-direct"
                        aria-selected={bmiMode === 'direct'}
                        className={`bmi-mode-pill ${bmiMode === 'direct' ? 'active' : ''}`}
                        onClick={() => setBmiMode('direct')}
                      >
                        <span>Direct Input</span>
                      </button>
                    </div>
                  </div>

                  {bmiMode === 'calculate' ? (
                    <div className="bmi-widget-body">
                      <div className="bmi-calc-pair">
                        <div className="input-group">
                          <label htmlFor="input-height">
                            <span>Height</span>
                            <span className="input-micro-hint">Standing stature (50 – 250 cm)</span>
                          </label>
                          <div className="input-with-suffix">
                            <input
                              id="input-height"
                              type="number"
                              min="50"
                              max="250"
                              placeholder="e.g. 170"
                              value={heightCm}
                              onChange={(e) => handleHeightChange(e.target.value)}
                            />
                            <span className="input-suffix">cm</span>
                          </div>
                        </div>

                        <div className="input-group">
                          <label htmlFor="input-weight">
                            <span>Weight / Mass</span>
                            <span className="input-micro-hint">Measured body mass (20 – 250 kg)</span>
                          </label>
                          <div className="input-with-suffix">
                            <input
                              id="input-weight"
                              type="number"
                              min="20"
                              max="250"
                              placeholder="e.g. 68"
                              value={weightKg}
                              onChange={(e) => handleWeightChange(e.target.value)}
                            />
                            <span className="input-suffix">kg</span>
                          </div>
                        </div>
                      </div>

                      {/* Streamlined Inline Result Badge */}
                      <div className="bmi-inline-badge-bar">
                        <div className="bmi-badge-left">
                          <span className="bmi-badge-caption">Calculated BMI:</span>
                          <span className="bmi-badge-figure">
                            {formData.BMI ? `${formData.BMI.toFixed(1)} kg/m²` : '-- kg/m²'}
                          </span>
                          {bmiCategory && (
                            <>
                              <span className="bmi-badge-sep">•</span>
                              <span className={`bmi-status-chip ${bmiCategory.categoryClass}`}>
                                <span className="chip-bullet" />
                                <span>{bmiCategory.label}</span>
                              </span>
                            </>
                          )}
                        </div>
                        <span className="bmi-sync-note">Synced with risk model</span>
                      </div>
                    </div>
                  ) : (
                    <div className="bmi-widget-body">
                      <div className="bmi-direct-pair">
                        <div className="input-group" style={{ flex: 1 }}>
                          <label htmlFor="input-bmi">
                            <span>Direct Body Mass Index (BMI)</span>
                            <span className="input-micro-hint">Valid clinical range: 15.0 – 55.0 kg/m²</span>
                          </label>
                          <div className="input-with-suffix">
                            <input
                              id="input-bmi"
                              type="number"
                              step="0.1"
                              min="15"
                              max="55"
                              placeholder="e.g. 24.0"
                              value={formData.BMI || ''}
                              onChange={(e) => updateField('BMI', parseFloat(e.target.value) || 20)}
                            />
                            <span className="input-suffix">kg/m²</span>
                          </div>
                        </div>
                        {bmiCategory && (
                          <div className="bmi-direct-chip-wrap">
                            <span className={`bmi-status-chip ${bmiCategory.categoryClass}`}>
                              <span className="chip-bullet" />
                              <span>{bmiCategory.label}</span>
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="input-group">
                  <label htmlFor="input-hr">
                    <span>Resting Heart Rate</span>
                    <span className="input-micro-hint">Normal resting: 60 – 100 bpm</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-hr"
                      type="number" 
                      min="40" 
                      max="180" 
                      value={formData.heartRate} 
                      onChange={(e) => updateField('heartRate', parseFloat(e.target.value) || 70)} 
                    />
                    <span className="input-suffix">bpm</span>
                  </div>
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
                  <label htmlFor="input-sysbp">
                    <span>Systolic Blood Pressure (sysBP)</span>
                    <span className="input-micro-hint">Normal: 90 – 120 mmHg (Elevated: ≥130)</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-sysbp"
                      type="number" 
                      min="70" 
                      max="295" 
                      value={formData.sysBP} 
                      onChange={(e) => updateField('sysBP', parseFloat(e.target.value) || 120)} 
                    />
                    <span className="input-suffix">mmHg</span>
                  </div>
                </div>

                <div className="input-group">
                  <label htmlFor="input-diabp">
                    <span>Diastolic Blood Pressure (diaBP)</span>
                    <span className="input-micro-hint">Normal: 60 – 80 mmHg (Stage 1: ≥80)</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-diabp"
                      type="number" 
                      min="40" 
                      max="160" 
                      value={formData.diaBP} 
                      onChange={(e) => updateField('diaBP', parseFloat(e.target.value) || 80)} 
                    />
                    <span className="input-suffix">mmHg</span>
                  </div>
                </div>

                <div className="input-group">
                  <label htmlFor="input-chol">
                    <span>Total Serum Cholesterol (totChol)</span>
                    <span className="input-micro-hint">Desirable: &lt; 200 mg/dL (Borderline: 200 – 239)</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-chol"
                      type="number" 
                      min="100" 
                      max="600" 
                      value={formData.totChol} 
                      onChange={(e) => updateField('totChol', parseFloat(e.target.value) || 180)} 
                    />
                    <span className="input-suffix">mg/dL</span>
                  </div>
                </div>

                <div className="input-group">
                  <label htmlFor="input-glucose">
                    <span>Fasting Blood Glucose (glucose)</span>
                    <span className="input-micro-hint">Normal fasting: 70 – 99 mg/dL (Impaired: 100 – 125)</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-glucose"
                      type="number" 
                      min="40" 
                      max="400" 
                      value={formData.glucose} 
                      onChange={(e) => updateField('glucose', parseFloat(e.target.value) || 90)} 
                    />
                    <span className="input-suffix">mg/dL</span>
                  </div>
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
                  <label htmlFor="input-cigs">
                    <span>Cigarettes Smoked / Day</span>
                    <span className="input-micro-hint">Average daily quantity</span>
                  </label>
                  <div className="input-with-suffix">
                    <input 
                      id="input-cigs"
                      type="number" 
                      min="0" 
                      max="70" 
                      disabled={formData.currentSmoker === 0}
                      value={formData.cigsPerDay} 
                      onChange={(e) => updateField('cigsPerDay', parseFloat(e.target.value) || 0)} 
                    />
                    <span className="input-suffix">cigs/day</span>
                  </div>
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
