import React, { useState, useEffect } from 'react';
import { X, Stethoscope, Mail, Lock, ArrowRight, Zap, Building2, AlertCircle, Loader2 } from 'lucide-react';
import './DoctorLoginModal.css';
import { loginDoctor, registerDoctor } from './api';
import type { DoctorUser } from './api';

interface DoctorLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (doctor: DoctorUser, token: string) => void;
}

export default function DoctorLoginModal({ isOpen, onClose, onLogin }: DoctorLoginModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [specialization, setSpecialization] = useState('Cardiology');
  const [hospital, setHospital] = useState('Axiora Health Network');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      if (mode === 'login') {
        const res = await loginDoctor(email.trim(), password);
        onLogin(res.doctor, res.access_token);
        onClose();
      } else {
        if (!fullName.trim()) {
          throw new Error('Please enter your full clinical name and title.');
        }
        const res = await registerDoctor({
          email: email.trim(),
          password,
          fullName: fullName.trim(),
          specialization: specialization.trim() || 'Cardiology',
          hospital: hospital.trim() || 'Axiora Health Network'
        });
        onLogin(res.doctor, res.access_token);
        onClose();
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    const demoEmail = 'dr.smith@cardiorecourse.lk';
    const demoPw = 'DoctorPass123!';

    try {
      try {
        const res = await loginDoctor(demoEmail, demoPw);
        onLogin(res.doctor, res.access_token);
        onClose();
        return;
      } catch {
        // Auto-register demo account if first time running on fresh Firestore instance
        const res = await registerDoctor({
          email: demoEmail,
          password: demoPw,
          fullName: 'Dr. Jane Smith',
          specialization: 'Interventional Cardiology',
          hospital: 'Axiora Heart Institute'
        });
        onLogin(res.doctor, res.access_token);
        onClose();
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Demo login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="auth-overlay fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isLoading) {
          onClose();
        }
      }}
    >
      <div
        className="auth-modal fade-up"
        style={{
          maxHeight: '90vh',
          overflowY: 'auto',
          paddingBottom: '2rem',
        }}
      >
        <button className="auth-close" onClick={onClose} disabled={isLoading} title="Close dialog">
          <X size={24} />
        </button>

        <div className="auth-header">
          <div className="auth-icon-wrapper">
            <Stethoscope size={32} color="#0284c7" />
          </div>
          <h2 className="auth-title shiny-heading-text">Doctor Portal</h2>
          <p className="auth-subtitle">Secure clinical access for verified healthcare providers</p>
        </div>

        {/* Tab Toggle: Sign In vs Register */}
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setErrorMessage(null); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setErrorMessage(null); }}
          >
            Create Account
          </button>
        </div>

        {errorMessage && (
          <div className="auth-error-msg">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <>
              <div className="input-group">
                <label>Doctor Full Name &amp; Title</label>
                <div className="input-wrapper">
                  <Stethoscope size={18} className="input-icon" />
                  <input 
                    type="text" 
                    placeholder="e.g. Dr. Jane Smith, MD" 
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required 
                  />
                </div>
              </div>

              <div className="input-group">
                <label>Specialization</label>
                <div className="input-wrapper">
                  <Stethoscope size={18} className="input-icon" />
                  <input 
                    type="text" 
                    placeholder="e.g. Cardiology / Internal Medicine" 
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                  />
                </div>
              </div>

              <div className="input-group">
                <label>Hospital / Clinic Affiliation</label>
                <div className="input-wrapper">
                  <Building2 size={18} className="input-icon" />
                  <input 
                    type="text" 
                    placeholder="e.g. City General Hospital" 
                    value={hospital}
                    onChange={(e) => setHospital(e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          <div className="input-group">
            <label>Clinical Email</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                placeholder="dr.name@hospital.org" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
              />
            </div>
          </div>

          <div className="input-group">
            <label>Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                placeholder="At least 6 characters" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
                minLength={6}
              />
            </div>
          </div>

          <button type="submit" className="auth-submit-btn" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Authenticating...
              </>
            ) : mode === 'login' ? (
              <>
                Sign In to Portal <ArrowRight size={18} />
              </>
            ) : (
              <>
                Register Clinical Account <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-divider">
          <span>OR</span>
        </div>

        <button 
          className="demo-login-btn" 
          onClick={handleDemoLogin}
          type="button"
          disabled={isLoading}
        >
          <Zap size={18} className="demo-icon" />
          1-Click Demo Login (Dr. Jane Smith)
        </button>
      </div>
    </div>
  );
}
