import joblib
import pandas as pd
import shap
import numpy as np
from typing import Dict, Any

class RiskAgent:
    """
    Risk Agent - Worker Agent
    Loads the pre-trained XGBoost model to predict an internal risk score.
    Now includes Explainable AI (SHAP) to explain the 'Why' behind the score.
    """
    
    def __init__(self, model_path: str = 'risk_model.joblib'):
        self.model_pipeline = None
        self.explainer = None
        self.feature_names = None
        
        try:
            self.model_pipeline = joblib.load(model_path)
            print("✅ XGBoost Risk Model loaded successfully.")
            
            # --- SETUP SHAP EXPLAINER ---
            # We need to access the actual XGBoost model step inside the pipeline
            # Assuming the pipeline step name for the model is 'classifier' or 'model'
            # If it's a simple model (not pipeline), we use it directly.
            
            model_step = None
            if hasattr(self.model_pipeline, 'steps'):
                # Try to find the model step (usually the last one)
                model_step = self.model_pipeline.steps[-1][1]
            else:
                model_step = self.model_pipeline

            # Initialize SHAP TreeExplainer (optimized for XGBoost)
            # Note: SHAP explains the raw model output (margin), not probability directly
            if model_step:
                self.explainer = shap.TreeExplainer(model_step)
            
        except FileNotFoundError:
            print(f"❌ ERROR: Model file not found at {model_path}.")
            print("Please run 'python train_risk_model.py' first.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")

    def get_safety_score(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts the customer's safety score AND provides an explanation.
        """
        if self.model_pipeline is None:
            return {
                "safety_score": 0.50, 
                "explanation": "Risk model unavailable (using default score).",
                "error": "Model not loaded"
            }

        try:
            # 1. Convert customer dict to DataFrame (Standardize Input)
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
            
            # 2. Get Probability
            # Class 0 = Safe, Class 1 = Risk
            probabilities = self.model_pipeline.predict_proba(customer_df)
            safety_score = probabilities[0][0] # Probability of being Safe
            
            # 3. Generate Explanation (SHAP)
            explanation = "Your profile looks balanced." # Default
            
            if self.explainer:
                try:
                    # Pipeline usually has a preprocessor (e.g., OneHotEncoder)
                    # We need to transform the data *before* passing to SHAP if using a pipeline
                    # This logic handles standard sklearn Pipelines
                    if hasattr(self.model_pipeline, 'named_steps') and 'preprocessor' in self.model_pipeline.named_steps:
                        processed_data = self.model_pipeline.named_steps['preprocessor'].transform(customer_df)
                        # Get feature names after transformation (for OneHotEncoded cols)
                        try:
                            feature_names = self.model_pipeline.named_steps['preprocessor'].get_feature_names_out()
                        except:
                            feature_names = [f"Feature {i}" for i in range(processed_data.shape[1])]
                    else:
                        # Fallback for simple models (no preprocessing step)
                        processed_data = customer_df
                        feature_names = customer_df.columns

                    # Calculate SHAP values
                    shap_values = self.explainer.shap_values(processed_data)
                    
                    # Handle different SHAP output formats (sometimes list, sometimes array)
                    if isinstance(shap_values, list):
                        # For binary classification, SHAP might return list [class0_shap, class1_shap]
                        # We want explanations for Class 0 (Safety)
                        vals = shap_values[0] 
                        if len(vals.shape) > 1: vals = vals[0] # Take first row
                    else:
                        vals = shap_values[0] # Take first row

                    explanation = self._generate_text_explanation(vals, feature_names)
                    
                except Exception as shap_e:
                    print(f"⚠️ SHAP Error: {shap_e}")
                    explanation = "Explanation unavailable."

            return {
                "safety_score": round(safety_score, 2),
                "explanation": explanation,
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Error during risk prediction: {e}")
            return {"safety_score": 0.50, "explanation": "Error calculating score.", "error": str(e)}

    def _generate_text_explanation(self, shap_values, feature_names):
        """
        Converts SHAP numerical values into a simple English sentence.
        """
        # Pair feature names with their impact values
        features = list(zip(feature_names, shap_values))
        
        # Sort by absolute impact (biggest movers first)
        features.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Take top 2 factors
        top_factors = features[:2]
        
        reasons = []
        for name, value in top_factors:
            # Clean up feature names (e.g., "cat__city_Mumbai" -> "City")
            clean_name = name.split('__')[-1].replace('_', ' ').title()
            
            # Determine direction (Positive SHAP for class 0 usually means Higher Safety)
            # Note: This depends on how the model was trained. 
            # Assuming SHAP value > 0 pushes towards the class being explained.
            effect = "boosted" if value > 0 else "lowered"
            
            reasons.append(f"{clean_name} ({effect} score)")
            
        if not reasons:
            return "Based on your overall profile."
            
        return f"Key factors: {', '.join(reasons)}."