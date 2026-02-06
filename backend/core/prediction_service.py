"""
Prediction service
"""
class PredictionService:
    def __init__(self):
        pass
    
    async def predict(self, data):
        """Make prediction"""
        return {"prediction": "bullish", "confidence": 0.75}

prediction_service = PredictionService()
