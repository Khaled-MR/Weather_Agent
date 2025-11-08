# Weather Emergency Response System

A modern web-based weather monitoring and disaster response system built with FastAPI and a beautiful HTML/CSS/JavaScript frontend.

## Features

- 🌦️ Real-time weather monitoring for single or multiple cities
- 🚨 Automatic disaster type detection (Hurricane, Flood, Heatwave, etc.)
- 📊 Severity assessment (Critical, High, Medium, Low)
- 📧 Email alerts for weather emergencies
- 📝 Automatic logging of all weather checks and disasters
- 🎨 Modern, responsive web interface
- ⚡ FastAPI backend with async support

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:
```env
API_KEY=your_openweathermap_api_key
google_api_key=your_google_gemini_api_key
SENDER_EMAIL=your_email@gmail.com
RECEIVER_EMAIL=recipient_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## Usage

### Web Interface (Recommended)

1. Start the FastAPI server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Use the web interface to:
   - Check weather for a single city
   - Check weather for multiple cities (comma-separated)
   - View recent weather checks and disaster logs
   - Monitor real-time status of weather checks

### Command Line Interface (Original)

You can still use the original command-line interface:

```bash
python Agents.py
```

Note: The CLI version includes interactive human verification prompts for low/medium severity alerts.

## API Endpoints

- `GET /` - Main web interface
- `POST /api/check-weather` - Check weather for a single city
- `POST /api/check-multiple-cities` - Check weather for multiple cities
- `GET /api/check-status/{task_id}` - Get status of a weather check
- `GET /api/logs` - Get recent disaster logs
- `GET /api/running-tasks` - Get all running tasks

## Project Structure

```
weather/
├── app.py                 # FastAPI application
├── Agents.py              # Core weather logic and LangGraph workflow
├── static/
│   ├── index.html        # Main web interface
│   ├── styles.css        # Modern styling
│   └── script.js         # Frontend JavaScript
├── disaster_log.txt      # Log file for weather checks
└── requirements.txt      # Python dependencies
```

## How It Works

1. **Weather Data Fetching**: Retrieves current weather from OpenWeatherMap API
2. **Disaster Analysis**: Uses Google Gemini AI to identify potential disasters
3. **Severity Assessment**: AI evaluates the severity level
4. **Response Generation**: Creates appropriate response plans based on disaster type
5. **Email Alerts**: Sends alerts for high/critical severity (with human approval for low/medium)
6. **Logging**: All checks are logged to `disaster_log.txt`

### System Workflow

The following flowchart illustrates the autonomous agent's process for handling weather-related disaster responses:

![Weather Emergency Response System Workflow](images/workflow.png)

*Note: The agent operates autonomously, running continuously to call the weather API at specified intervals. It processes the fetched data within the state graph, ensuring dynamic handling and decision-making based on real-time weather updates.*

## Technologies

- **Backend**: FastAPI, Python
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI**: Google Gemini (via LangChain)
- **Workflow**: LangGraph
- **Weather API**: OpenWeatherMap

## Notes

- The web interface runs weather checks asynchronously in the background
- Human verification prompts (for low/medium severity) are only available in the CLI version
- All weather checks are automatically logged
- The system auto-refreshes logs every 30 seconds in the web interface


