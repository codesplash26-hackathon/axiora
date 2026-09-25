import React, { useState } from 'react';
import { X, Stethoscope, Mail, Lock, ArrowRight, Zap } from 'lucide-react';
import './DoctorLoginModal.css';

interface DoctorLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (doctor: { id: string; name: string; email: string }) => void;
}

export default function DoctorLoginModal({ isOpen, onClose, onLogin }: DoctorLoginModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

  const handleStandardLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock standard login
    onLogin({ id: 'doc-002', name: 'Dr. Clinician', email });
    onClose();
  };

  const handleDemoLogin = () => {
    // 1-Click Demo Login from the plan
    onLogin({ id: 'doc-001', name: 'Dr. Smith', email: 'dr.smith@cardiorecourse.lk' });
    onClose();
  };

  return (
    <div className="auth-overlay fade-in">
      <div className="auth-modal fade-up">
        <button className="auth-close" onClick={onClose}>
          <X size={24} />
        </button>

        <div className="auth-header">
          <div className="auth-icon-wrapper">
            <Stethoscope size={32} color="#0284c7" />
          </div>
          <h2 className="auth-title shiny-heading-text">Doctor Portal</h2>
          <p className="auth-subtitle">Secure clinical access for healthcare providers</p>
        </div>

        <form className="auth-form" onSubmit={handleStandardLogin}>
          <div className="input-group">
            <label>Clinical Email</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                placeholder="dr.name@hospital.com" 
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
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
            </div>
          </div>

          <button type="submit" className="auth-submit-btn">
            Sign In to Portal
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="auth-divider">
          <span>OR</span>
        </div>

        <button className="demo-login-btn" onClick={handleDemoLogin}>
          <Zap size={18} className="demo-icon" />
          1-Click Demo Login
        </button>
      </div>
    </div>
  );
}
