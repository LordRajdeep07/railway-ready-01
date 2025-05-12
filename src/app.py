import os
import sys
import logging
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Import caching configuration
from caching_config import disable_caches

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from flask import Flask, redirect, render_template, request, url_for, flash, session, jsonify
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
    UserMixin
)
import joblib
import requests
import json

# Add OpenAI integration
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI API Key - Replace with your actual API key or use environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
openai.api_key = OPENAI_API_KEY

# Feature flag to toggle between local and API responses
USE_CHATGPT_API = False  # Set to False for fast local responses, True for API calls

# Application Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models/outbreak_model.pkl")
DB_PATH = os.path.join(BASE_DIR, 'models/database.db')
TEMPLATE_DIR = os.path.join(BASE_DIR, "../templates")
STATIC_DIR = os.path.join(BASE_DIR, "../static")

# Import caching configuration
from caching_config import disable_caches

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from flask import Flask, redirect, render_template, request, url_for, flash, session, jsonify
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
    UserMixin
)
import joblib
import requests
import json

# Firebase configuration - will be passed to templates
firebase_config = {
    "apiKey": "AIzaSyDxEVoMUMGYgbit8uYbjITLw1TcFhAu2zU",
    "authDomain": "alpha-8d676.firebaseapp.com",
    "projectId": "alpha-8d676",
    "storageBucket": "alpha-8d676.firebasestorage.app",
    "messagingSenderId": "47580545885",
    "appId": "1:47580545885:web:d67c304a39a886c555deb4",
    "measurementId": "G-1Y46N5QES1"
}

# Initialize Flask
server = Flask(__name__, template_folder=TEMPLATE_DIR)

# Force delete cache
cache_settings = disable_caches()
server.config.update(cache_settings)

server.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "your-secret-key-here"),
)

# Disable template caching explicitly
server.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize Dash
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.SOLAR],
    assets_folder=STATIC_DIR
)

# User class for Flask-Login that doesn't require Firebase Admin SDK
class User(UserMixin):
    def __init__(self, uid, username, email):
        self.id = uid
        self.username = username
        self.email = email
        
    @staticmethod
    def get_user_info_from_session():
        # This creates a user from session information
        if 'user_id' in session and 'user_email' in session and 'user_name' in session:
            return User(
                uid=session['user_id'],
                username=session['user_name'],
                email=session['user_email']
            )
        return None

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "login"

# Load ML model
try:
    model = joblib.load(MODEL_PATH)
    logger.info("ML model loaded successfully")
except FileNotFoundError:
    logger.error(f"Model file not found at: {MODEL_PATH}")
    raise

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Load a user from session."""
    return User.get_user_info_from_session()

@server.route("/")
def home():
    return render_template("home.html")

@server.route("/about")
def about():
    return render_template("about.html")

@server.route("/contact")
def contact():
    return render_template("contact.html")

@server.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login without Firebase Admin SDK."""
    if current_user.is_authenticated:
        return redirect("/dashboard")
        
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username", email.split('@')[0] if email else "User")
        user_id = request.form.get("firebase_uid", f"user_{hash(email)}")
        
        # Store user info in session
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = username
        
        # Create and login the user
        user = User(uid=user_id, username=username, email=email)
        login_user(user)
        
        flash("Login successful!", "success")
        return redirect("/dashboard")
    
    return render_template("login.html", firebase_config=firebase_config)

@server.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration without Firebase Admin SDK."""
    if current_user.is_authenticated:
        return redirect("/dashboard")
        
    if request.method == "POST":
        # The client-side Firebase SDK handles all the registration logic
        # We just show a success message
        flash(
            "Registration successful! A verification email has been sent to your email address. "
            "Please verify your email before logging in.", 
            "success"
        )
        
        return redirect("/login")
    
    return render_template("register.html", firebase_config=firebase_config)

@server.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    # Clear the session
    session.clear()
    return redirect("/login")

@server.route("/reset-password", methods=["POST"])
def reset_password():
    """Send password reset email using Firebase client SDK only."""
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"success": False, "error": "Email is required"})
            
        # The actual password reset is handled by the Firebase client SDK
        # Just return success
        return jsonify({
            "success": True, 
            "message": "Password reset email sent"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def create_risk_gauge(risk_probability: float) -> dcc.Graph:
    """Create a modern gauge chart for risk probability visualization."""
    threshold_value = 70
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_probability * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        delta={'reference': threshold_value, 'increasing': {'color': "#EF4444"}, 'decreasing': {'color': "#10B981"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#E5E7EB", 'visible': True},
            'bar': {'color': "rgba(255, 255, 255, 0)"},
            'bgcolor': "#F9FAFB",
            'borderwidth': 2,
            'bordercolor': "#E5E7EB",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.7)'},  # Green
                {'range': [30, 70], 'color': 'rgba(249, 115, 22, 0.7)'},  # Orange
                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.7)'}   # Red
            ],
            'threshold': {
                'line': {'color': "#6366F1", 'width': 4},
                'thickness': 0.75,
                'value': threshold_value
            }
        },
        title={
            'text': "Outbreak Risk Assessment",
            'font': {'size': 24, 'color': '#4F46E5', 'family': "'Poppins', sans-serif"}
        },
        number={'font': {'size': 40, 'color': '#4F46E5', 'family': "'Poppins', sans-serif"}, 'suffix': '%'}
    ))
    
    # Add custom shapes to make it more visually appealing
    fig.add_shape(
        type="circle",
        xref="paper", yref="paper",
        x0=0.485, y0=0.485, x1=0.515, y1=0.515,
        fillcolor="#6366F1",
        line_color="#6366F1",
    )
    
    risk_level = "LOW" if risk_probability < 0.3 else "MODERATE" if risk_probability < 0.7 else "CRITICAL"
    risk_color = "#10B981" if risk_probability < 0.3 else "#F59E0B" if risk_probability < 0.7 else "#EF4444"
    
    fig.add_annotation(
        xref="paper", yref="paper", x=0.5, y=0.25,
        text=f"Risk Level: <b>{risk_level}</b>",
        showarrow=False,
        font=dict(family="'Poppins', sans-serif", size=18, color=risk_color)
    )
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

def create_trend_chart(historical_data: pd.DataFrame) -> dcc.Graph:
    """Create a modern line chart for historical trend visualization."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add risk level area
    fig.add_trace(
        go.Scatter(
            x=historical_data['date'],
            y=historical_data['risk_level'],
            name="Risk Level",
            line=dict(color='rgba(99, 102, 241, 0.9)', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ),
        secondary_y=False
    )
    
    # Add cases bar chart
    fig.add_trace(
        go.Bar(
            x=historical_data['date'],
            y=historical_data['new_cases'],
            name="New Cases",
            marker_color='rgba(129, 140, 248, 0.7)',
            opacity=0.8
        ),
        secondary_y=True
    )
    
    # Add moving average of risk level
    moving_avg = historical_data['risk_level'].rolling(window=3).mean()
    fig.add_trace(
        go.Scatter(
            x=historical_data['date'],
            y=moving_avg,
            name="Risk Trend (3-day MA)",
            line=dict(color='rgba(139, 92, 246, 0.9)', width=2, dash='dot'),
            visible='legendonly'  # Hidden by default
        ),
        secondary_y=False
    )
    
    # Add projections
    last_date = historical_data['date'].iloc[-1]
    forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=7)
    forecast_risk = historical_data['risk_level'].iloc[-7:].mean() * np.ones(7) * 1.1  # Simple projection
    forecast_risk = np.clip(forecast_risk, 0, 1)  # Ensure values are between 0 and 1
    
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_risk,
            name="Risk Projection (7 days)",
            line=dict(color='rgba(167, 139, 250, 0.7)', width=2, dash='dash'),
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(167, 139, 250, 0.1)'
        ),
        secondary_y=False
    )
    
    fig.update_layout(
        title={
            'text': 'Historical Trend Analysis',
            'font': {'family': "'Poppins', sans-serif", 'size': 24, 'color': '#4F46E5'},
            'y': 0.95
        },
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'center',
            'x': 0.5,
            'bgcolor': 'rgba(255, 255, 255, 0.8)',
            'bordercolor': 'rgba(0, 0, 0, 0.1)',
            'borderwidth': 1
        },
        hovermode='x unified',
        hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.9)', font_size=12, font_family="'Poppins', sans-serif"),
        height=500,
        margin=dict(l=20, r=20, t=100, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 0, 0, 0.03)',
            title='Date',
            titlefont=dict(family="'Poppins', sans-serif", size=14)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 0, 0, 0.03)',
            title='Risk Level',
            titlefont=dict(family="'Poppins', sans-serif", size=14),
            tickformat='.0%'
        ),
        yaxis2=dict(
            showgrid=False,
            title='New Cases',
            titlefont=dict(family="'Poppins', sans-serif", size=14)
        )
    )
    
    # Add annotation for projection zone
    fig.add_shape(
        type="rect",
        xref="x",
        yref="paper",
        x0=last_date,
        y0=0,
        x1=forecast_dates[-1],
        y1=1,
        fillcolor="rgba(200, 200, 200, 0.05)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_annotation(
        xref="x",
        yref="paper",
        x=last_date + (forecast_dates[-1] - last_date) / 2,
        y=0.95,
        text="Projection Zone",
        showarrow=False,
        font=dict(family="'Poppins', sans-serif", size=12, color="rgba(79, 70, 229, 0.7)")
    )
    
    return dcc.Graph(
        figure=fig, 
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )

