# Disease Outbreak Prediction Dashboard

An interactive web application for predicting disease outbreak risks based on environmental and demographic factors.

## Features

- Modern, responsive UI with eye-catching animations
- Interactive form inputs with real-time feedback
- Loading animation with progress indicators
- Risk assessment visualization with gauge charts
- Detailed risk analysis reports
- Historical trend analysis
- User authentication with Firebase
- AI Health Assistant for symptom analysis and disease identification

## Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Loading Animation
![Loading Animation](screenshots/loading.png)

### Risk Analysis
![Risk Analysis](screenshots/risk-analysis.png)

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/disease-outbreak-prediction.git
cd disease-outbreak-prediction
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
cd src
python app.py
```

4. Open your browser and navigate to:
```
http://127.0.0.1:8050/
```

## Project Structure

```
disease-outbreak-prediction/
├── data/                  # Data files
├── models/                # ML models
├── src/                   # Source code
│   ├── app.py             # Main application
│   └── caching_config.py  # Cache configuration
├── static/                # Static assets
│   ├── style.css          # Main styles
│   └── loading.css        # Loading animation styles
├── templates/             # HTML templates
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Usage

1. Log in to the dashboard using your credentials
2. Enter the required parameters:
   - New Cases
   - Humidity
   - Population Density
   - Temperature
   - Rainfall
   - Vaccination Rate
3. Click "Analyze Outbreak Risk"
4. View the risk assessment and recommendations
5. Use the AI Health Assistant:
   - Type your symptoms in the chat
   - Click on symptom chips for quick input
   - Get immediate analysis of possible conditions
   - Receive recommendations based on symptoms

## Technologies Used

- **Dash**: Interactive web application framework
- **Plotly**: Interactive data visualization
- **Flask**: Web server backend
- **Firebase**: User authentication
- **Pandas/NumPy**: Data processing
- **Scikit-learn**: Machine learning models
- **OpenAI API** (optional): Enhanced AI Health Assistant responses

## Contributors

- Your Name - Initial work

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspiration from public health monitoring systems
- Modern UI/UX design principles 