// KNOUX OS Guardian - Modules Manager

class ModulesManager {
  constructor() {
    this.modules = MODULES_CONFIG;
  }

  getModule(id) {
    return this.modules.find(m => m.id === id);
  }

  getAllModules() {
    return this.modules;
  }

  getModulesByStatus(status) {
    return this.modules.filter(m => m.status === status);
  }

  searchModules(query) {
    const lowerQuery = query.toLowerCase();
    return this.modules.filter(m =>
      m.name.toLowerCase().includes(lowerQuery) ||
      m.description.toLowerCase().includes(lowerQuery)
    );
  }

  updateModuleStatus(id, status) {
    const module = this.getModule(id);
    if (module) {
      module.status = status;
      return true;
    }
    return false;
  }

  getModuleStats(id) {
    const module = this.getModule(id);
    return module ? module.stats : null;
  }
}
