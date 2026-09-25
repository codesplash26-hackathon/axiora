import React, { useState } from 'react';
import { X, User, Stethoscope, Mail, Lock, ArrowRight } from 'lucide-react';
import './AuthModal.css';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode: 'login' | 'signup';
  onAuthenticate: (user: { type: 'patient' | 'doctor'; name: string }) => void;
}

export default function AuthModal({ isOpen, onClose, initialMode, onAuthenticate }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'signup'>(initialMode);
  const [userType, setUserType] = useState<'patient' | 'doctor'>('patient');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock authentication for the hackathon
    const userName = name || (userType === 'doctor' ? 'Dr. Smith' : 'Alex Johnson');
    onAuthenticate({ type: userType, name: userName });
    onClose();
  };

  return (
    <div className="auth-overlay fade-in">
      <div className="auth-modal fade-up">
        <button className="auth-close" onClick={onClose}>
          <X size={24} />
        </button>

        <div className="auth-header">
          <h2 className="auth-title shiny-heading-text">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="auth-subtitle">
            {mode === 'login' 
              ? 'Enter your credentials to access your portal' 
              : 'Join CardioRecourse to manage cardiovascular health'}
          </p>
        </div>

        <div className="auth-type-toggle">
          <button 
            type="button"
            className={`type-btn ${userType === 'patient' ? 'active' : ''}`}
            onClick={() => setUserType('patient')}
          >
            <User size={20} />
            <span>Patient</span>
          </button>
          <button 
            type="button"
            className={`type-btn ${userType === 'doctor' ? 'active' : ''}`}
            onClick={() => setUserType('doctor')}
          >
            <Stethoscope size={20} />
            <span>Clinician</span>
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div className="input-group">
              <label>Full Name</label>
              <div className="input-wrapper">
                <User size={18} className="input-icon" />
                <input 
                  type="text" 
                  placeholder={userType === 'doctor' ? "Dr. Jane Doe" : "John Doe"}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required 
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label>Email Address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                placeholder="you@example.com" 
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
            {mode === 'login' ? 'Sign In' : 'Create Account'}
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="auth-footer">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button className="text-link" onClick={() => setMode('signup')}>Sign up</button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button className="text-link" onClick={() => setMode('login')}>Sign in</button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
