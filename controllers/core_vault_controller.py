from src.modules.registry_guardian import get_registry_guardian

class CoreVaultController:
    def __init__(self):
        self.service = get_registry_guardian()
    
    def execute(self):
        try:
            self.service.start()
            result = self.service.scan()
            return {"status": "success", "message": "Registry protected", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
