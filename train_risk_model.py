import pandas as pd
import xgboost as xgb
import joblib
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def load_data():
    """Load customer data from JSON."""
    json_path = 'customer_data.json'
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return None
        
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Normalize data to the structure we need
    customer_list = []
    for customer in data['customers']:
        customer_list.append({
            "age": customer['age'],
            "salary": customer['salary'],
            "preapproved_limit": customer['preapproved_limit'],
            "has_current_loan": 1 if customer.get('current_loans', 'None') != 'None' else 0,
            "has_collateral": 1 if customer.get('collateral', 'None') != 'None' else 0,
            "city": customer.get('city', 'Unknown'),
            # --- This is our Target Variable (Y) ---
            # We are creating a proxy for risk.
            # 1 = High Risk, 0 = Low Risk
            "is_high_risk": 1 if customer['score'] < 700 else 0
        })
        
    return pd.DataFrame(customer_list)

def train_model():
    """Train and save the XGBoost risk model."""
    
    df = load_data()
    if df is None:
        return

    # Define features (X) and target (y)
    # We deliberately DO NOT use the CIBIL 'score' as a feature,
    # because our target 'is_high_risk' is derived from it.
    # We want to see if other features can predict this risk.
    features = ['age', 'salary', 'preapproved_limit', 'has_current_loan', 'has_collateral', 'city']
    target = 'is_high_risk'
    
    X = df[features]
    y = df[target]
    
    # We have very little data (20 samples), so we'll train on all of it
    # for this demo. In a real-world scenario, you'd need thousands
    # of rows and a proper train/test split.
    X_train, y_train = X, y

    # Create a preprocessor
    # We need to One-Hot Encode the 'city' column
    categorical_features = ['city']
    numeric_features = ['age', 'salary', 'preapproved_limit', 'has_current_loan', 'has_collateral']

    # Create a transformer pipeline for numeric and categorical features
    numeric_transformer = Pipeline(steps=[('num', 'passthrough')]) # No scaling needed for XGB
    categorical_transformer = Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore'))])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    # Create the full XGBoost model pipeline
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
    ])

    # Train the model
    print("Training XGBoost risk model...")
    model_pipeline.fit(X_train, y_train)
    
    # Save the pipeline
    model_path = 'risk_model.joblib'
    joblib.dump(model_pipeline, model_path)
    
    print(f"✅ Model saved successfully to {model_path}")
    print("You can now run main.py")

if __name__ == "__main__":
    train_model()