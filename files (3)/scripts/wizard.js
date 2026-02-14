// KNOUX OS Guardian - Setup Wizard

class SetupWizard {
  constructor() {
    this.currentStep = 0;
    this.totalSteps = 4;
    this.wizardData = {};
  }
  
  init() {
    this.renderWizard();
    this.attachEventListeners();
  }
  
  renderWizard() {
    const wizardHTML = `
      <div class="wizard-container glass-modal">
        <div class="wizard-progress">
          ${this.renderProgressSteps()}
        </div>
        <div class="wizard-content">
          ${this.renderCurrentStep()}
        </div>
        <div class="wizard-actions">
          <button class="wizard-btn btn-secondary" onclick="wizard.previousStep()" ${this.currentStep === 0 ? 'disabled' : ''}>
            ← Previous
          </button>
          <button class="wizard-btn btn-primary" onclick="wizard.nextStep()">
            ${this.currentStep === this.totalSteps - 1 ? 'Finish' : 'Next →'}
          </button>
        </div>
      </div>
    `;
    
    document.getElementById('wizardRoot').innerHTML = wizardHTML;
  }
  
  renderProgressSteps() {
    const steps = ['Welcome', 'Configure Modules', 'Set Preferences', 'Complete'];
    return steps.map((step, index) => `
      <div class="wizard-step ${index === this.currentStep ? 'active' : ''} ${index < this.currentStep ? 'completed' : ''}">
        <div class="step-number">${index + 1}</div>
        <div class="step-label">${step}</div>
      </div>
    `).join('');
  }
  
  renderCurrentStep() {
    const steps = [
      this.renderWelcomeStep(),
      this.renderModuleConfigStep(),
      this.renderPreferencesStep(),
      this.renderCompleteStep()
    ];
    
    return steps[this.currentStep];
  }
  
  renderWelcomeStep() {
    return `
      <div class="wizard-step-content animate-fade-in-scale">
        <div class="wizard-icon">🛡️</div>
        <h2>Welcome to KNOUX OS Guardian</h2>
        <p>Let's set up your system protection and optimization suite.</p>
        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-icon">🔒</span>
            <span>Advanced Security Hardening</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">⚡</span>
            <span>Performance Optimization</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">💾</span>
            <span>Automated Backup Management</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span>AI-Powered Recommendations</span>
          </div>
        </div>
      </div>
    `;
  }
  
  renderModuleConfigStep() {
    return `
      <div class="wizard-step-content animate-fade-in-scale">
        <h2>Select Modules to Enable</h2>
        <p>Choose which protection modules you want to activate.</p>
        <div class="module-selection-grid">
          <label class="module-checkbox glass-card">
            <input type="checkbox" checked data-module="security">
            <span class="checkbox-icon">🔒</span>
            <span class="checkbox-label">Security Hardener</span>
          </label>
          <label class="module-checkbox glass-card">
            <input type="checkbox" checked data-module="backup">
            <span class="checkbox-icon">💾</span>
            <span class="checkbox-label">Backup Orchestrator</span>
          </label>
          <label class="module-checkbox glass-card">
            <input type="checkbox" checked data-module="performance">
            <span class="checkbox-icon">⚡</span>
            <span class="checkbox-label">Performance Optimizer</span>
          </label>
          <label class="module-checkbox glass-card">
            <input type="checkbox" checked data-module="ai">
            <span class="checkbox-icon">🤖</span>
            <span class="checkbox-label">AI/ML Assistant</span>
          </label>
        </div>
      </div>
    `;
  }
  
  renderPreferencesStep() {
    return `
      <div class="wizard-step-content animate-fade-in-scale">
        <h2>Set Your Preferences</h2>
        <p>Customize your Guardian experience.</p>
        <div class="preferences-form">
          <div class="form-group">
            <label>Theme</label>
            <select class="glass-input">
              <option value="default">Crystalline (Default)</option>
              <option value="night">Night</option>
              <option value="calm">Calm</option>
            </select>
          </div>
          <div class="form-group">
            <label>Scan Frequency</label>
            <select class="glass-input">
              <option value="daily" selected>Daily</option>
              <option value="weekly">Weekly</option>
              <option value="manual">Manual Only</option>
            </select>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" checked> Enable notifications
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" checked> Auto-start on boot
            </label>
          </div>
        </div>
      </div>
    `;
  }
  
  renderCompleteStep() {
    return `
      <div class="wizard-step-content animate-fade-in-scale">
        <div class="wizard-icon success">✓</div>
        <h2>Setup Complete!</h2>
        <p>KNOUX OS Guardian is ready to protect your system.</p>
        <div class="setup-summary glass-card">
          <h3>Configuration Summary</h3>
          <ul>
            <li>✓ 4 modules enabled</li>
            <li>✓ Daily security scans scheduled</li>
            <li>✓ Notifications enabled</li>
            <li>✓ Auto-start configured</li>
          </ul>
        </div>
      </div>
    `;
  }
  
  nextStep() {
    if (this.currentStep < this.totalSteps - 1) {
      this.currentStep++;
      this.renderWizard();
    } else {
      this.completeSetup();
    }
  }
  
  previousStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.renderWizard();
    }
  }
  
  completeSetup() {
    localStorage.setItem('knoux-wizard-completed', 'true');
    window.location.href = 'index.html';
  }
  
  attachEventListeners() {
    // Add any additional event listeners here
  }
}

// Initialize wizard if on wizard page
if (document.getElementById('wizardRoot')) {
  const wizard = new SetupWizard();
  wizard.init();
}