def create_input_field(id_name: str, label: str, placeholder: str = "") -> html.Div:
    """Create a standardized input field with label."""
    return html.Div([
        html.Label(label, style={"color": "#333"}),
        dcc.Input(
            id=id_name,
            type="number",
            placeholder=placeholder,
            style={
                "marginBottom": "10px",
                "width": "100%",
                "padding": "8px",
                "borderRadius": "4px",
                "border": "1px solid #ddd"
            }
        )
    ])

def create_prediction_card(prediction_details: Dict) -> dbc.Card:
    """Create a modern prediction card with visual elements."""
    risk_color = "#EF4444" if prediction_details['risk_level'] == "High" else "#10B981"
    risk_icon = "fas fa-exclamation-triangle" if prediction_details['risk_level'] == "High" else "fas fa-check-circle"
    
    return dbc.Card([
        dbc.CardHeader(
            [
                html.I(className=f"{risk_icon} mr-2"),
                "Detailed Risk Analysis Report"
            ],
            className="d-flex align-items-center",
            style={
                "backgroundColor": risk_color,
                "color": "white",
                "fontSize": "1.25rem",
                "fontWeight": "bold",
                "padding": "15px 20px",
                "borderRadius": "15px 15px 0 0"
            }
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
            html.Div([
                        html.H2(
                            f"{prediction_details['risk_level']} Risk",
                            className="text-center mb-2",
                            style={"color": risk_color, "fontWeight": "bold"}
                        ),
                        html.Div([
                            html.Span("Confidence Score", 
                                    className="d-block text-muted small mb-1"),
                            html.Div([
                                html.Span(
                                    f"{prediction_details['confidence']:.1f}%", 
                                    style={
                                        "fontSize": "1.8rem", 
                                        "fontWeight": "bold",
                                        "color": "#4F46E5"
                                    }
                                )
                            ], className="d-flex justify-content-center")
                        ], className="text-center p-3 mb-3", style={
                            "backgroundColor": "#F9FAFB",
                            "borderRadius": "10px",
                            "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"
                        })
                    ])
                ], md=4),
                dbc.Col([
                    html.Div([
                        html.H5("Key Risk Factors", 
                              className="mb-3", 
                              style={"color": "#4F46E5", "fontWeight": "bold"}),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-arrow-circle-up mr-2", 
                                      style={"color": "#EF4444" if "high" in value.lower() else "#10B981"}),
                                html.Span(factor, className="text-muted small mr-2"),
                                html.Span(value, style={"fontWeight": "bold"})
                            ], className="d-flex align-items-center mb-3")
                    for factor, value in prediction_details['key_factors'].items()
                        ])
                    ], className="p-3", style={
                        "backgroundColor": "#F9FAFB",
                        "borderRadius": "10px",
                        "height": "100%",
                        "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"
                    })
                ], md=8)
            ], className="mb-4"),
            html.Div([
                html.H5(
                    "Recommended Actions",
                    className="mb-3",
                    style={"color": "#4F46E5", "fontWeight": "bold"}
                ),
                html.Div(
                    prediction_details['recommendation'],
                    style={
                        "borderRadius": "10px",
                        "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"
                    }
                )
            ], className="mt-2")
        ], style={"padding": "25px"})
    ], className="shadow-sm border-0", style={"borderRadius": "15px"})

