import React, { useEffect, useState } from 'react';
import './DoctorDashboard.css';
import {
  Heart,
  Users,
  Activity,
  Target,
  ShieldCheck,
  Search,
  Plus,
  RefreshCw,
  Clock,
  AlertTriangle,
  X,
  UserPlus,
  Home,
  Pencil,
  LogOut,
} from 'lucide-react';
import {
  getDoctorOverview,
  listPatients,
  createPatient,
  updatePatient,
  getPatientHistory,
  assessDoctorPatient,
} from './api';
import type {
  DoctorUser,
  DoctorOverview,
  PatientRecord,
  PatientHistory,
  AssessmentResponse,
} from './api';

interface DoctorDashboardPageProps {
  doctor: DoctorUser;
  token: string;
  onLogout: () => void;
  onGoHome?: () => void;
  onNewAssessment: () => void;
  onViewAssessmentResult?: (assessment: AssessmentResponse) => void;
  onAssessPatient?: (patient: PatientRecord) => void;
}

export default function DoctorDashboardPage({
  doctor,
  token,
  onLogout,
  onGoHome,
  onNewAssessment,
  onViewAssessmentResult,
  onAssessPatient,
}: DoctorDashboardPageProps) {
  const [overview, setOverview] = useState<DoctorOverview | null>(null);
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Registration Modal State
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [newPtName, setNewPtName] = useState('');
  const [newPtAge, setNewPtAge] = useState(55);
  const [newPtSex, setNewPtSex] = useState('Female');
  const [newPtPhone, setNewPtPhone] = useState('');
  const [enterVitalsNow, setEnterVitalsNow] = useState(false);
  const [initialBiomarkers, setInitialBiomarkers] = useState({
    sysBP: 130,
    diaBP: 85,
    totChol: 210,
    glucose: 90,
    BMI: 26.0,
    heartRate: 72,
    currentSmoker: 0,
    cigsPerDay: 0,
    BPMeds: 0,
    diabetes: 0,
    prevalentHyp: 0,
    prevalentStroke: 0,
  });
  const [isSubmittingPt, setIsSubmittingPt] = useState(false);

  // History Drawer State
  const [selectedHistory, setSelectedHistory] = useState<PatientHistory | null>(null);
  const [historyPatientName, setHistoryPatientName] = useState('');

  // Edit Patient State
  const [editingPatient, setEditingPatient] = useState<PatientRecord | null>(null);
  const [editFullName, setEditFullName] = useState('');
  const [editAge, setEditAge] = useState(55);
  const [editSex, setEditSex] = useState('Female');
  const [editPhone, setEditPhone] = useState('');
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [editErrorMessage, setEditErrorMessage] = useState<string | null>(null);

  const handleOpenEdit = (pt: PatientRecord) => {
    setEditingPatient(pt);
    setEditFullName(pt.fullName || '');
    setEditAge(pt.age || 50);
    setEditSex(pt.sex || 'Female');
    setEditPhone(pt.contactPhone || '');
    setEditErrorMessage(null);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPatient) return;
    if (!editFullName.trim()) {
      setEditErrorMessage('Patient full name is required.');
      return;
    }

    setIsSavingEdit(true);
    setEditErrorMessage(null);
    try {
      await updatePatient(token, editingPatient.patientId, {
        fullName: editFullName.trim(),
        age: Number(editAge),
        sex: editSex,
        contactPhone: editPhone.trim(),
      });
      setEditingPatient(null);
      await loadDashboardData();
    } catch (err: unknown) {
      setEditErrorMessage(err instanceof Error ? err.message : 'Failed to update patient demographics.');
    } finally {
      setIsSavingEdit(false);
    }
  };

  // Fetch live overview and patients list
  const loadDashboardData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [overviewData, patientsData] = await Promise.all([
        getDoctorOverview(token),
        listPatients(token, searchTerm.trim(), riskFilter),
      ]);
      setOverview(overviewData);
      setPatients(patientsData);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to synchronize with clinical backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [riskFilter]);

  // Debounced search
  useEffect(() => {
    const handler = setTimeout(() => {
      listPatients(token, searchTerm.trim(), riskFilter)
        .then(setPatients)
        .catch(() => {});
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const updateInitialBiomarker = <K extends keyof typeof initialBiomarkers>(
    key: K,
    val: typeof initialBiomarkers[K]
  ) => {
    setInitialBiomarkers((prev) => {
      const updated = { ...prev, [key]: val };
      if (key === 'currentSmoker') {
        if (val === 0) updated.cigsPerDay = 0;
        else if (val === 1 && prev.cigsPerDay === 0) updated.cigsPerDay = 10;
      } else if (key === 'cigsPerDay') {
        const cigs = Number(val);
        if (cigs <= 0) {
          updated.currentSmoker = 0;
          updated.cigsPerDay = 0;
        } else {
          updated.currentSmoker = 1;
          updated.cigsPerDay = cigs;
        }
      }
      return updated;
    });
  };

  const resetRegistrationForm = () => {
    setNewPtName('');
    setNewPtAge(55);
    setNewPtSex('Female');
    setNewPtPhone('');
    setEnterVitalsNow(false);
    setInitialBiomarkers({
      sysBP: 130,
      diaBP: 85,
      totChol: 210,
      glucose: 90,
      BMI: 26.0,
      heartRate: 72,
      currentSmoker: 0,
      cigsPerDay: 0,
      BPMeds: 0,
      diabetes: 0,
      prevalentHyp: 0,
      prevalentStroke: 0,
    });
  };

  const handleRegisterPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPtName.trim()) return;

    setIsSubmittingPt(true);
    try {
      if (!enterVitalsNow) {
        // Register without initial assessment: no fake or random risk scores injected
        await createPatient(token, {
          fullName: newPtName.trim(),
          age: Number(newPtAge),
          sex: newPtSex,
          contactPhone: newPtPhone.trim(),
          baselineBiomarkers: {},
        });
        setIsRegisterOpen(false);
        resetRegistrationForm();
        await loadDashboardData();
      } else {
        // Register and immediately compute real ML inference
        const fullBiomarkers = {
          male: newPtSex === 'Male' ? 1 : 0,
          age: Number(newPtAge),
          ...initialBiomarkers,
        };
        const created = await createPatient(token, {
          fullName: newPtName.trim(),
          age: Number(newPtAge),
          sex: newPtSex,
          contactPhone: newPtPhone.trim(),
          baselineBiomarkers: fullBiomarkers,
        });
        const assessRes = await assessDoctorPatient(token, created.patientId, fullBiomarkers);
        setIsRegisterOpen(false);
        resetRegistrationForm();
        if (onViewAssessmentResult) {
          onViewAssessmentResult(assessRes);
        } else {
          await loadDashboardData();
        }
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsSubmittingPt(false);
    }
  };

  const handleOpenHistory = async (pt: PatientRecord) => {
    setHistoryPatientName(pt.fullName || pt.patientId);
    try {
      const hist = await getPatientHistory(token, pt.patientId);
      setSelectedHistory(hist);
    } catch {
      alert('Unable to load clinical timeline for this patient.');
    }
  };

  const handleRunAssessment = async (pt: PatientRecord) => {
    setIsLoading(true);
    try {
      const res = await assessDoctorPatient(token, pt.patientId);
      if (onViewAssessmentResult) {
        onViewAssessmentResult(res);
      } else {
        alert(`Assessment completed for ${pt.fullName}! Risk: ${res.prediction.risk_percentage.toFixed(1)}% (${res.prediction.risk_band})`);
        await loadDashboardData();
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Assessment failed');
    } finally {
      setIsLoading(false);
    }
  };

  const doctorInitials = (doctor.fullName || doctor.email || 'DR')
    .replace(/^Dr\.\s*/i, '')
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'DR';

  return (
    <div className="doctor-dashboard-container">
      {/* Sleek Executive Clinical Header */}
      <header className="doctor-navbar">
        {/* Left: Brand Identity */}
        <div
          onClick={onGoHome}
          className="doctor-nav-brand"
          title={onGoHome ? "Return to Home / Overview" : undefined}
          role={onGoHome ? "button" : undefined}
          tabIndex={onGoHome ? 0 : undefined}
          onKeyDown={(e) => {
            if (onGoHome && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              onGoHome();
            }
          }}
        >
          <div className="brand-icon-squircle">
            <Heart size={20} color="#ffffff" fill="rgba(255, 255, 255, 0.25)" />
          </div>
          <div className="brand-text-group">
            <span className="brand-title">
              Cardio<span className="accent">Recourse</span>
            </span>
            <span className="brand-portal-badge">
              Clinical Decision Portal
            </span>
          </div>
        </div>

        {/* Right: Actions, Doctor Avatar Chip & Sign Out */}
        <div className="doctor-nav-actions">
          {onGoHome && (
            <button
              className="btn-doctor-overview"
              onClick={onGoHome}
              title="Return to Home / Overview without signing out"
            >
              <Home size={15} color="#64748b" />
              <span>Overview</span>
            </button>
          )}

          {/* Doctor Profile Chip */}
          <div className="doctor-profile-chip" title={doctor.specialization || "Clinical Staff"}>
            <div className="doctor-avatar-circle">
              {doctorInitials}
            </div>
            <div className="doctor-meta">
              <span className="doctor-meta-name">
                {doctor.fullName || `Dr. ${doctor.email}`}
              </span>
              <span className="doctor-meta-hospital">
                {doctor.hospital || 'Hospital Staff'}
              </span>
            </div>
          </div>

          {/* Sign Out */}
          <button
            className="btn-doctor-signout"
            onClick={onLogout}
            title="Sign Out of Clinical Session"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="dashboard-content">
        <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>Clinical Overview &amp; Patient Registry</h1>
            <p>
              Real-time cardiovascular risk surveillance, SHAP diagnostic attributions, and DiCE counterfactuals.
            </p>
          </div>
          <button 
            className="btn-action" 
            onClick={loadDashboardData}
            disabled={isLoading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> Refresh Data
          </button>
        </div>

        {errorMessage && (
          <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Overview Stats Cards */}
        <div className="overview-grid">
          <div className="stat-card">
            <div className="stat-info">
              <h3>Total Registered Patients</h3>
              <div className="stat-value">{overview ? overview.totalPatients : '...'}</div>
              <div className="stat-trend positive">Active clinical cohort</div>
            </div>
            <div className="stat-icon blue">
              <Users size={24} />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-info">
              <h3>High Risk (≥20%)</h3>
              <div className="stat-value" style={{ color: '#ef4444' }}>
                {overview ? overview.highRiskCount : '...'}
              </div>
              <div className="stat-trend negative">Requires immediate GDMT</div>
            </div>
            <div className="stat-icon red">
              <Activity size={24} />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-info">
              <h3>Borderline (10–19.9%)</h3>
              <div className="stat-value" style={{ color: '#f59e0b' }}>
                {overview ? overview.borderlineCount : '...'}
              </div>
              <div className="stat-trend positive">Target for lifestyle recourse</div>
            </div>
            <div className="stat-icon green">
              <ShieldCheck size={24} />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-info">
              <h3>Low Risk (&lt;10%)</h3>
              <div className="stat-value" style={{ color: '#10b981' }}>
                {overview ? overview.lowRiskCount : '...'}
              </div>
              <div className="stat-trend positive">Wellness &amp; preventative care</div>
            </div>
            <div className="stat-icon purple">
              <Target size={24} />
            </div>
          </div>
        </div>

        {/* Patient Registry Table */}
        <div className="patient-table-container">
          <div className="table-header">
            <h2>Patient Cohort Surveillance</h2>
            <div className="table-actions">
              <div className="search-box">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  placeholder="Search name or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <select
                className="filter-select"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
              >
                <option value="All">All Risk Bands</option>
                <option value="High">High Risk (≥20%)</option>
                <option value="Borderline">Borderline (10-19.9%)</option>
                <option value="Low">Low Risk (&lt;10%)</option>
              </select>

              <button className="btn-action" onClick={() => setIsRegisterOpen(true)}>
                <UserPlus size={16} style={{ verticalAlign: 'middle', marginRight: '0.35rem' }} /> Register Patient
              </button>

              <button className="btn-action primary" onClick={onNewAssessment}>
                <Plus size={16} style={{ verticalAlign: 'middle', marginRight: '0.25rem' }} /> Public Assessment Run
              </button>
            </div>
          </div>

          <table className="patient-table">
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Full Name</th>
                <th>Age / Sex</th>
                <th>Contact</th>
                <th>Latest 10-Yr Risk</th>
                <th>Status / Band</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-state">
                    {isLoading ? 'Loading patient registry from Firestore...' : 'No patient records found in your clinical cohort.'}
                  </td>
                </tr>
              ) : (
                patients.map((pt) => {
                  const isAssessed =
                    Boolean(pt.latestRiskBand) &&
                    pt.latestRiskBand !== 'Not Assessed' &&
                    pt.latestRiskBand !== 'Pending' &&
                    pt.latestRiskScore !== null &&
                    pt.latestRiskScore !== undefined;

                  const scorePct =
                    pt.latestRiskPercentage ??
                    (pt.latestRiskScore !== null && pt.latestRiskScore !== undefined
                      ? pt.latestRiskScore * 100
                      : null);

                  const isHigh = isAssessed && (pt.latestRiskBand === 'High' || (scorePct !== null && scorePct >= 20));
                  const isBorderline =
                    isAssessed &&
                    (pt.latestRiskBand === 'Borderline' ||
                      (scorePct !== null && scorePct >= 10 && scorePct < 20));

                  return (
                    <tr key={pt.patientId}>
                      <td style={{ fontWeight: 600, color: '#0ea5e9' }}>{pt.patientId}</td>
                      <td style={{ fontWeight: 600, color: '#0f172a' }}>{pt.fullName}</td>
                      <td>{pt.age} / {pt.sex}</td>
                      <td>{pt.contactPhone || '—'}</td>
                      <td>
                        <span style={{ fontWeight: 700, color: isAssessed ? (isHigh ? '#dc2626' : isBorderline ? '#d97706' : '#059669') : '#94a3b8' }}>
                          {isAssessed && scorePct !== null ? `${scorePct.toFixed(1)}%` : '—'}
                        </span>
                      </td>
                      <td>
                        <span className={`risk-badge ${isAssessed ? (isHigh ? 'high' : isBorderline ? 'borderline' : 'low') : 'neutral'}`}>
                          {isAssessed ? pt.latestRiskBand : 'Not Assessed'}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                          <button
                            className="btn-action primary"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                            onClick={() => {
                              if (onAssessPatient) {
                                onAssessPatient(pt);
                              } else {
                                handleRunAssessment(pt);
                              }
                            }}
                            title="Open 14-Factor Clinical Assessment Wizard"
                          >
                            Assess
                          </button>
                          <button
                            className="btn-action"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                            onClick={() => handleOpenEdit(pt)}
                            title="Edit Patient Demographics"
                          >
                            <Pencil size={13} style={{ verticalAlign: 'middle', marginRight: '0.2rem' }} /> Edit
                          </button>
                          <button
                            className="btn-action"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                            onClick={() => handleOpenHistory(pt)}
                            title="View Previous Assessments & Action Plans"
                          >
                            <Clock size={13} style={{ verticalAlign: 'middle', marginRight: '0.2rem' }} /> History
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Register New Patient */}
      {isRegisterOpen && (
        <div className="modal-overlay fade-in">
          <div className="modal-card fade-up">
            <div className="modal-header">
              <h2>Register New Patient</h2>
              <button className="modal-close-btn" onClick={() => setIsRegisterOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRegisterPatient}>
              <div className="modal-form-grid">
                <div className="form-group-full">
                  <label className="form-input-label">Patient Full Name</label>
                  <input
                    type="text"
                    className="form-input-control"
                    placeholder="e.g. Anura Perera"
                    value={newPtName}
                    onChange={(e) => setNewPtName(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="form-input-label">Chronological Age</label>
                  <input
                    type="number"
                    className="form-input-control"
                    min={18}
                    max={120}
                    value={newPtAge}
                    onChange={(e) => setNewPtAge(Number(e.target.value))}
                    required
                  />
                </div>

                <div>
                  <label className="form-input-label">Biological Sex</label>
                  <select
                    className="form-input-control"
                    value={newPtSex}
                    onChange={(e) => setNewPtSex(e.target.value)}
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                  </select>
                </div>

                <div className="form-group-full">
                  <label className="form-input-label">Contact Phone (Optional)</label>
                  <input
                    type="tel"
                    className="form-input-control"
                    placeholder="+94 77 123 4567"
                    value={newPtPhone}
                    onChange={(e) => setNewPtPhone(e.target.value)}
                  />
                </div>
                <div className="form-group-full" style={{ marginTop: '0.5rem', padding: '0.75rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontWeight: 600, color: '#0369a1', margin: 0 }}>
                    <input
                      type="checkbox"
                      checked={enterVitalsNow}
                      onChange={(e) => setEnterVitalsNow(e.target.checked)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span>Enter Initial Vitals &amp; Labs Now (12 Clinical Biomarkers)</span>
                  </label>
                  <p style={{ margin: '0.25rem 0 0 1.75rem', fontSize: '0.8rem', color: '#64748b' }}>
                    {enterVitalsNow
                      ? 'Biomarkers will run through XGBoost & SHAP immediately upon registration.'
                      : "Patient will be saved as 'Not Assessed' so vitals can be captured later via the Assess button."}
                  </p>

                  {enterVitalsNow && (
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Systolic BP (mmHg)</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={80}
                          max={260}
                          value={initialBiomarkers.sysBP}
                          onChange={(e) => updateInitialBiomarker('sysBP', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Diastolic BP (mmHg)</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={40}
                          max={150}
                          value={initialBiomarkers.diaBP}
                          onChange={(e) => updateInitialBiomarker('diaBP', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Total Cholesterol (mg/dL)</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={100}
                          max={600}
                          value={initialBiomarkers.totChol}
                          onChange={(e) => updateInitialBiomarker('totChol', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Fasting Glucose (mg/dL)</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={40}
                          max={400}
                          value={initialBiomarkers.glucose}
                          onChange={(e) => updateInitialBiomarker('glucose', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Body Mass Index (BMI)</label>
                        <input
                          type="number"
                          step="0.1"
                          className="form-input-control"
                          min={15}
                          max={55}
                          value={initialBiomarkers.BMI}
                          onChange={(e) => updateInitialBiomarker('BMI', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Resting Heart Rate (bpm)</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={40}
                          max={200}
                          value={initialBiomarkers.heartRate}
                          onChange={(e) => updateInitialBiomarker('heartRate', Number(e.target.value))}
                          required
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Current Smoker</label>
                        <select
                          className="form-input-control"
                          value={initialBiomarkers.currentSmoker}
                          onChange={(e) => updateInitialBiomarker('currentSmoker', Number(e.target.value))}
                        >
                          <option value={0}>Non-Smoker</option>
                          <option value={1}>Active Smoker</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Cigarettes / Day</label>
                        <input
                          type="number"
                          className="form-input-control"
                          min={0}
                          max={70}
                          disabled={initialBiomarkers.currentSmoker === 0}
                          value={initialBiomarkers.cigsPerDay}
                          onChange={(e) => updateInitialBiomarker('cigsPerDay', Number(e.target.value))}
                        />
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>BP Medication</label>
                        <select
                          className="form-input-control"
                          value={initialBiomarkers.BPMeds}
                          onChange={(e) => updateInitialBiomarker('BPMeds', Number(e.target.value))}
                        >
                          <option value={0}>No</option>
                          <option value={1}>Yes (Active)</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Diabetes Status</label>
                        <select
                          className="form-input-control"
                          value={initialBiomarkers.diabetes}
                          onChange={(e) => updateInitialBiomarker('diabetes', Number(e.target.value))}
                        >
                          <option value={0}>Non-Diabetic</option>
                          <option value={1}>Diabetic</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>Prevalent Hypertension</label>
                        <select
                          className="form-input-control"
                          value={initialBiomarkers.prevalentHyp}
                          onChange={(e) => updateInitialBiomarker('prevalentHyp', Number(e.target.value))}
                        >
                          <option value={0}>No</option>
                          <option value={1}>Yes</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-input-label" style={{ fontSize: '0.8rem' }}>History of Stroke</label>
                        <select
                          className="form-input-control"
                          value={initialBiomarkers.prevalentStroke}
                          onChange={(e) => updateInitialBiomarker('prevalentStroke', Number(e.target.value))}
                        >
                          <option value={0}>No</option>
                          <option value={1}>Yes</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => {
                    setIsRegisterOpen(false);
                    resetRegistrationForm();
                  }}
                  disabled={isSubmittingPt}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-action primary"
                  disabled={isSubmittingPt}
                >
                  {isSubmittingPt ? 'Registering...' : enterVitalsNow ? 'Register & Assess Now' : 'Save & Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Patient Clinical Timeline & History */}
      {selectedHistory && (
        <div className="modal-overlay fade-in">
          <div className="modal-card fade-up">
            <div className="modal-header">
              <div>
                <h2>Clinical Timeline: {historyPatientName}</h2>
                <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                  Patient ID: {selectedHistory.patientId}
                </span>
              </div>
              <button className="modal-close-btn" onClick={() => setSelectedHistory(null)}>
                <X size={20} />
              </button>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <h3 style={{ fontSize: '1rem', color: '#0f172a', marginBottom: '0.75rem' }}>
                Assessment Timeline ({selectedHistory.assessments.length})
              </h3>
              {selectedHistory.assessments.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No previous assessments recorded.</p>
              ) : (
                selectedHistory.assessments.map((a) => (
                  <div key={a.assessmentId} className="timeline-entry">
                    <div className="timeline-date">
                      {new Date(a.assessedAt).toLocaleDateString()} {new Date(a.assessedAt).toLocaleTimeString()}
                    </div>
                    <div className="timeline-title">
                      10-Year Risk: <strong>{a.riskPercentage.toFixed(1)}%</strong> ({a.riskBand})
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#475569' }}>
                      Latency: {a.pipelineLatencyMs}ms | Systolic BP: {a.inputBiomarkers.sysBP} mmHg | Cholesterol: {a.inputBiomarkers.totChol} mg/dL
                    </div>
                  </div>
                ))
              )}

              <h3 style={{ fontSize: '1rem', color: '#0f172a', marginTop: '1.5rem', marginBottom: '0.75rem' }}>
                Confirmed Action Plans ({selectedHistory.actionPlans.length})
              </h3>
              {selectedHistory.actionPlans.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No action plans confirmed yet.</p>
              ) : (
                selectedHistory.actionPlans.map((p) => (
                  <div key={p.planId} className="timeline-entry" style={{ borderColor: '#10b981' }}>
                    <div className="timeline-date">
                      {new Date(p.createdAt).toLocaleDateString()}
                    </div>
                    <div className="timeline-title" style={{ color: '#047857' }}>
                      {p.selectedPathwayTitle} (Projected: {p.projectedRiskPercentage.toFixed(1)}%, Reduction: -{p.absoluteRiskReduction.toFixed(1)}%)
                    </div>
                    {p.clinicianNotes && (
                      <p style={{ fontSize: '0.85rem', background: '#f8fafc', padding: '0.5rem', borderRadius: '0.375rem', marginTop: '0.35rem' }}>
                        <strong>Doctor Notes:</strong> {p.clinicianNotes}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="modal-actions">
              <button className="btn-action primary" onClick={() => setSelectedHistory(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Edit Patient Demographics */}
      {editingPatient && (
        <div className="modal-overlay fade-in">
          <div className="modal-card fade-up">
            <div className="modal-header">
              <div>
                <h2>Edit Patient Demographics</h2>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                  ID: <strong style={{ color: '#0ea5e9' }}>{editingPatient.patientId}</strong>
                </p>
              </div>
              <button className="modal-close-btn" onClick={() => setEditingPatient(null)}>
                <X size={20} />
              </button>
            </div>

            {editErrorMessage && (
              <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                <AlertTriangle size={16} />
                <span>{editErrorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSaveEdit}>
              <div className="modal-form-grid">
                <div className="form-group-full">
                  <label className="form-input-label">Patient Full Name</label>
                  <input
                    type="text"
                    className="form-input-control"
                    placeholder="e.g. Anura Perera"
                    value={editFullName}
                    onChange={(e) => setEditFullName(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="form-input-label">Chronological Age</label>
                  <input
                    type="number"
                    className="form-input-control"
                    min={18}
                    max={120}
                    value={editAge}
                    onChange={(e) => setEditAge(Number(e.target.value))}
                    required
                  />
                </div>

                <div>
                  <label className="form-input-label">Biological Sex</label>
                  <select
                    className="form-input-control"
                    value={editSex}
                    onChange={(e) => setEditSex(e.target.value)}
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                  </select>
                </div>

                <div className="form-group-full">
                  <label className="form-input-label">Contact Phone</label>
                  <input
                    type="tel"
                    className="form-input-control"
                    placeholder="+94 77 123 4567"
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                  />
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => setEditingPatient(null)}
                  disabled={isSavingEdit}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-action primary"
                  disabled={isSavingEdit}
                >
                  {isSavingEdit ? 'Saving...' : 'Save Demographics'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
