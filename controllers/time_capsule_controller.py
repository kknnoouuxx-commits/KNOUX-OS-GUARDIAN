from src.modules.backup_orchestrator import get_backup_orchestrator

class TimeCapsuleController:
    def __init__(self):
        self.service = get_backup_orchestrator()
    
    def execute(self):
        try:
            self.service.start()
            result = self.service.create_backup()
            return {"status": "success", "message": "Backup created", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