def predict_outbreak(new_cases: float, humidity: float, population_density: float,
                    temperature: float, rainfall: float, vaccination_rate: float = None) -> str:
    """Make prediction using the loaded model."""
    try:
        # Base prediction using the model
        prediction = model.predict([[
            new_cases,
            humidity,
            population_density,
            temperature,
            rainfall
        ]])[0]
        
        # If vaccination rate is provided, adjust prediction
        if vaccination_rate is not None:
            # Simple adjustment: high vaccination rates reduce risk
            # This is a simplified approach - in a real model, this would be more sophisticated
            if vaccination_rate > 70 and prediction == 1:
                # If vaccination is high, there's a chance to reduce high risk to low
                if np.random.random() < (vaccination_rate - 70) / 30:
                    prediction = 0
            elif vaccination_rate < 40 and prediction == 0:
                # If vaccination is low, there's a chance to increase low risk to high
                if np.random.random() < (40 - vaccination_rate) / 40:
                    prediction = 1
        
        return "High" if prediction == 1 else "Low"
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise

def get_recommendation(risk_level: str, probability: float) -> str:
    """Generate detailed recommendations based on risk level and probability."""
    
    # High Risk + High Confidence (Immediate Action)
    if risk_level == "High" and probability > 0.7:
        return html.Div([
            html.H5("🚨 CRITICAL RISK: IMMEDIATE ACTION REQUIRED", className="text-danger"),
            html.Ul([
                html.Li("Enforce strict lockdowns in affected areas"),
                html.Li("Mobilize emergency medical teams"),
                html.Li("Establish field hospitals"),
                html.Li("Mandate N95 masks in public"),
                html.Li("Deploy contact tracing at maximum capacity"),
                html.Li("Suspend public gatherings >10 people")
            ], style={"color": "#374151"}),
            html.P("Trigger Condition: Risk >70% with high transmission factors", 
                  className="text-muted mt-2", 
                  style={"fontSize": "0.9rem"})
        ], style={"backgroundColor": "#FEF2F2", "padding": "15px", "borderRadius": "10px", "border": "1px solid #FECACA"})
    
    # High Risk + Moderate Confidence (Warning)
    elif risk_level == "High":
        return html.Div([
            html.H5("⚠️ ELEVATED RISK: PREPARE RESPONSE", className="text-warning"),
            html.Ul([
                html.Li("Activate outbreak response teams"),
                html.Li("Stockpile PPE and ventilators"),
                html.Li("Increase ICU capacity by 50%"),
                html.Li("Launch public awareness campaigns"),
                html.Li("Test wastewater for viral load"),
                html.Li("Prepare quarantine facilities")
            ], style={"color": "#374151"}),
            html.P("Trigger Condition: Risk >50% with environmental triggers", 
                  className="text-muted mt-2", 
                  style={"fontSize": "0.9rem"})
        ], style={"backgroundColor": "#FFFBEB", "padding": "15px", "borderRadius": "10px", "border": "1px solid #FEF3C7"})
    
    # Low Risk + Very Low Confidence (Monitor)
    elif risk_level == "Low" and probability < 0.3:
        return html.Div([
            html.H5("✅ LOW RISK: ROUTINE MONITORING", className="text-success"),
            html.Ul([
                html.Li("Maintain standard surveillance"),
                html.Li("Keep 30-day medical supplies"),
                html.Li("Conduct monthly drills"),
                html.Li("Update pandemic playbooks"),
                html.Li("Monitor zoonotic hotspots"),
                html.Li("Vaccinate high-risk groups")
            ], style={"color": "#374151"}),
            html.P("Trigger Condition: Risk <30% with stable indicators", 
                  className="text-muted mt-2", 
                  style={"fontSize": "0.9rem"})
        ], style={"backgroundColor": "#ECFDF5", "padding": "15px", "borderRadius": "10px", "border": "1px solid #D1FAE5"})
    
    # Default Caution (Vigilance)
    else:
        return html.Div([
            html.H5("🔍 MODERATE RISK: ENHANCED VIGILANCE", className="text-primary"),
            html.Ul([
                html.Li("Increase testing by 20%"),
                html.Li("Audit hospital readiness"),
                html.Li("Pre-position supplies"),
                html.Li("Train contact tracers"),
                html.Li("Accelerate vaccine research"),
                html.Li("Model outbreak scenarios")
            ], style={"color": "#374151"}),
            html.P("Trigger Condition: Uncertain risk factors present", 
                  className="text-muted mt-2", 
                  style={"fontSize": "0.9rem"})
        ], style={"backgroundColor": "#EEF2FF", "padding": "15px", "borderRadius": "10px", "border": "1px solid #E0E7FF"})

# Dash Layout
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div(id="page-content", style={
        "padding": "20px",
        "backgroundColor": "#f9fafb",
        "minHeight": "100vh",
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "flex-start"
    }),
    html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    ),
    # Add link to our loading CSS
    html.Link(
        rel="stylesheet",
        href="/assets/loading.css"
    ),
    # Add Google Fonts
    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Montserrat:wght@400;500;600;700&display=swap"
    ),
    # Loading overlay div
    html.Div(
        id="loading-container",
        style={"display": "none", "width": "100%", "height": "100%", "position": "fixed", "top": 0, "left": 0, "zIndex": 9999}
    ),
    # Store for tracking analysis state
    dcc.Store(id="progress-store", data={'step': 0}),
    # Interval for updating progress
    dcc.Interval(
        id="loading-interval",
        interval=4000,  # 4 seconds between updates
        n_intervals=0,
        disabled=True
    )
])

