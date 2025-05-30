# Mushroom Monitoring Dashboard for the University of Pikeville designed by Ivan Wheeling

A real-time monitoring system for mushroom cultivation with sensor data visualization and AI-powered insights.

## Project Structure

- `api_server.py`: FastAPI backend server handling WebSocket connections and API endpoints
- `sensor_handler.py`: Manages sensor data reading and processing
- `ai_model.py`: Handles AI conversation and insights
- `insight_bot.py`: Generates insights from sensor data
- `mushroom-dashboard/`: React frontend application

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

## Setup

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install fastapi uvicorn websockets numpy pandas
```

### Frontend Setup

1. Navigate to the React app directory:
```bash
cd mushroom-dashboard
```

2. Install Node.js dependencies:
```bash
npm install
```

## Running the Application

### Terminal 1 - Backend Server
```bash
# Activate virtual environment if not already activated
source env/bin/activate  # On Windows: env\Scripts\activate

# Start the FastAPI server
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 - Frontend Development Server
```bash
cd mushroom-dashboard
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Features

- Real-time sensor data monitoring
- WebSocket connection for live updates
- AI-powered insights and recommendations
- Historical data visualization
- Interactive chat interface for queries

## API Endpoints

- `GET /history`: Retrieve historical sensor data
- `GET /insight`: Get current AI insights
- `GET /run_insight`: Trigger new insight generation
- `POST /chat`: Send messages to AI assistant
- `WebSocket /ws`: Real-time sensor data stream

## Development

- The backend uses FastAPI for high-performance API development
- The frontend is built with React and uses Recharts for data visualization
- WebSocket connections enable real-time updates
- AI integration provides intelligent insights and recommendations

## Security Notes

- API keys are stored in `key.txt` which is gitignored
- Use `key.template.txt` as a reference for setting up new environments
- Never commit sensitive credentials to the repository
- Assistant IDs are configuration values and can be safely committed
- All file paths are relative for better portability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 