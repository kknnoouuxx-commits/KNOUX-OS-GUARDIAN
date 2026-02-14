from src.modules.performance_optimizer import get_performance_optimizer

class VelocityController:
    def __init__(self):
        self.service = get_performance_optimizer()
    
    def execute(self):
        try:
            self.service.start()
            result = self.service.optimize()
            return {"status": "success", "message": "Performance optimized", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e), "data": {}}