def create_dashboard():
    # Custom styles for number inputs - ensure arrows are visible
    number_input_style = {
        "borderRadius": "10px",
        "padding": "12px 15px 12px 15px",
        "border": "1px solid rgba(99, 102, 241, 0.2)",
        "boxShadow": "0 2px 5px rgba(0, 0, 0, 0.02)",
        # Add padding on the right to prevent icon overlap with up/down arrows
        "paddingRight": "40px",
        # Make sure input has room for spinners
        "width": "100%",
        "height": "45px",
        "fontFamily": "'Poppins', sans-serif",
        "backgroundColor": "rgba(255, 255, 255, 0.9)",
        "color": "#4B5563",
        "transition": "all 0.3s ease"
    }
    
    # Position for icons to avoid overlapping with spinners
    icon_style = {
        "right": "15px", 
        "top": "40px", 
        "opacity": "0.5",
        "zIndex": "1"  # Ensure icon is above the input
    }
    
    return html.Div([
        dbc.Container([
            # Navigation Bar
            dbc.Navbar(
                [
                    dbc.Container(
                        [
                            html.A(
                                dbc.Row(
                                    [
                                        dbc.Col(html.I(className="fas fa-virus-covid", style={"color": "#6366F1", "fontSize": "1.8rem"})),
                                        dbc.Col(dbc.NavbarBrand("Disease Outbreak Prediction", className="ml-2", style={"fontFamily": "'Montserrat', sans-serif", "fontWeight": "600", "letterSpacing": "0.5px"})),
                                    ],
                                    align="center",
                                    className="g-0",
                                ),
                                href="/dashboard",
                                style={"textDecoration": "none"},
                            ),
                            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                            dbc.Collapse(
                                dbc.Nav(
                                    [
                                        dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", active=True, style={"fontFamily": "'Poppins', sans-serif", "fontWeight": "500"})),
                                        # Logout button removed from header
                                    ],
                                    className="ml-auto",
                                    navbar=True,
                                ),
                                id="navbar-collapse",
                                is_open=False,
                                navbar=True,
                            ),
                        ]
                    ),
                ],
                color="white",
                light=True,
                className="mb-5 shadow-sm navbar-enhanced",
                style={"borderRadius": "15px"}
            ),
            
            # Header Row with modern clean design
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Add decorative elements
                        html.Div(className="header-decoration-left"),
                        html.Div(className="header-decoration-right"),
                        
                        html.H1(
                            [
                                html.I(className="fas fa-virus-covid mr-2", style={"color": "#ffffff"}),
                                " Welcome, ",
                                html.Span(
                                    current_user.username,
                                    className="username-highlight",
                                    id="username-display"
                                ),
                                "!"
                            ],
                            className="text-center mb-4",
                            style={
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "700",
                                "letterSpacing": "1px",
                                "color": "#ffffff",
                                "position": "relative",
                                "zIndex": "2"
                            }
                        ),
                        html.P(
                            "Disease Outbreak Detection System",
                            className="text-center mb-4",
                            style={
                                "fontSize": "1.2rem", 
                                "opacity": "0.9", 
                                "color": "#ffffff", 
                                "fontFamily": "'Poppins', sans-serif", 
                                "fontWeight": "300", 
                                "letterSpacing": "0.5px",
                                "position": "relative",
                                "zIndex": "2"
                            }
                        ),
                        # Add subtle particle effect
                        html.Div(className="particles")
                    ], className="py-5 px-4 header-gradient", style={
                        "borderRadius": "15px",
                        "boxShadow": "0 10px 25px rgba(99, 102, 241, 0.2)",
                        "position": "relative",
                        "overflow": "hidden"
                    })
                ], width=12)
            ], className="mb-5"),

            # Input Form Row with updated styles
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            [
                                html.I(className="fas fa-chart-line mr-2", 
                                      style={"color": "#6366F1"}),
                                "Risk Analysis Parameters"
                            ],
                            className="h4 d-flex align-items-center",
                            style={
                                "background": "linear-gradient(45deg, #6366F1, #8B5CF6)",
                                "color": "white",
                                "borderRadius": "15px 15px 0 0",
                                "border": "none",
                                "padding": "20px",
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "600",
                                "letterSpacing": "0.5px"
                            }
                        ),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Label("New Cases", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="new-cases",
                                            type="number",
                                            placeholder="e.g., 150",
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-virus input-icon")
                                    ], className="input-group")
                                ], md=6),
                                dbc.Col([
                                    html.Div([
                                        html.Label("Humidity (%)", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="humidity",
                                            type="number",
                                            placeholder="e.g., 65",
                                            min=0,
                                            max=100,
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-tint input-icon")
                                    ], className="input-group")
                                ], md=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Label("Population Density", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="population-density",
                                            type="number",
                                            placeholder="e.g., 200",
                                            min=0,
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-users input-icon")
                                    ], className="input-group")
                                ], md=6),
                                dbc.Col([
                                    html.Div([
                                        html.Label("Temperature (°C)", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="temperature",
                                            type="number",
                                            placeholder="e.g., 28",
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-thermometer-half input-icon")
                                    ], className="input-group")
                                ], md=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Label("Rainfall (mm)", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="rainfall",
                                            type="number",
                                            placeholder="e.g., 120",
                                            min=0,
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-cloud-rain input-icon")
                                    ], className="input-group")
                                ], md=6),
                                dbc.Col([
                                    html.Div([
                                        html.Label("Vaccination Rate (%)", className="input-label", 
                                                 style={"marginLeft": "8px"}),
                                        dcc.Input(
                                            id="vaccination-rate",
                                            type="number",
                                            placeholder="e.g., 75",
                                            min=0,
                                            max=100,
                                            className="form-control form-control-enhanced",
                                            style=number_input_style
                                        ),
                                        html.I(className="fas fa-syringe input-icon")
                                    ], className="input-group")
                                ], md=6)
                            ]),
                            
                            # Updated analyze button
                            dbc.Button(
                                [
                                    html.I(className="fas fa-biohazard mr-2"),
                                    "Analyze Outbreak Risk"
                                ],
                                id="predict-button",
                                color="primary",
                                className="w-100 mt-3 py-3 btn-gradient",
                                style={
                                    "fontSize": "1.1rem",
                                    "fontFamily": "'Poppins', sans-serif",
                                    "fontWeight": "600",
                                    "letterSpacing": "0.5px",
                                    "borderRadius": "10px"
                                }
                            )
                            
                        ], style={"backgroundColor": "#ffffff", "borderRadius": "0 0 15px 15px", "padding": "25px"})
                    ], className="border-0 shadow-sm card-enhanced", style={"borderRadius": "15px"})
                ], md=10, sm=12, className="mx-auto")
            ], className="mb-5 justify-content-center"),

            # Prediction Output Row with Animated Cards
            dbc.Row([
                dbc.Col([
                    html.Div(
                        id="prediction-output",
                        className="mb-5",
                        style={"minHeight": "400px"}
                    )
                ], width=12)
            ], className="justify-content-center"),
            
            # AI Health Assistant Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            [
                                html.I(className="fas fa-robot mr-2", 
                                      style={"color": "#ffffff"}),
                                "AI Health Assistant"
                            ],
                            className="h4 d-flex align-items-center",
                            style={
                                "background": "linear-gradient(45deg, #10B981, #059669)",
                                "color": "white",
                                "borderRadius": "15px 15px 0 0",
                                "border": "none",
                                "padding": "20px",
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "600",
                                "letterSpacing": "0.5px"
                            }
                        ),
                        dbc.CardBody([
                            html.P(
                                "Describe your symptoms, and I'll help identify possible conditions. For educational purposes only - always consult a healthcare professional.",
                                className="mb-3",
                                style={"color": "#4B5563"}
                            ),
                            
                            # Symptom chips
                            html.Div([
                                html.Div("Fever", id="chip-fever", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                                html.Div("Cough", id="chip-cough", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                                html.Div("Headache", id="chip-headache", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                                html.Div("Fatigue", id="chip-fatigue", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                                html.Div("Sore throat", id="chip-sore-throat", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                                html.Div("Nausea", id="chip-nausea", className="symptom-chip", 
                                       style={
                                           "background": "rgba(16, 185, 129, 0.1)",
                                           "color": "#059669", 
                                           "padding": "8px 15px",
                                           "borderRadius": "20px",
                                           "display": "inline-block",
                                           "margin": "0 8px 8px 0",
                                           "fontSize": "14px",
                                           "cursor": "pointer",
                                           "transition": "all 0.3s ease",
                                           "border": "1px solid rgba(16, 185, 129, 0.2)"
                                       }),
                            ], className="mb-4"),
                            
                            # Chat messages container
                            html.Div([
                                html.Div(
                                    "Hello! I'm your health assistant. I can help identify possible conditions based on your symptoms. What symptoms are you experiencing?",
                                    className="bot-message mb-3",
                                    style={
                                        "background": "rgba(16, 185, 129, 0.1)",
                                        "padding": "12px 15px",
                                        "borderRadius": "15px",
                                        "borderBottomLeftRadius": "0",
                                        "maxWidth": "80%",
                                        "alignSelf": "flex-start",
                                        "fontSize": "14px",
                                        "color": "#1F2937"
                                    }
                                )
                            ], id="chat-messages", className="chat-messages", style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "250px",
                                "overflowY": "auto",
                                "marginBottom": "15px",
                                "padding": "10px",
                                "background": "rgba(249, 250, 251, 0.5)",
                                "borderRadius": "10px"
                            }),
                            
                            # Chat input
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(
                                        id="chat-input",
                                        placeholder="Type your symptoms here...",
                                        style={
                                            "background": "rgba(249, 250, 251, 0.5)",
                                            "border": "1px solid rgba(16, 185, 129, 0.3)",
                                            "borderRadius": "10px",
                                            "padding": "12px 15px",
                                            "boxShadow": "0 2px 5px rgba(0, 0, 0, 0.05)"
                                        }
                                    )
                                ], width=10),
                                dbc.Col([
                                    dbc.Button(
                                        html.I(className="fas fa-paper-plane"),
                                        id="send-message-button",
                                        color="success",
                                        style={
                                            "width": "100%",
                                            "borderRadius": "10px",
                                            "background": "linear-gradient(45deg, #10B981, #059669)",
                                            "border": "none"
                                        }
                                    )
                                ], width=2)
                            ])
                        ], style={"backgroundColor": "#ffffff", "borderRadius": "0 0 15px 15px", "padding": "25px"})
                    ], className="border-0 shadow-sm card-enhanced", style={"borderRadius": "15px"})
                ], md=8, className="mx-auto mb-5")
            ], className="justify-content-center"),

            # Historical Trend Row with updated style
            dbc.Row([
                dbc.Col([
                    html.Div(
                        id="historical-trend",
                        className="mb-5 p-4",
                        style={
                            "background": "linear-gradient(135deg, #F5F7FF, #EEF2FF)",
                            "borderRadius": "15px",
                            "boxShadow": "0 10px 15px rgba(99, 102, 241, 0.1)"
                        }
                    )
                ], width=12)
            ], className="justify-content-center"),

            # Footer with updated style
            dbc.Row([
                dbc.Col([
                    html.Hr(style={"borderColor": "#E5E7EB"}),
                    html.Div([
                        html.A(
                            [
                                html.I(className="fas fa-sign-out-alt mr-2"),
                                "Logout"
                            ],
                            href="/logout",
                            className="btn btn-outline-primary btn-lg",
                            style={
                                "width": "200px",
                                "transition": "all 0.3s ease",
                                "boxShadow": "0 0 10px rgba(99, 102, 241, 0.1)",
                                "borderRadius": "50px",
                                "borderColor": "#6366F1",
                                "color": "#6366F1",
                                "fontFamily": "'Poppins', sans-serif",
                                "fontWeight": "500"
                            }
                        )
                    ], className="text-center")
                ], width=12)
            ], className="mt-5")
        ], fluid=True, style={"maxWidth": "1400px"})
    ], style={"backgroundColor": "#f9fafb", "minHeight": "100vh", "fontFamily": "'Poppins', sans-serif"})

