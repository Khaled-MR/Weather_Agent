"""
Web-Friendly Agent Interface Module

This module provides a web-compatible interface to the LangGraph agent.
It handles human verification through the GUI instead of blocking terminal input.
"""

from typing import Dict, Any, Optional
import sys
import os
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage

# Add current directory to path to import Agents module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import necessary functions from Agents.py
    from Agents import (
        WeatherState, get_weather_data, analyze_disaster_type, 
        assess_severity, data_logging, emergency_response,
        civil_defense_response, public_works_response,
        send_email_alert, handle_no_approval, route_response,
        verify_approval_router
    )
except ImportError as e:
    print(f"Warning: Could not import from Agents.py: {e}")
    # Will use placeholder if import fails
    WeatherState = None


# Store pending verifications (in production, use a proper cache/database)
_pending_verifications = {}


def wait_for_approval(state: WeatherState) -> WeatherState:
    """
    Placeholder node that just returns the state when waiting for approval.
    This allows the workflow to stop here.
    """
    return state


def verify_approval_router_web(state: WeatherState):
    """
    Web-friendly router that handles pending approvals.
    If approval is pending (None), route to wait_for_approval to stop execution.
    """
    if state.get("needs_approval") and state.get("human_approved") is None:
        # Route to wait node to stop execution
        return "wait_for_approval"
    
    return "send_email_alert" if state.get('human_approved') else "handle_no_approval"


def get_human_verification_web(state: WeatherState) -> WeatherState:
    """
    Web-friendly version of human verification that doesn't block.
    Instead, it stores the state and returns a flag indicating approval is needed.
    """
    severity = state["severity"].strip().lower()
    
    if severity in ["low", "medium"]:
        # Store the state for later continuation
        import time
        verification_id = f"{state['city']}_{int(time.time() * 1000)}"
        _pending_verifications[verification_id] = state
        
        # Mark that approval is needed
        return {
            **state,
            "human_approved": None,  # None means pending
            "verification_id": verification_id,
            "needs_approval": True,
            "messages": state["messages"] + [
                SystemMessage(content="Human verification required for low/medium severity alert")
            ]
        }
    else:
        # Auto-approve for high/critical severity
        return {
            **state,
            "human_approved": True,
            "needs_approval": False,
            "messages": state["messages"] + [
                SystemMessage(content=f"Auto-approved {severity} severity alert")
            ]
        }


def continue_with_approval(verification_id: str, approved: bool) -> Dict[str, Any]:
    """
    Continue the agent workflow with the human approval decision.
    
    Args:
        verification_id: ID of the pending verification
        approved: Whether the user approved sending the email
        
    Returns:
        Final agent result
    """
    if verification_id not in _pending_verifications:
        raise ValueError(f"Verification ID {verification_id} not found")
    
    state = _pending_verifications[verification_id].copy()
    state["human_approved"] = approved
    state["needs_approval"] = False
    
    # Continue from verification step - route based on approval
    if approved:
        final_state = send_email_alert(state)
    else:
        final_state = handle_no_approval(state)
    
    # Clean up
    del _pending_verifications[verification_id]
    
    return final_state


def run_agent_web(city: str) -> Dict[str, Any]:
    """
    Run the weather emergency response agent for web interface.
    Stops before human verification if needed and returns a flag.
    
    Args:
        city: Name of the city to analyze
        
    Returns:
        dict: Structured response with a flag indicating if approval is needed
    """
    if WeatherState is None:
        return {
            "city": city,
            "weather_data": {},
            "disaster_type": "Error",
            "severity": "Unknown",
            "response": "Agent not available",
            "needs_approval": False,
            "verification_id": None
        }
    
    try:
        # Create web-friendly workflow
        workflow = StateGraph(WeatherState)
        
        # Add nodes
        workflow.add_node("get_weather", get_weather_data)
        workflow.add_node("analyze_disaster", analyze_disaster_type)
        workflow.add_node("assess_severity", assess_severity)
        workflow.add_node("data_logging", data_logging)
        workflow.add_node("emergency_response", emergency_response)
        workflow.add_node("civil_defense_response", civil_defense_response)
        workflow.add_node("public_works_response", public_works_response)
        workflow.add_node("get_human_verification", get_human_verification_web)
        workflow.add_node("wait_for_approval", wait_for_approval)
        workflow.add_node("send_email_alert", send_email_alert)
        workflow.add_node("handle_no_approval", handle_no_approval)
        
        # Add edges
        workflow.add_edge("get_weather", "analyze_disaster")
        workflow.add_edge("analyze_disaster", "assess_severity")
        workflow.add_edge("assess_severity", "data_logging")
        workflow.add_conditional_edges("data_logging", route_response)
        workflow.add_edge("civil_defense_response", "get_human_verification")
        workflow.add_edge("public_works_response", "get_human_verification")
        workflow.add_conditional_edges("get_human_verification", verify_approval_router_web)
        workflow.add_edge("wait_for_approval", END)  # Stop here when approval needed
        workflow.add_edge("emergency_response", "send_email_alert")
        workflow.add_edge("send_email_alert", END)
        workflow.add_edge("handle_no_approval", END)
        
        workflow.set_entry_point("get_weather")
        app = workflow.compile()
        
        # Initialize state
        initial_state = {
            "city": city,
            "weather_data": {},
            "disaster_type": "",
            "severity": "",
            "response": "",
            "messages": [],
            "alerts": [],
            "human_approved": False,
            "needs_approval": False,
            "verification_id": None
        }
        
        # Run the workflow
        result = app.invoke(initial_state)
        
        # Check if approval is needed
        needs_approval = result.get("needs_approval", False)
        verification_id = result.get("verification_id")
        
        # If approval is needed, return early with the current state
        if needs_approval:
            return {
                "city": result.get("city", city),
                "weather_data": result.get("weather_data", {}),
                "disaster_type": result.get("disaster_type", "Unknown"),
                "severity": result.get("severity", "Unknown"),
                "response": result.get("response", ""),
                "needs_approval": True,
                "verification_id": verification_id,
                "messages": [str(msg) for msg in result.get("messages", [])],
                "alerts": result.get("alerts", [])
            }
        
        # Otherwise, return complete result
        return {
            "city": result.get("city", city),
            "weather_data": result.get("weather_data", {}),
            "disaster_type": result.get("disaster_type", "No Immediate Threat"),
            "severity": result.get("severity", "Low"),
            "response": result.get("response", "No response plan generated"),
            "needs_approval": False,
            "verification_id": None,
            "messages": [str(msg) for msg in result.get("messages", [])],
            "alerts": result.get("alerts", []),
            "email_sent": "send_email_alert" in [str(msg) for msg in result.get("messages", [])]
        }
        
    except Exception as e:
        print(f"Error running agent for {city}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "city": city,
            "weather_data": {},
            "disaster_type": "Analysis Error",
            "severity": "Unknown",
            "response": f"Error occurred during analysis: {str(e)}",
            "needs_approval": False,
            "verification_id": None,
            "messages": [],
            "alerts": []
        }



