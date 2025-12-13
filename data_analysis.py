import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib
import numpy as np
import joblib
import shap

# Use TkAgg backend to avoid GUI issues in some environments
try:
    matplotlib.use("TkAgg")
except:
    pass

# Set the style for professional-looking plots
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

class LoanAnalytics:
    def __init__(self, data_path='customer_data.json', model_path='risk_model.joblib'):
        self.model_path = model_path
        self.data_path = data_path
        self.model = None
        self.data = self._load_customer_data()
        
        # Load Risk Model (for SHAP)
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("✅ Model loaded for SHAP analysis.")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
        else:
            print(f"⚠️ Model file not found at {self.model_path}. SHAP analysis will be skipped.")

    def _load_customer_data(self):
        """Loads and processes data from customer.json"""
        if not os.path.exists(self.data_path):
            print(f"❌ Error: {self.data_path} not found! Generating mock data instead.")
            return self._generate_mock_data(100) # Fallback

        try:
            with open(self.data_path, 'r') as f:
                raw_data = json.load(f)
            
            customers = raw_data.get("customers", [])
            if not customers:
                print("⚠️ No customers found in JSON. Using mock data.")
                return self._generate_mock_data(100)

            df = pd.DataFrame(customers)
            
            # --- Data Cleaning & Feature Engineering ---
            # Rename columns to match what visualization expects
            df.rename(columns={
                'salary': 'Income',
                'score': 'Credit_Score',
                'age': 'Age',
                'preapproved_limit': 'Loan_Amount' # Using limit as proxy for amount
            }, inplace=True)

            # Ensure numeric types
            df['Income'] = pd.to_numeric(df['Income'], errors='coerce').fillna(0)
            df['Credit_Score'] = pd.to_numeric(df['Credit_Score'], errors='coerce').fillna(600)
            df['Loan_Amount'] = pd.to_numeric(df['Loan_Amount'], errors='coerce').fillna(0)
            df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(30)

            # Simulate 'Safety_Score' if not present (since it's usually calculated at runtime)
            if 'internal_safety_score' not in df.columns:
                # Simple heuristic for visualization
                df['Safety_Score'] = (
                    (df['Credit_Score'] / 900) * 0.5 + 
                    (df['Income'] / df['Income'].max()) * 0.5
                ).clip(0, 1)
            else:
                df['Safety_Score'] = df['internal_safety_score']

            # Simulate 'Loan_Purpose' and 'Status' if missing
            np.random.seed(42)
            if 'Loan_Purpose' not in df.columns:
                df['Loan_Purpose'] = np.random.choice(
                    ['Wedding', 'Business', 'Medical', 'Travel', 'Renovation', 'Education'], 
                    len(df)
                )
            
            if 'Status' not in df.columns:
                # Mock status based on score
                df['Status'] = df['Credit_Score'].apply(
                    lambda x: 'Approved' if x > 750 else ('Rejected' if x < 650 else 'Secured Loan')
                )

            print(f"✅ Successfully loaded {len(df)} records from {self.data_path}")
            return df

        except Exception as e:
            print(f"❌ Error reading JSON: {e}. Using mock data.")
            return self._generate_mock_data(100)

    def _generate_mock_data(self, n_samples=500):
        """Fallback mock data generator"""
        np.random.seed(42)
        data = pd.DataFrame({
            'Income': np.random.normal(60000, 20000, n_samples).astype(int),
            'Credit_Score': np.random.normal(700, 50, n_samples).astype(int),
            'Loan_Amount': np.random.normal(500000, 200000, n_samples).astype(int),
            'Age': np.random.randint(21, 60, n_samples),
            'Safety_Score': np.random.uniform(0.3, 0.99, n_samples),
            'Loan_Purpose': np.random.choice(['Wedding', 'Business', 'Medical', 'Travel', 'Renovation'], n_samples),
            'Status': np.random.choice(['Approved', 'Rejected', 'Secured Loan'], n_samples, p=[0.4, 0.3, 0.3])
        })
        return data

    def plot_histogram_safety_scores(self):
        plt.figure(figsize=(10, 6))
        sns.histplot(self.data['Safety_Score'], bins=15, kde=True, color='teal')
        plt.title('Distribution of Safety Scores (Customer Base)', fontsize=15)
        plt.xlabel('Safety Score (0=High Risk, 1=Safe)')
        plt.ylabel('Frequency')
        plt.axvline(0.7, color='red', linestyle='--', label='Approval Threshold')
        plt.legend()
        plt.tight_layout()
        plt.savefig('analytics_1_histogram.png') 
        plt.close()
        print("✅ Saved: analytics_1_histogram.png")

    def plot_pie_loan_purposes(self):
        plt.figure(figsize=(8, 8))
        if 'Loan_Purpose' in self.data.columns:
            purpose_counts = self.data['Loan_Purpose'].value_counts()
            plt.pie(purpose_counts, labels=purpose_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
            plt.title('Distribution of Loan Purposes', fontsize=15)
            plt.tight_layout()
            plt.savefig('analytics_2_pie_chart.png')
            plt.close()
            print("✅ Saved: analytics_2_pie_chart.png")
        else:
            print("⚠️ Skipping Pie Chart: 'Loan_Purpose' column missing.")

    def plot_heatmap_correlation(self):
        plt.figure(figsize=(10, 8))
        # Filter only numeric columns for correlation
        numeric_df = self.data.select_dtypes(include=[np.number])
        
        if not numeric_df.empty:
            corr_data = numeric_df.corr()
            sns.heatmap(corr_data, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
            plt.title('Correlation Heatmap (Financial Metrics)', fontsize=15)
            plt.tight_layout()
            plt.savefig('analytics_3_heatmap.png')
            plt.close()
            print("✅ Saved: analytics_3_heatmap.png")
        else:
            print("⚠️ Skipping Heatmap: No numeric data found.")

    def plot_bar_approval_status(self):
        plt.figure(figsize=(10, 6))
        if 'Status' in self.data.columns:
            sns.countplot(x='Status', data=self.data, palette='viridis')
            plt.title('Loan Decision Status Overview', fontsize=15)
            plt.xlabel('Status')
            plt.ylabel('Number of Customers')
            plt.tight_layout()
            plt.savefig('analytics_4_bar_graph.png')
            plt.close()
            print("✅ Saved: analytics_4_bar_graph.png")
        else:
            print("⚠️ Skipping Bar Graph: 'Status' column missing.")

    def plot_shap_analysis(self):
        if self.model is None:
            print("⚠️ Skipping SHAP analysis (Model not found).")
            return

        print("⏳ Generating SHAP Analysis...")
        # Select features that match the model's training data structure
        # NOTE: Ensure these column names match what your XGBoost model expects!
        # Mapping generic names back to model specific names if needed
        X = self.data[['Income', 'Credit_Score', 'Loan_Amount', 'Age']].copy()
        X.columns = ['salary', 'score', 'preapproved_limit', 'age'] # Rename to match training features typically used
        
        try:
            model_step = self.model
            if hasattr(self.model, 'steps'):
                model_step = self.model.steps[-1][1]
                
            explainer = shap.TreeExplainer(model_step)
            shap_values = explainer.shap_values(X)
            
            plt.figure()
            plt.title("SHAP Feature Importance (Global)", fontsize=14)
            shap.summary_plot(shap_values, X, show=False)
            plt.tight_layout()
            plt.savefig('analytics_5_shap_summary.png')
            plt.close()
            print("✅ Saved: analytics_5_shap_summary.png")
            
        except Exception as e:
            print(f"❌ Error generating SHAP plot: {e}")
            print("   (Hint: Check if feature names match your trained model input)")

if __name__ == "__main__":
    print("="*50)
    print("🚀 Generating Analytics from Customer Data...")
    print("="*50)
    
    analytics = LoanAnalytics()
    
    analytics.plot_histogram_safety_scores()
    analytics.plot_pie_loan_purposes()
    analytics.plot_heatmap_correlation()
    analytics.plot_bar_approval_status()
    analytics.plot_shap_analysis()
    
    print("\n✅ Done! Check your folder for the images.")