# Add hover effects and transitions to buttons in callback
@app.callback(
    Output("predict-button", "style"),
    [Input("predict-button", "n_clicks")]
)
def animate_button(n_clicks):
    if n_clicks:
        return {
            "transform": "scale(0.95)",
            "boxShadow": "0 2px 5px rgba(99, 102, 241, 0.2)",
            "fontSize": "1.1rem",
            "fontFamily": "'Poppins', sans-serif",
            "fontWeight": "600",
            "letterSpacing": "0.5px",
            "borderRadius": "10px"
        }
    return {
        "boxShadow": "0 4px 15px rgba(99, 102, 241, 0.3)",
        "fontSize": "1.1rem",
        "fontFamily": "'Poppins', sans-serif",
        "fontWeight": "600",
        "letterSpacing": "0.5px",
        "borderRadius": "10px"
    }

@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname == "/dashboard":
        if not current_user.is_authenticated:
            return dcc.Location(id='redirect', href="/login")
        return create_dashboard()
    return dcc.Location(id='redirect', href="/login")

# Create loading overlay content when button is clicked
@app.callback(
    [
        Output("loading-container", "children"),
        Output("loading-container", "style"),
        Output("progress-store", "data", allow_duplicate=True)
    ],
    Input("predict-button", "n_clicks"),
    State("progress-store", "data"),
    prevent_initial_call=True
)
def show_loading_overlay(n_clicks, progress_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    # Reset progress data
    progress_data = {'step': 0}
    
    # Create loading overlay content
    loading_content = html.Div(
        className="loading-overlay",
        children=[
            html.Div(
                className="loading-container",
                children=[
                    # Dots animation container
                    html.Div(
                        className="dots-container",
                        children=[
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                            html.Div(className="dot"),
                        ]
                    ),
                    html.Div(
                        className="loading-progress-container",
                        children=[
                            html.Div(
                                id="loading-progress-bar",
                                className="loading-progress-bar",
                                style={"width": "0%"}
                            )
                        ]
                    ),
                    html.P(id="loading-status", className="loading-status", children="Processing population density data...")
                ]
            )
        ]
    )
    
    # Show the loading overlay
    return loading_content, {"display": "block", "width": "100%", "height": "100%", "position": "fixed", "top": 0, "left": 0, "zIndex": 9999}, progress_data

# Update progress bar and status text
@app.callback(
    [
        Output("loading-progress-bar", "style"),
        Output("loading-status", "children"),
        Output("progress-store", "data")
    ],
    Input("loading-interval", "n_intervals"),
    State("progress-store", "data"),
    prevent_initial_call=True
)
def update_progress_bar(n_intervals, progress_data):
    if n_intervals is None:
        raise dash.exceptions.PreventUpdate
    
    steps = [
        {"width": "20%", "text": "Processing population density data..."},
        {"width": "40%", "text": "Analyzing environmental factors..."},
        {"width": "60%", "text": "Processing health metrics..."},
        {"width": "80%", "text": "Calculating risk probabilities..."},
        {"width": "95%", "text": "Finalizing prediction..."}
    ]
    
    if n_intervals < len(steps):
        progress_data['step'] = n_intervals
        return {"width": steps[n_intervals]["width"]}, steps[n_intervals]["text"], progress_data
    else:
        progress_data['step'] = len(steps)
        return {"width": "100%"}, "Analysis complete", progress_data

# Enable/disable interval and handle completion
@app.callback(
    [
        Output("loading-interval", "disabled"),
        Output("loading-container", "style", allow_duplicate=True)
    ],
    [Input("predict-button", "n_clicks"),
     Input("loading-interval", "n_intervals")],
    [State("progress-store", "data")],
    prevent_initial_call=True
)
def toggle_interval_and_overlay(n_clicks, n_intervals, progress_data):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Start interval when button is clicked
    if trigger_id == "predict-button" and n_clicks:
        return False, {"display": "block", "width": "100%", "height": "100%", "position": "fixed", "top": 0, "left": 0, "zIndex": 9999}
    
    # Stop interval and hide overlay when complete (after 5 intervals = 20 seconds)
    if trigger_id == "loading-interval" and n_intervals is not None and n_intervals >= 5:
        return True, {"display": "none"}
    
    raise dash.exceptions.PreventUpdate

# Modify the update_dashboard callback
@app.callback(
    [
        Output("prediction-output", "children"),
        Output("historical-trend", "children")
    ],
    Input("loading-interval", "n_intervals"),
    [
        State("new-cases", "value"),
        State("humidity", "value"),
        State("population-density", "value"),
        State("temperature", "value"),
        State("rainfall", "value"),
        State("vaccination-rate", "value"),
        State("progress-store", "data")
    ],
    prevent_initial_call=True
)
def update_dashboard(n_intervals, new_cases, humidity, population_density, temperature, rainfall, vaccination_rate, progress_data):
    # Only process when we reach the last interval
    if n_intervals is None or n_intervals < 5:  # 5 intervals = 20 seconds
        raise dash.exceptions.PreventUpdate
    
    try:
        # Validate inputs
        parameters = {
            'New Cases': new_cases,
            'Humidity': humidity,
            'Population Density': population_density,
            'Temperature': temperature,
            'Rainfall': rainfall,
            'Vaccination Rate': vaccination_rate
        }
        
        if any(v is None for v in parameters.values()):
            missing_fields = [k for k, v in parameters.items() if v is None]
            return dbc.Alert(
                f"Please enter values for: {', '.join(missing_fields)}",
                color="warning"
            ), ""
        
        # Make prediction
        risk_level = predict_outbreak(new_cases, humidity, population_density, temperature, rainfall, vaccination_rate)
        
        # Calculate confidence and risk probability 
        confidence = np.random.uniform(75, 95) 
        # Adjust risk probability based on vaccination rate
        risk_probability = 0.8 if risk_level == "High" else 0.2  
        if vaccination_rate is not None:
            # Reduce risk probability as vaccination rate increases
            risk_probability *= max(0.2, (100 - vaccination_rate) / 100)
        
        # Generate prediction details
        prediction_details = {
            'risk_level': risk_level,
            'confidence': confidence,
            'key_factors': {
                'Population Density Impact': f"{population_density:.1f} people/km²",
                'Environmental Risk': f"{(humidity * temperature / 100):.1f}",
                'Current Spread Rate': f"{(new_cases / population_density):.2f}",
                'Vaccination Coverage': f"{vaccination_rate:.1f}%"
            },
            'recommendation': get_recommendation(risk_level, risk_probability)
        }
        
        # Generate sample historical data (replace with actual data)
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        historical_data = pd.DataFrame({
            'date': dates,
            'risk_level': np.random.uniform(0, 1, 30),
            'new_cases': np.random.normal(new_cases, new_cases*0.1, 30)
        })
        
        # Create prediction output
        prediction_output = dbc.Container([
            dbc.Row([
                dbc.Col([
                    create_risk_gauge(risk_probability)
                ], md=6, sm=12),
                dbc.Col([
                    create_prediction_card(prediction_details)
                ], md=6, sm=12)
            ]),
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Button(
                            "Return to Dashboard",
                            color="primary",
                            className="mt-3 btn-gradient",
                            style={
                                "fontFamily": "'Poppins', sans-serif",
                                "fontWeight": "500"
                            }
                        ),
                        href="/dashboard"
                    )
                ])
            ])
        ])
        
        # Create historical trend
        trend_output = create_trend_chart(historical_data)
        
        return prediction_output, trend_output
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return dbc.Alert(
            "An error occurred during prediction. Please try again.",
            color="danger"
        ), ""

