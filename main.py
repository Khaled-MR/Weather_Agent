"""
FastAPI Backend for Weather Emergency Response System

This module provides REST API endpoints to interact with the LangGraph-based
weather emergency response agent through a web interface.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

# Import agent and email utilities
try:
    from agent_web import run_agent_web, continue_with_approval
    WEB_AGENT_AVAILABLE = True
except ImportError:
    from agent import run_agent
    WEB_AGENT_AVAILABLE = False
    print("Warning: agent_web not available, using basic agent (may block on terminal input)")

from email_utils import send_email

# Initialize FastAPI app
app = FastAPI(
    title="Weather Emergency Response API",
    description="API for real-time weather disaster analysis and response",
    version="1.0.0"
)

# Mount static files directory (for CSS if needed)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for weather analysis"""
    city: str


class AnalyzeResponse(BaseModel):
    """Response model for weather analysis"""
    city: str
    weather_data: dict
    disaster_type: str
    severity: str
    response: str
    success: bool
    message: Optional[str] = None
    needs_approval: Optional[bool] = False
    verification_id: Optional[str] = None


class EmailRequest(BaseModel):
    """Request model for email sending"""
    city: str
    report_text: str
    recipient_email: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request model for human approval"""
    verification_id: str
    approved: bool


class EmailResponse(BaseModel):
    """Response model for email sending"""
    success: bool
    message: str


@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Serve the main HTML interface
    
    Returns:
        HTMLResponse: The index.html template
    """
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: templates/index.html not found</h1>",
            status_code=404
        )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_weather(request: AnalyzeRequest):
    """
    Analyze weather conditions for a given city using the LangGraph agent
    
    Args:
        request: AnalyzeRequest containing the city name
        
    Returns:
        AnalyzeResponse: Weather analysis results including:
            - Current weather data
            - Disaster type classification
            - Severity assessment
            - Emergency response plan
    """
    try:
        # Validate city name
        if not request.city or not request.city.strip():
            raise HTTPException(
                status_code=400,
                detail="City name cannot be empty"
            )
        
        city = request.city.strip()
        
        # Call the agent to analyze weather
        if WEB_AGENT_AVAILABLE:
            result = run_agent_web(city)
        else:
            result = run_agent(city)
            result["needs_approval"] = False
            result["verification_id"] = None
        
        # Extract relevant data from agent result
        weather_data = result.get("weather_data", {})
        disaster_type = result.get("disaster_type", "Unknown")
        severity = result.get("severity", "Unknown")
        response_plan = result.get("response", "No response plan generated")
        needs_approval = result.get("needs_approval", False)
        verification_id = result.get("verification_id")
        
        if needs_approval:
            message = f"Human approval required for {city} - Low/Medium severity detected"
        else:
            message = f"Weather analysis completed for {city}"
        
        return AnalyzeResponse(
            city=city,
            weather_data=weather_data,
            disaster_type=disaster_type,
            severity=severity,
            response=response_plan,
            success=True,
            message=message,
            needs_approval=needs_approval,
            verification_id=verification_id
        )
        
    except Exception as e:
        # Handle errors gracefully
        return AnalyzeResponse(
            city=request.city,
            weather_data={},
            disaster_type="Error",
            severity="Unknown",
            response="",
            success=False,
            message=f"Error analyzing weather: {str(e)}"
        )


@app.post("/send_email", response_model=EmailResponse)
async def send_email_report(request: EmailRequest):
    """
    Send weather emergency report via email
    
    Args:
        request: EmailRequest containing city, report text, and optional recipient
        
    Returns:
        EmailResponse: Success status and message
    """
    try:
        # Validate input
        if not request.city or not request.report_text:
            raise HTTPException(
                status_code=400,
                detail="City and report text are required"
            )
        
        # Prepare email content
        subject = f"Weather Emergency Report: {request.city}"
        content = request.report_text
        
        # Use recipient from request or default from environment
        recipient = request.recipient_email or os.getenv("RECEIVER_EMAIL")
        
        if not recipient:
            raise HTTPException(
                status_code=400,
                detail="Recipient email not provided and RECEIVER_EMAIL not set in environment"
            )
        
        # Send email using email utility
        success = send_email(recipient, subject, content)
        
        if success:
            return EmailResponse(
                success=True,
                message=f"✅ Email sent successfully to {recipient}!"
            )
        else:
            return EmailResponse(
                success=False,
                message="❌ Failed to send email. Please check email configuration."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        return EmailResponse(
            success=False,
            message=f"Error sending email: {str(e)}"
        )


@app.post("/approve")
async def handle_approval(request: ApprovalRequest):
    """
    Handle human approval/rejection for low/medium severity alerts
    
    Args:
        request: ApprovalRequest containing verification_id and approval decision
        
    Returns:
        dict: Result of continuing the workflow with approval decision
    """
    try:
        if not WEB_AGENT_AVAILABLE:
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "message": "Web agent not available. Approval handling requires agent_web module."
                }
            )
        
        # Continue the workflow with the approval decision
        result = continue_with_approval(request.verification_id, request.approved)
        
        # Extract relevant data
        email_sent = "send_email_alert" in [str(msg) for msg in result.get("messages", [])]
        
        if request.approved and email_sent:
            message = "✅ Email alert sent successfully!"
        elif request.approved:
            message = "✅ Approval granted, but email sending encountered an issue."
        else:
            message = "❌ Approval rejected. Email alert not sent."
        
        return {
            "success": True,
            "message": message,
            "email_sent": email_sent,
            "city": result.get("city", "Unknown")
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"Verification ID not found: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing approval: {str(e)}"
            }
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: API status
    """
    return {
        "status": "healthy",
        "service": "Weather Emergency Response API",
        "version": "1.0.0",
        "web_agent_available": WEB_AGENT_AVAILABLE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

