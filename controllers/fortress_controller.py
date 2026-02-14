from src.modules.security_hardener import get_security_hardener

class FortressController:
    def __init__(self):
        self.service = get_security_hardener()
    
    def execute(self):
        try:
            self.service.start()
            result = self.service.scan()
            return {"status": "success", "message": "Fortress scan completed", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