# Define the disease database for the chatbot
disease_database = {
    'covid-19': {
        'symptoms': ['fever', 'cough', 'fatigue', 'shortness of breath', 'loss of taste', 'loss of smell', 'sore throat', 'headache', 'body aches'],
        'description': 'COVID-19 is a respiratory illness caused by the SARS-CoV-2 virus that can range from mild to severe.',
        'recommendation': 'Isolate yourself to prevent spread, rest, stay hydrated, and use over-the-counter medications for symptoms. Seek medical attention if you experience severe symptoms such as difficulty breathing.'
    },
    'influenza': {
        'symptoms': ['fever', 'cough', 'sore throat', 'body aches', 'headache', 'fatigue', 'chills', 'runny nose', 'congestion'],
        'description': 'Influenza (flu) is a contagious respiratory illness that can cause mild to severe illness and sometimes lead to hospitalization or death.',
        'recommendation': 'Rest, stay hydrated, and take over-the-counter medications for symptoms. Consider antiviral medications if diagnosed early. Seek medical attention if symptoms worsen.'
    },
    'common cold': {
        'symptoms': ['runny nose', 'sneezing', 'cough', 'sore throat', 'mild fatigue', 'congestion', 'mild headache'],
        'description': 'The common cold is a viral infection of your nose and throat caused by many different viruses.',
        'recommendation': 'Rest, stay hydrated, gargle with salt water for sore throat, and use over-the-counter decongestants or pain relievers as needed.'
    },
    'malaria': {
        'symptoms': ['fever', 'chills', 'headache', 'nausea', 'body aches', 'fatigue', 'sweating', 'vomiting', 'diarrhea'],
        'description': 'Malaria is a life-threatening disease caused by parasites transmitted through the bite of infected female Anopheles mosquitoes.',
        'recommendation': 'Seek immediate medical attention for proper diagnosis and treatment with antimalarial medications. Early treatment can prevent complications.'
    },
    'dengue fever': {
        'symptoms': ['high fever', 'severe headache', 'pain behind the eyes', 'joint and muscle pain', 'rash', 'nausea', 'vomiting', 'bleeding gums', 'fatigue'],
        'description': 'Dengue fever is a mosquito-borne tropical disease caused by the dengue virus, characterized by high fever and severe joint and muscle pain.',
        'recommendation': 'Seek immediate medical attention, especially if you develop severe abdominal pain, persistent vomiting, or signs of bleeding. Stay hydrated and rest.'
    },
    'strep throat': {
        'symptoms': ['sore throat', 'difficulty swallowing', 'fever', 'swollen lymph nodes', 'headache', 'red and swollen tonsils', 'white patches in throat'],
        'description': 'Strep throat is a bacterial infection that causes inflammation and pain in the throat, requiring antibiotic treatment.',
        'recommendation': 'See a doctor for proper diagnosis and antibiotic treatment. Rest, stay hydrated, and use pain relievers to manage symptoms.'
    },
    'gastroenteritis': {
        'symptoms': ['nausea', 'vomiting', 'diarrhea', 'stomach cramps', 'mild fever', 'fatigue', 'headache', 'loss of appetite'],
        'description': 'Gastroenteritis is an intestinal infection that causes inflammation of the stomach and intestines, resulting in diarrhea, vomiting and abdominal pain.',
        'recommendation': 'Stay hydrated by sipping clear fluids, gradually reintroduce bland foods, and seek medical attention if symptoms are severe or persist.'
    },
    'bronchitis': {
        'symptoms': ['cough', 'production of mucus', 'fatigue', 'shortness of breath', 'mild fever', 'chest discomfort', 'wheezing'],
        'description': 'Bronchitis is an inflammation of the lining of your bronchial tubes, which carry air to and from your lungs.',
        'recommendation': 'Rest, stay hydrated, use a humidifier, and take over-the-counter pain relievers. See a doctor if symptoms persist or worsen.'
    },
    'migraine': {
        'symptoms': ['severe headache', 'throbbing pain', 'nausea', 'vomiting', 'sensitivity to light', 'sensitivity to sound', 'visual disturbances', 'dizziness'],
        'description': 'Migraine is a neurological condition characterized by intense, debilitating headaches often accompanied by sensory disturbances.',
        'recommendation': 'Rest in a quiet, dark room, apply cold compresses, stay hydrated, and use over-the-counter pain relievers. Consult a doctor for recurring migraines.'
    },
    'sinusitis': {
        'symptoms': ['facial pain', 'nasal congestion', 'thick nasal discharge', 'reduced sense of smell', 'cough', 'fatigue', 'headache', 'ear pressure'],
        'description': 'Sinusitis is an inflammation or swelling of the tissue lining the sinuses, often caused by infection.',
        'recommendation': 'Use nasal saline sprays, inhale steam, apply warm compresses to face, and take over-the-counter decongestants. See a doctor if symptoms last longer than 10 days.'
    },
    'allergic rhinitis': {
        'symptoms': ['sneezing', 'itchy nose', 'runny nose', 'congestion', 'itchy eyes', 'watery eyes', 'fatigue', 'postnasal drip'],
        'description': 'Allergic rhinitis is an allergic response to specific allergens, causing inflammation of the nose and upper respiratory tract.',
        'recommendation': 'Avoid known allergens, use antihistamines, nasal corticosteroids, or decongestants as recommended. Consider allergy testing if symptoms are severe or persistent.'
    },
    'urinary tract infection': {
        'symptoms': ['burning sensation during urination', 'frequent urination', 'cloudy urine', 'strong-smelling urine', 'pelvic pain', 'lower back pain', 'fever', 'fatigue'],
        'description': 'A urinary tract infection (UTI) is an infection in any part of the urinary system, including kidneys, bladder, ureters, and urethra.',
        'recommendation': 'See a doctor for antibiotics, drink plenty of water, avoid irritants like alcohol and caffeine, and use over-the-counter pain relievers for discomfort.'
    }
}

