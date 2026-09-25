import React from 'react';
import './DoctorDashboard.css';
import { Heart, Stethoscope, Users, Activity, Target, ShieldCheck, Search, Filter } from 'lucide-react';

interface DoctorDashboardPageProps {
  doctor: { id: string; name: string; email: string };
  onLogout: () => void;
  onNewAssessment: () => void;
}

// Dummy data for the Patient Table
const recentPatients = [
  { id: 'PT-8842', age: 45, sex: 'Male', baselineRisk: 28.4, status: 'Plan Generated', date: '2023-10-25' },
  { id: 'PT-7193', age: 62, sex: 'Female', baselineRisk: 15.2, status: 'Borderline', date: '2023-10-25' },
  { id: 'PT-9921', age: 58, sex: 'Male', baselineRisk: 42.1, status: 'Pending Review', date: '2023-10-24' },
  { id: 'PT-3410', age: 39, sex: 'Female', baselineRisk: 4.5, status: 'Low Risk', date: '2023-10-24' },
  { id: 'PT-6022', age: 51, sex: 'Male', baselineRisk: 21.0, status: 'Plan Generated', date: '2023-10-23' },
];

const DoctorDashboardPage: React.FC<DoctorDashboardPageProps> = ({ doctor, onLogout, onNewAssessment }) => {
  return (
    <div className="doctor-dashboard-container">
      {/* Doctor Navbar */}
      <nav className="doctor-navbar">
        <div className="doctor-nav-brand">
          <Heart size={24} color="#38bdf8" />
          <span>CardioRecourse <span style={{ color: '#94a3b8', fontWeight: 500 }}>| Clinical Portal</span></span>
        </div>
        <div className="doctor-nav-user">
          <div className="doctor-user-info">
            <Stethoscope size={18} />
            <span>Dr. {doctor.name.replace('Dr. ', '')}</span>
          </div>
          <button className="btn-doctor-logout" onClick={onLogout}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* Dashboard Content */}
      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>Clinical Overview</h1>
          <p>Monitor patient cardiovascular risk assessments and AI-generated recourse plans.</p>
        </div>

        {/* Overview Cards */}
        <div className="overview-grid">
          <div className="stat-card">
            <div className="stat-info">
              <h3>Total Assessments</h3>
              <div className="stat-value">1,284</div>
              <div className="stat-trend positive">↑ 12% this month</div>
            </div>
            <div className="stat-icon blue">
              <Users size={24} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <h3>High Risk Patients</h3>
              <div className="stat-value">342</div>
              <div className="stat-trend negative">↑ 5% this month</div>
            </div>
            <div className="stat-icon red">
              <Activity size={24} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <h3>Action Plans Issued</h3>
              <div className="stat-value">892</div>
              <div className="stat-trend positive">↑ 18% this month</div>
            </div>
            <div className="stat-icon green">
              <ShieldCheck size={24} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <h3>Avg Risk Reduction</h3>
              <div className="stat-value">-14.2%</div>
              <div className="stat-trend positive">Projected DiCE target</div>
            </div>
            <div className="stat-icon purple">
              <Target size={24} />
            </div>
          </div>
        </div>

        {/* Patient Table */}
        <div className="patient-table-container">
          <div className="table-header">
            <h2>Recent Patient Runs</h2>
            <div className="table-actions">
              <div className="search-box">
                <Search size={18} className="search-icon" />
                <input type="text" placeholder="Search Patient ID..." />
              </div>
              <button className="btn-action">
                <Filter size={16} style={{ verticalAlign: 'middle', marginRight: '0.25rem' }} /> Filter
              </button>
              <button className="btn-action primary" onClick={onNewAssessment}>
                + New Assessment
              </button>
            </div>
          </div>
          <table className="patient-table">
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Date</th>
                <th>Age / Sex</th>
                <th>Baseline Risk</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentPatients.map((pt) => (
                <tr key={pt.id}>
                  <td style={{ fontWeight: 600, color: '#0ea5e9' }}>{pt.id}</td>
                  <td>{pt.date}</td>
                  <td>{pt.age} / {pt.sex}</td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{pt.baselineRisk.toFixed(1)}%</span>
                  </td>
                  <td>
                    <span className={`risk-badge ${pt.baselineRisk >= 20 ? 'high' : pt.baselineRisk >= 10 ? 'borderline' : 'low'}`}>
                      {pt.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn-action">View Report</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DoctorDashboardPage;
