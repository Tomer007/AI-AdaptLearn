# AI-AdaptLearn

An AI-driven adaptive learning platform that integrates intelligent assessments, dynamic content delivery, and real-time user interaction through a chatbot.

## Features

- **AI-Powered Chatbot**: Interactive interface using LangChain and GPT for personalized learning
- **Adaptive Learning**: Dynamic content delivery based on user progress and preferences
- **Real-time Interaction**: Instant responses and real-time chat experience
- **User History Management**: Stores last 1000 chat messages for context-aware responses
- **Personalized Settings**: Customizable learning packs, sections, and assessment parameters

## Project Structure

```
AI-AdaptLearn/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── user.py            # User and settings models
│   │   └── chat.py            # Chat message models
│   ├── controllers/            # API controllers
│   │   ├── __init__.py
│   │   ├── user_controller.py # User settings controller
│   │   └── chat_controller.py # Chat interaction controller
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── user_service.py    # User management service
│   │   ├── chat_service.py    # Chat processing service
│   │   └── llm_service.py     # LangChain integration service
│   ├── database/               # Database configuration
│   │   ├── __init__.py
│   │   ├── database.py        # Database connection
│   │   └── models.py          # SQLAlchemy models
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── helpers.py         # Helper functions
├── frontend/                   # Frontend application
│   ├── index.html             # Main HTML file
│   ├── styles.css             # CSS styles
│   └── script.js              # Frontend JavaScript
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── run_app.sh                 # Full automated run script (with AI features)
├── run_simple.sh              # Simple run script (basic functionality)
├── run_minimal.sh             # Minimal run script (creates basic working version)
├── run_direct.sh              # Direct run script (no modifications)
├── run_ide.sh                 # IDE setup script (sets PYTHONPATH)
├── launch.py                  # Python launcher script
├── migrate_db.py              # Database migration script
└── README.md                  # This file
```

## Quick Start

### Option 1: Using the IDE Launcher Script (Recommended for IDE Debug)
```bash
# Make the script executable (first time only)
chmod +x run_ide.sh

# Setup environment for IDE
./run_ide.sh
```

This script sets up the environment and PYTHONPATH so you can use "Run -> Debug" in your IDE.

### Option 2: Using the Python Launcher
```bash
# Run directly with Python
python launch.py
```

This launcher script sets the correct Python path and runs the application.

### Option 3: Using the Simple Run Script (Basic Setup)
```bash
# Make the script executable (first time only)
chmod +x run_simple.sh

# Run the basic application
./run_simple.sh
```

The simple run script will:
- Create a virtual environment if it doesn't exist
- Install basic dependencies (FastAPI, SQLAlchemy, etc.)
- Create a default `.env` file if needed
- Start the FastAPI server without AI features

### Option 4: Using the Full Run Script (Includes AI Features)
```bash
# Make the script executable (first time only)
chmod +x run_app.sh

# Run the full application with AI features
./run_app.sh
```

**Note**: The full version requires proper LangChain setup and may have dependency compatibility issues.

### Option 2: Manual Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AI-AdaptLearn
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # The run script will create this automatically, or you can create manually:
   cp .env.example .env  # if .env.example exists
   # Edit .env with your OpenAI API key and other settings
   ```

5. **Run the application**:
   ```bash
   python -m app.main
   # OR
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Usage

1. **Start the backend server** (runs on http://localhost:8000)
2. **Open the frontend** (frontend/index.html) in your browser
3. **Configure your learning settings** (pack name, sections, tester name, date)
4. **Start chatting** with the AI-powered chatbot

## API Endpoints

- `POST /api/settings` - Submit user learning settings (creates new user or updates existing)
- `GET /api/users/settings/{tester_name}` - Get user settings by name
- `GET /api/users/{user_id}` - Get user information by ID
- `POST /api/chat` - Send chat messages
- `GET /api/chat/history` - Get chat history
- `GET /api/docs` - API documentation (Swagger UI)

## Database Schema

### Users Table
The users table now includes all learning settings:
- `id` - Primary key
- `tester_name` - Name of the tester/user
- `pack_name` - Learning pack name (e.g., "Watson Glaser")
- `assessment_date` - Date of the assessment (YYYY-MM-DD format)
- `duration` - Assessment duration in minutes
- `notes` - Additional notes or preferences
- `created_at` - User creation timestamp
- `last_active` - Last activity timestamp

## Configuration

Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./ai_adaptlearn.db
```

## Technologies Used

- **Backend**: FastAPI, Python
- **AI Integration**: LangChain, OpenAI GPT
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Real-time Communication**: WebSockets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Current Status

### ✅ What's Working
- FastAPI backend server setup
- Basic API endpoints and routing
- Database models and SQLAlchemy integration
- **Complete user management system with settings storage**
- **User settings persistence (pack name, sections, assessment date, notes)**
- **Smart save/update functionality (auto-detects new vs existing users)**
- **Frontend form auto-population from saved settings**
- Basic chat functionality structure

### ⚠️ Known Issues
- LangChain dependency compatibility issues (version conflicts)
- AI features may not work without proper dependency resolution

### 🔧 Recommended Approach
- Use `run_simple.sh` for basic functionality testing
- Use `run_app.sh` only after resolving LangChain compatibility issues

## IDE Setup

### For VS Code / PyCharm / Other IDEs
1. **Run the IDE setup script first**:
   ```bash
   ./run_ide.sh
   ```
   This sets the PYTHONPATH correctly.

2. **Then use "Run -> Debug"** in your IDE - it should work now!

3. **Alternative**: Use the Python launcher directly:
   ```bash
   python launch.py
   ```

### Python Path Issues
If you get "ModuleNotFoundError: No module named 'app'" when running from IDE:
- The IDE setup script (`run_ide.sh`) fixes this
- Or manually set PYTHONPATH to include the project root directory
- Or use the Python launcher script (`launch.py`)

## Troubleshooting

### Common Issues

1. **Import Error: name 'Optional' is not defined**
   - This has been fixed in the latest version
   - Ensure you're using the updated code

2. **ModuleNotFoundError: No module named 'app'**
   - Use `./run_ide.sh` to set up the environment
   - Or use `python launch.py` to run the app
   - This happens when Python can't find the app module

3. **LangChain Import Errors**
   - Use the simple run script for basic functionality
   - Check LangChain version compatibility
   - Consider using a different AI integration approach

2. **Virtual Environment Issues**
   - If you encounter permission issues, try: `chmod +x run_app.sh`
   - On Windows, use: `env\Scripts\activate`

3. **Port Already in Use**
   - Change the port in `.env` file: `PORT=8001`
   - Or kill the process using the port: `lsof -ti:8000 | xargs kill -9`

4. **OpenAI API Key Issues**
   - Ensure your API key is valid and has sufficient credits
   - Check the `.env` file has the correct format

### System Requirements

- Python 3.8 or higher
- macOS, Linux, or Windows
- Internet connection for AI features

## License

This project is licensed under the MIT License.

## How to Run the App (Step-by-Step)

1. Create and activate a virtual environment
   ```bash
   python3 -m venv env
   source env/bin/activate        # Windows: env\Scripts\activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Set your environment variables
   ```bash
   export OPENAI_API_KEY=YOUR_KEY_HERE
   export DEBUG=true
   ```
   On Windows (PowerShell):
   ```powershell
   $env:OPENAI_API_KEY="YOUR_KEY_HERE"
   $env:DEBUG="true"
   ```
4. Start the backend
   ```bash
   python launch.py
   ```
5. Open the UI
   - Navigate to `http://localhost:8000`
   - Use the Diagnostic tab to start the Intro Assessment
