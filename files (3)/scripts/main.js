const MODULES = [
  {
    id: 'security', title: 'Security Hardener', icon: '🔒',
    description: 'Comprehensive system security scanning', color: '#ef4444', colorDark: '#dc2626', glow: 'rgba(239, 68, 68, 0.4)',
    stats: [{ label: 'Threats', value: '0' }, { label: 'Status', value: 'Secure' }]
  },
  {
    id: 'backup', title: 'Backup Orchestrator', icon: '💾',
    description: 'Automated backup management', color: '#8b5cf6', colorDark: '#7c3aed', glow: 'rgba(139, 92, 246, 0.4)',
    stats: [{ label: 'Backups', value: '12' }, { label: 'Last', value: '2h ago' }]
  },
  {
    id: 'performance', title: 'Performance Optimizer', icon: '⚡',
    description: 'Real-time performance monitoring', color: '#10b981', colorDark: '#059669', glow: 'rgba(16, 185, 129, 0.4)',
    stats: [{ label: 'CPU', value: '42%' }, { label: 'RAM', value: '8.2GB' }]
  },
  {
    id: 'registry', title: 'Registry Guardian', icon: '📋',
    description: 'Windows Registry maintenance', color: '#f59e0b', colorDark: '#d97706', glow: 'rgba(245, 158, 11, 0.4)',
    stats: [{ label: 'Keys', value: '2.4M' }, { label: 'Errors', value: '3' }]
  },
  {
    id: 'disk', title: 'Disk Space Orchestrator', icon: '💿',
    description: 'Intelligent disk space management', color: '#06b6d4', colorDark: '#0891b2', glow: 'rgba(6, 182, 212, 0.4)',
    stats: [{ label: 'Free', value: '128GB' }, { label: 'Used', value: '67%' }]
  },
  {
    id: 'network', title: 'Network Monitor', icon: '🌐',
    description: 'Network traffic analysis', color: '#3b82f6', colorDark: '#2563eb', glow: 'rgba(59, 130, 246, 0.4)',
    stats: [{ label: 'Download', value: '2.4MB/s' }, { label: 'Upload', value: '856KB/s' }]
  },
  {
    id: 'driver', title: 'Driver Health Manager', icon: '🔧',
    description: 'Hardware driver monitoring', color: '#ec4899', colorDark: '#db2777', glow: 'rgba(236, 72, 153, 0.4)',
    stats: [{ label: 'Drivers', value: '47' }, { label: 'Updates', value: '2' }]
  },
  {
    id: 'forensic', title: 'Forensic Analyzer', icon: '🔍',
    description: 'Advanced system forensics', color: '#6366f1', colorDark: '#4f46e5', glow: 'rgba(99, 102, 241, 0.4)',
    stats: [{ label: 'Events', value: '1.2K' }, { label: 'Alerts', value: '0' }]
  },
  {
    id: 'thermal', title: 'Thermal Controller', icon: '🌡️',
    description: 'Temperature monitoring', color: '#f97316', colorDark: '#ea580c', glow: 'rgba(249, 115, 22, 0.4)',
    stats: [{ label: 'CPU', value: '52°C' }, { label: 'GPU', value: '48°C' }]
  },
  {
    id: 'power', title: 'Power Manager', icon: '🔋',
    description: 'Power consumption optimization', color: '#84cc16', colorDark: '#65a30d', glow: 'rgba(132, 204, 22, 0.4)',
    stats: [{ label: 'Battery', value: '100%' }, { label: 'Mode', value: 'Balanced' }]
  },
  {
    id: 'apps', title: 'Application Curator', icon: '📱',
    description: 'Application health monitoring', color: '#14b8a6', colorDark: '#0d9488', glow: 'rgba(20, 184, 166, 0.4)',
    stats: [{ label: 'Apps', value: '84' }, { label: 'Updates', value: '5' }]
  },
  {
    id: 'ai', title: 'AI/ML Assistant', icon: '🤖',
    description: 'Intelligent recommendations', color: '#a855f7', colorDark: '#9333ea', glow: 'rgba(168, 85, 247, 0.4)',
    stats: [{ label: 'Actions', value: '23' }, { label: 'Saved', value: '4.2h' }]
  }
];

document.addEventListener('DOMContentLoaded', () => {
  initializeSplashScreen();
  renderModuleCards();
  initializeSearch();
});

function initializeSplashScreen() {
  const splash = document.getElementById('splash-screen');
  if (splash) {
    setTimeout(() => {
      splash.style.opacity = '0';
      setTimeout(() => splash.style.display = 'none', 500);
    }, 2000);
  }
}

function renderModuleCards() {
  const grid = document.getElementById('moduleGrid');
  if (!grid) return;
  
  grid.innerHTML = MODULES.map((m, i) => `
    <div class="module-card glass-card hover-lift animate-fade-in-scale stagger-${(i % 8) + 1}"
         style="--module-color: ${m.color}; --module-color-dark: ${m.colorDark}; --module-glow: ${m.glow};"
         data-module="${m.id}" onclick="openModule('${m.id}')">
      <div class="module-header">
        <div class="module-icon">${m.icon}</div>
        <div class="module-info">
          <h3 class="module-title">${m.title}</h3>
          <p class="module-description">${m.description}</p>
        </div>
      </div>
      <div class="module-stats">
        ${m.stats.map(s => `
          <div class="stat-item">
            <div class="stat-label">${s.label}</div>
            <div class="stat-value">${s.value}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

function initializeSearch() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      document.querySelectorAll('.module-card').forEach(card => {
        const moduleId = card.getAttribute('data-module');
        const module = MODULES.find(m => m.id === moduleId);
        if (module && (module.title.toLowerCase().includes(query) || module.description.toLowerCase().includes(query))) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }
}

function openModule(moduleId) {
  if (moduleId === 'security') {
    window.location.href = 'modules/security.html';
  } else {
    alert(`Module: ${moduleId}\nThis module page will be created following the security.html template.\nBackend integration pending.`);
  }
}
