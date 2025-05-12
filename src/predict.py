import joblib
import pandas as pd

# Load the trained model
model = joblib.load('models/outbreak_model.pkl')

def predict_outbreak(new_data):
    """
    Predict outbreak risk for new data.
    Args:
        new_data (dict): Input features (e.g., NewCases, Humidity, etc.).
    Returns:
        int: 0 (No Outbreak) or 1 (Outbreak).
    """
    # Convert input to DataFrame
    input_df = pd.DataFrame([new_data])
    
    # Predict
    prediction = model.predict(input_df)
    return prediction[0]

# Example usage
if __name__ == "__main__":
    # Example input
    new_data = {
        'NewCases': 120,
        'Humidity_x': 85,
        'PopulationDensity': 20000,
        'Temperature': 28,
        'Rainfall': 12.5
    }
    
    # Make prediction
    result = predict_outbreak(new_data)
    print(f"Outbreak Risk: {result} (0 = No, 1 = Yes)")