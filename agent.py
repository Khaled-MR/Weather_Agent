"""
Agent Interface Module

This module provides a clean interface to the existing LangGraph-based
weather emergency response agent. It wraps the agent functionality
to make it easy to integrate with the FastAPI backend.

To use your actual agent, this module imports and calls the
run_weather_emergency_system function from Agents.py
"""

from typing import Dict, Any
import sys
import os

# Add current directory to path to import Agents module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the existing agent from Agents.py
    from Agents import run_weather_emergency_system
except ImportError:
    # Fallback to placeholder if import fails
    print("Warning: Could not import Agents.py. Using placeholder function.")
    run_weather_emergency_system = None


def run_agent(city: str) -> Dict[str, Any]:
    """
    Run the weather emergency response agent for a given city
    
    This function serves as a wrapper around the existing LangGraph agent.
    It processes the agent's output and returns a structured response.
    
    Args:
        city: Name of the city to analyze
        
    Returns:
        dict: Structured response containing:
            - weather_data: Current weather conditions
            - disaster_type: Identified disaster type
            - severity: Severity level (Critical, High, Medium, Low)
            - response: Emergency response plan
            - messages: Agent execution messages
            - alerts: Generated alerts
    """
    try:
        # Use the actual agent if available
        if run_weather_emergency_system is not None:
            # Call the existing agent function
            result = run_weather_emergency_system(city)
            
            # Extract and structure the response
            return {
                "city": result.get("city", city),
                "weather_data": result.get("weather_data", {}),
                "disaster_type": result.get("disaster_type", "No Immediate Threat"),
                "severity": result.get("severity", "Low"),
                "response": result.get("response", "No response plan generated"),
                "messages": [str(msg) for msg in result.get("messages", [])],
                "alerts": result.get("alerts", [])
            }
        else:
            # Placeholder function for testing without the actual agent
            return _placeholder_agent(city)
            
    except Exception as e:
        # Handle errors gracefully
        print(f"Error running agent for {city}: {str(e)}")
        return {
            "city": city,
            "weather_data": {
                "weather": "Error",
                "temperature": "N/A",
                "wind_speed": "N/A",
                "humidity": "N/A",
                "pressure": "N/A"
            },
            "disaster_type": "Analysis Error",
            "severity": "Unknown",
            "response": f"Error occurred during analysis: {str(e)}",
            "messages": [],
            "alerts": []
        }


def _placeholder_agent(city: str) -> Dict[str, Any]:
    """
    Placeholder agent function for testing
    
    This function simulates the agent's behavior when the actual
    agent is not available. Replace this with your actual agent call.
    
    Args:
        city: Name of the city to analyze
        
    Returns:
        dict: Simulated agent response
    """
    # Simulated response for testing
    return {
        "city": city,
        "weather_data": {
            "weather": "Clear sky",
            "temperature": 22.5,
            "wind_speed": 5.2,
            "humidity": 65,
            "pressure": 1013,
            "cloud_cover": 10
        },
        "disaster_type": "No Immediate Threat",
        "severity": "Low",
        "response": f"Current weather conditions in {city} are stable. No immediate emergency response required. Continue monitoring weather patterns.",
        "messages": ["Placeholder agent executed"],
        "alerts": []
    }


