// KNOUX OS Guardian - Configuration
const MODULES_CONFIG = [
  {
    id: 'security', name: 'Security Hardener', icon: '🛡️',
    description: 'Advanced threat detection and system hardening',
    color: '#ef4444', status: 'active',
    stats: { scans: '2,547', threats: '0', lastScan: '2h ago' }
  },
  {
    id: 'backup', name: 'Backup Orchestrator', icon: '💾',
    description: 'Automated backup with cloud sync',
    color: '#8b5cf6', status: 'active',
    stats: { backups: '47', size: '284GB', lastBackup: '3h ago' }
  },
  {
    id: 'performance', name: 'Performance Optimizer', icon: '⚡',
    description: 'Real-time system optimization',
    color: '#10b981', status: 'active',
    stats: { cpu: '24%', ram: '67%', uptime: '5d 12h' }
  },
  {
    id: 'registry', name: 'Registry Guardian', icon: '📋',
    description: 'Registry maintenance and cleanup',
    color: '#f59e0b', status: 'active',
    stats: { keys: '2.4M', errors: '3', fixed: '145' }
  },
  {
    id: 'disk', name: 'Disk Manager', icon: '💿',
    description: 'Disk analysis and health monitoring',
    color: '#06b6d4', status: 'active',
    stats: { free: '128GB', used: '67%', temp: '2.4GB' }
  },
  {
    id: 'network', name: 'Network Monitor', icon: '🌐',
    description: 'Network traffic analysis',
    color: '#3b82f6', status: 'active',
    stats: { down: '2.4MB/s', up: '856KB/s', connections: '47' }
  },
  {
    id: 'driver', name: 'Driver Manager', icon: '🔧',
    description: 'Hardware driver updates',
    color: '#ec4899', status: 'active',
    stats: { total: '47', updates: '2', outdated: '0' }
  },
  {
    id: 'forensic', name: 'Forensic Analyzer', icon: '🔍',
    description: 'System forensics and investigation',
    color: '#6366f1', status: 'active',
    stats: { events: '1,247', alerts: '0', scans: '24' }
  },
  {
    id: 'thermal', name: 'Thermal Controller', icon: '🌡️',
    description: 'Temperature and cooling management',
    color: '#f97316', status: 'active',
    stats: { cpu: '52°C', gpu: '48°C', fan: '1,847 RPM' }
  },
  {
    id: 'power', name: 'Power Manager', icon: '🔋',
    description: 'Power and battery optimization',
    color: '#84cc16', status: 'active',
    stats: { battery: '100%', mode: 'Balanced', time: '4h 23m' }
  },
  {
    id: 'apps', name: 'Application Curator', icon: '📱',
    description: 'App monitoring and updates',
    color: '#14b8a6', status: 'active',
    stats: { installed: '84', updates: '5', size: '47GB' }
  },
  {
    id: 'ai', name: 'AI Assistant', icon: '🤖',
    description: 'Intelligent automation',
    color: '#a855f7', status: 'active',
    stats: { actions: '247', saved: '4.2h', predictions: '12' }
  }
];

const APP_CONFIG = {
  name: 'KNOUX OS Guardian',
  version: '1.0.0',
  backendPath: 'F:\\KNOUX_OS_Guardian\\dist\\KNOUX_OS_Guardian.exe'
};