# Helper functions for the chatbot
def is_medical_query(message):
    """Check if the query is related to medical symptoms"""
    medical_terms = [
        'fever', 'cough', 'headache', 'pain', 'ache', 'sore', 'throat', 'runny', 'nose', 'sneeze', 'tired',
        'fatigue', 'nausea', 'vomit', 'diarrhea', 'rash', 'dizzy', 'breath', 'breathing', 'chest', 'stomach',
        'symptom', 'sick', 'illness', 'disease', 'infection', 'virus', 'bacterial', 'flu', 'cold', 'covid',
        'corona', 'health', 'medical', 'medicine', 'doctor', 'hospital', 'clinic', 'treatment', 'remedy',
        'diagnose', 'diagnosis', 'prescription', 'swollen', 'swelling', 'joint', 'muscle', 'bone', 'blood',
        'chill', 'temperature', 'pulse', 'heart', 'lung', 'organ', 'system', 'body', 'feel', 'feeling'
    ]
    
    message_lower = message.lower()
    return any(term in message_lower for term in medical_terms)

def generate_response(symptoms):
    """Generate a response based on the symptoms provided using enhanced matching"""
    if not symptoms:
        return "I need more information about your symptoms to help you. Could you please describe what you're experiencing?"
    
    # Find matching diseases with improved fuzzy matching
    matches = []
    symptom_words = set()
    for s in symptoms:
        # Add individual words from multi-word symptoms for better matching
        symptom_words.update(s.lower().split())
    
    for disease, data in disease_database.items():
        # Calculate matches at both the symptom level and word level
        direct_matches = [s for s in symptoms if any(s in ds or ds in s for ds in data['symptoms'])]
        
        # Word-level matching for better fuzzy matching
        disease_symptom_words = set()
        for ds in data['symptoms']:
            disease_symptom_words.update(ds.lower().split())
        
        word_match_count = len(symptom_words.intersection(disease_symptom_words))
        
        # Calculate a combined matching score
        if direct_matches or word_match_count > 0:
            direct_match_score = len(direct_matches) / len(data['symptoms']) if direct_matches else 0
            word_match_score = word_match_count / len(disease_symptom_words) if disease_symptom_words else 0
            
            # Combined score with more weight on direct matches
            combined_score = (direct_match_score * 0.7) + (word_match_score * 0.3)
            
            matches.append({
                'disease': disease,
                'data': data,
                'matching_symptoms': direct_matches,
                'match_score': combined_score
            })
    
    # Sort matches by score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    if not matches:
        return "Based on the symptoms you've described, I don't have enough information to suggest a specific condition. Please consult a healthcare professional for a proper diagnosis."
    
    # Generate response with top matches (up to 3)
    top_matches = matches[:3] if len(matches) > 2 else matches
    response = f"Based on your symptoms ({', '.join(symptoms)}), you might be experiencing:\n\n"
    
    for i, match in enumerate(top_matches):
        response += f"{i+1}. {match['disease'].upper()}: {match['data']['description']}\n"
        if match['matching_symptoms']:
            response += f"Matching symptoms: {', '.join(match['matching_symptoms'])}\n"
        response += f"Recommendation: {match['data']['recommendation']}\n\n"
    
    response += "IMPORTANT: This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation and treatment."
    
    return response

