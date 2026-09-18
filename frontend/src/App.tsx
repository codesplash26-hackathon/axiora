import React from 'react';
import './App.css';
import heartBg from './assets/heart_bg.png';

const HeartIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="input-icon"
  >
    <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
  </svg>
);

const App = () => {
  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-logo">ML FOR HEART DISEASE</div>
        <div className="navbar-links">
          <a href="#logout">LOGOUT</a>
          <a href="#advanced">ADVANCED</a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section" style={{ backgroundImage: `url(${heartBg})` }}>
        <div className="hero-overlay">
          <div className="hero-content">
            <h1 className="hero-title">EXAMINING YOUR HEARTS !</h1>
            <p className="hero-description">
              The goal of this project is to train a machine learning model to accurately predict
              whether a sample patient has been diagnosed with heart disease, with higher
              accuracy possible.
            </p>
            <div className="hero-buttons">
              <button className="btn btn-primary">CHECK YOUR HEART</button>
              <button className="btn btn-secondary">KNOW MORE</button>
            </div>
          </div>
        </div>
      </section>

      {/* Data Section */}
      <section className="data-section">
        <h2 className="data-title">HEART'S DATA</h2>
        <p className="data-subtitle">Input your data here</p>

        <form className="data-form">
          <div className="form-grid">
            {[
              'age',
              'sex',
              'chest pain',
              'blood pressure',
              'serum cholestoral',
              'fasting blood sugar',
              'electrocardiographic',
              'max heart rate',
              'induced angina',
              'ST depression',
              'slope',
              'vessels',
              'thal',
            ].map((label, index) => (
              <div className="input-group" key={index}>
                <div className="icon-container">
                  <HeartIcon />
                </div>
                <input type="text" placeholder={label} className="form-input" />
              </div>
            ))}
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-analyze">
              ANALYZE
            </button>
          </div>
        </form>
      </section>
    </div>
  );
};

export default App;
