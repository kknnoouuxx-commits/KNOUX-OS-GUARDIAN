import sqlite3

conn = sqlite3.connect('database/knoux_guardian.db')
cursor = conn.cursor()
modules = ['disk_space_orchestrator', 'update_guardian', 'performance_optimizer', 'network_monitor', 'security_hardener', 'driver_health_manager', 'forensic_analyzer', 'thermal_controller', 'power_manager', 'application_curator', 'registry_guardian', 'backup_orchestrator']
result = {}
for mod in modules:
    cursor.execute('SELECT severity, COUNT(*) FROM system_events WHERE module_name = ? GROUP BY severity', (mod,))
    counts = dict(cursor.fetchall())
    result[mod] = counts
print(result)
conn.close()