def get_chatgpt_response(symptoms, user_message):
    """Get a response from ChatGPT API based on the symptoms provided"""
    # If API is disabled, use local responses only
    if not USE_CHATGPT_API:
        return generate_response(symptoms)
        
    try:
        # If we can't get a response fast enough, fall back to local response
        # Use the local response first to provide instant feedback
        local_response = generate_response(symptoms)
        
        # Try to get a response from the API in a separate thread
        try:
            # Use a faster model with smaller token count
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use standard model with constraints for faster response
                messages=[
                    {"role": "system", "content": "You are a medical assistant. Be brief and concise."},
                    {"role": "user", "content": f"Symptoms: {', '.join(symptoms)}. What conditions match these symptoms? Be concise."}
                ],
                max_tokens=150,  # Reduced token count for faster response
                temperature=0.5,
                timeout=3.0  # 3 second timeout
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            return response_text
        except Exception as e:
            logger.warning(f"API response timed out or failed, using local fallback: {str(e)}")
            return local_response
            
    except Exception as e:
        logger.error(f"Error calling ChatGPT API: {str(e)}")
        # Fallback to the original implementation if the API call fails
        return generate_response(symptoms)

# Add callbacks for the chatbot functionality
@app.callback(
    [Output("chat-messages", "children"), Output("chat-input", "value")],
    [Input("send-message-button", "n_clicks"), 
     Input("chat-input", "n_submit")],
    [State("chat-input", "value"), 
     State("chat-messages", "children")],
    prevent_initial_call=True
)
def handle_chat_message(n_clicks, n_submit, message, current_messages):
    """Handle the chat message when the send button is clicked or Enter is pressed"""
    # Check if callback was triggered but no action was taken
    ctx = dash.callback_context
    if not ctx.triggered or (n_clicks is None and n_submit is None):
        raise dash.exceptions.PreventUpdate

    # If there's no message, don't update
    if not message or message.strip() == "":
        raise dash.exceptions.PreventUpdate
    
    user_message = message.strip()
    
    # Add the user message
    new_messages = current_messages + [
        html.Div(
            user_message,
            className="user-message mb-3",
            style={
                "background": "rgba(99, 102, 241, 0.1)",
                "padding": "12px 15px",
                "borderRadius": "15px",
                "borderBottomRightRadius": "0",
                "maxWidth": "80%",
                "alignSelf": "flex-end",
                "marginLeft": "auto",
                "fontSize": "14px",
                "color": "#1F2937"
            }
        )
    ]
    
    # Check if query is medical-related
    if not is_medical_query(user_message):
        bot_response = "I'm sorry, I can only help with health and symptom-related questions. Please describe your symptoms or ask health-related questions."
    else:
        # Extract symptoms from the message
        symptoms = [s.strip() for s in user_message.lower().split(',')]
        # Generate immediate response
        bot_response = generate_response(symptoms)
    
    # Add the bot's response immediately
    ai_response_div = html.Div(
        bot_response,
        className="bot-message mb-3",
        style={
            "background": "rgba(16, 185, 129, 0.1)",
            "padding": "12px 15px",
            "borderRadius": "15px",
            "borderBottomLeftRadius": "0",
            "maxWidth": "80%",
            "alignSelf": "flex-start",
            "whiteSpace": "pre-line",
            "fontSize": "14px",
            "color": "#1F2937"
        }
    )
    
    # Return immediately with both messages
    return new_messages + [ai_response_div], ""

# Handle symptom chip clicks
@app.callback(
    Output("chat-input", "value", allow_duplicate=True),
    [Input("chip-fever", "n_clicks"),
     Input("chip-cough", "n_clicks"),
     Input("chip-headache", "n_clicks"),
     Input("chip-fatigue", "n_clicks"),
     Input("chip-sore-throat", "n_clicks"),
     Input("chip-nausea", "n_clicks")],
    [State("chat-input", "value")],
    prevent_initial_call=True
)
def add_symptom_chip(n_fever, n_cough, n_headache, n_fatigue, n_sore_throat, n_nausea, current_value):
    """Add the selected symptom to the chat input when clicked"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    # Determine which button was clicked
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Map chip IDs to symptom names
    symptom_map = {
        "chip-fever": "Fever",
        "chip-cough": "Cough",
        "chip-headache": "Headache",
        "chip-fatigue": "Fatigue",
        "chip-sore-throat": "Sore throat",
        "chip-nausea": "Nausea"
    }
    
    # Get the symptom name
    symptom = symptom_map.get(trigger_id, "")
    
    if not symptom:
        raise dash.exceptions.PreventUpdate
    
    # Add symptom to the current input
    if current_value:
        return f"{current_value}, {symptom.lower()}"
    else:
        return symptom.lower()

if __name__ == "__main__":
    with server.app_context():
        pass  # No need for db.create_all() with Firebase
    
    logger.info("Starting the server with loading animation enabled...")
    app.run_server(debug=True)