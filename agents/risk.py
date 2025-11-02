import joblib
import pandas as pd
from typing import Dict, Any

class RiskAgent:
    """
    Risk Agent - Worker Agent
    Loads the pre-trained XGBoost model to predict an internal risk score.
    """
    
    def __init__(self, model_path: str = 'risk_model.joblib'):
        try:
            self.model_pipeline = joblib.load(model_path)
            print("✅ XGBoost Risk Model loaded successfully.")
        except FileNotFoundError:
            print(f"❌ ERROR: Model file not found at {model_path}.")
            print("Please run 'python train_risk_model.py' first.")
            self.model_pipeline = None
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model_pipeline = None

    def get_safety_score(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts the customer's safety score (probability of NOT being high risk).
        """
        if self.model_pipeline is None:
            return {"safety_score": 0.50, "error": "Model not loaded"} # Neutral score

        try:
            # 1. Convert the single customer dict into the format used for training
            salary = customer_data.get('salary', customer_data.get('monthly_income', 0))
            
            data = {
                "age": customer_data.get('age', 30),
                "salary": salary,
                "preapproved_limit": customer_data.get('preapproved_limit', customer_data.get('pre_approved_limit', 0)),
                "has_current_loan": 1 if customer_data.get('current_loans', 'None') != 'None' else 0,
                "has_collateral": 1 if customer_data.get('collateral', 'None') != 'None' else 0,
                "city": customer_data.get('city', 'Unknown')
            }
            
            customer_df = pd.DataFrame([data])
            
            # 2. Use the pipeline to predict probabilities
            # model.predict_proba() returns [[prob_class_0, prob_class_1]]
            # Class 0 = Low Risk (Safe)
            # Class 1 = High Risk
            probabilities = self.model_pipeline.predict_proba(customer_df)
            
            safety_score = probabilities[0][0] # Probability of being "Low Risk"
            
            return {
                "safety_score": round(safety_score, 2),
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Error during risk prediction: {e}")
            return {"safety_score": 0.50, "error": str(e)} # Neutral score