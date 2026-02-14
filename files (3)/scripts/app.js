// KNOUX OS Guardian - Main Application

class KNOUXApp {
  constructor() {
    this.init();
  }

  init() {
    this.hideSplashScreen();
    this.renderModules();
    this.setupEventListeners();
    this.setupNavigation();
    console.log('✅ KNOUX OS Guardian initialized');
  }

  hideSplashScreen() {
    setTimeout(() => {
      const splash = document.getElementById('splashScreen');
      if (splash) {
        splash.classList.add('hidden');
        setTimeout(() => splash.remove(), 500);
      }
    }, 2000);
  }

  renderModules() {
    const grid = document.getElementById('modulesGrid');
    if (!grid) return;

    grid.innerHTML = MODULES_CONFIG.map((module, index) => `
      <div class="module-card animate-fadeInUp delay-${(index % 8 + 1) * 100}" 
           style="--module-color: ${module.color}"
           onclick="app.openModule('${module.id}')">
        <div class="module-header">
          <div class="module-icon">${module.icon}</div>
          <div class="module-content">
            <h3 class="module-title">${module.name}</h3>
            <p class="module-description">${module.description}</p>
          </div>
        </div>
        <div class="module-meta">
          ${Object.entries(module.stats).map(([key, value]) => `
            <div class="module-stat">
              <div class="module-stat-label">${key}</div>
              <div class="module-stat-value">${value}</div>
            </div>
          `).join('')}
          <span class="module-status ${module.status}">${module.status}</span>
        </div>
      </div>
    `).join('');
  }

  setupEventListeners() {
    // Mobile menu toggle
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileToggle && sidebar) {
      mobileToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchModules(e.target.value);
      });
    }

    // View toggle
    const viewBtns = document.querySelectorAll('.view-btn');
    viewBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        viewBtns.forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const view = e.currentTarget.dataset.view;
        this.changeView(view);
      });
    });

    // Settings button
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
      settingsBtn.addEventListener('click', () => {
        alert('Settings panel - Backend integration pending\\nPath: ' + APP_CONFIG.backendPath);
      });
    }
  }

  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        navItems.forEach(nav => nav.classList.remove('active'));
        e.currentTarget.classList.add('active');
        
        const page = e.currentTarget.dataset.page;
        if (page) this.navigateTo(page);
      });
    });
  }

  navigateTo(page) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => p.classList.remove('active'));
    
    const targetPage = document.getElementById(`${page}Page`);
    if (targetPage) {
      targetPage.classList.add('active');
    }
    
    console.log(`📍 Navigated to: ${page}`);
  }

  openModule(moduleId) {
    const module = MODULES_CONFIG.find(m => m.id === moduleId);
    if (!module) return;

    console.log(`🚀 Opening module: ${module.name}`);
    alert(`Module: ${module.name}\\n\\nStatus: ${module.status}\\nBackend: ${APP_CONFIG.backendPath}\\n\\n✅ UI Complete - Backend integration pending`);
  }

  searchModules(query) {
    const cards = document.querySelectorAll('.module-card');
    const lowerQuery = query.toLowerCase();

    cards.forEach(card => {
      const module = MODULES_CONFIG.find(m => 
        card.textContent.toLowerCase().includes(m.name.toLowerCase())
      );

      if (!module) return;

      const matches = 
        module.name.toLowerCase().includes(lowerQuery) ||
        module.description.toLowerCase().includes(lowerQuery);

      card.style.display = matches ? 'flex' : 'none';
    });
  }

  changeView(view) {
    const grid = document.getElementById('modulesGrid');
    if (!grid) return;

    if (view === 'list') {
      grid.style.gridTemplateColumns = '1fr';
    } else {
      grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(320px, 1fr))';
    }
  }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new KNOUXApp();
});
