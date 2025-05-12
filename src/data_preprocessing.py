import pandas as pd
import numpy as np

def preprocess_health_data():
    # Load mock data instead of covid_global.csv
    health_data = pd.read_csv('data/raw/health/mock_outbreak_data.csv')
    climate_data = pd.read_csv('data/raw/climate/mock_climate_data.csv')

    # Merge datasets on 'Region' and 'Date'
    merged_data = pd.merge(
        health_data,
        climate_data,
        on=['Region', 'Date'],
        how='inner'
    )
    
    # Save processed data
    merged_data.to_csv('data/processed/merged_data.csv', index=False)
    return merged_data

if __name__ == "__main__":
    preprocess_health_data()