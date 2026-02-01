# Smart Financial Coach

An AI-powered financial analysis application that helps users understand their spending patterns, detect anomalies, identify recurring charges, and receive personalized insights.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **CSV Upload & Processing** - Upload bank transaction CSV files for analysis
- **AI-Powered Categorization** - Automatic transaction categorization using OpenAI GPT-4
- **Anomaly Detection** - Statistical detection of unusual spending patterns
- **Recurring Charge Detection** - Identify subscriptions and "gray charges" (forgotten small subscriptions)
- **Personalized Insights** - AI-generated actionable financial recommendations
- **Interactive Chat (Dinera)** - Conversational AI assistant for financial questions
- **Goal-Based Savings** - Get recommendations to achieve savings targets
- **Clerk Authentication** - Secure user authentication with session isolation

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL database ORM
- **SQLite** - Lightweight database
- **OpenAI GPT-4** - AI-powered insights and chat
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling
- **Clerk** - Authentication

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **npm** or **yarn** - Comes with Node.js

You'll also need API keys for:
- **OpenAI API** - [Get API Key](https://platform.openai.com/api-keys)
- **Clerk** (optional, for authentication) - [Get Started](https://clerk.com/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smart-financial-coach.git
cd smart-financial-coach
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

## Configuration

### Backend Environment Variables

```bash
# Copy the example file
cd backend
cp env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

Required variables:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Optional (for Clerk authentication):
```env
CLERK_SECRET_KEY=sk_test_your-clerk-secret-key
CLERK_FRONTEND_API=your-instance.clerk.accounts.dev
```

For development without authentication:
```env
AUTH_BYPASS=true
```

### Frontend Environment Variables

```bash
# Copy the example file
cd frontend
cp env.example .env
```

Optional (for Clerk authentication):
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your-clerk-publishable-key
```

> **Note:** If you don't configure Clerk, the app will run in development mode with authentication bypassed.

## Running the Application

### Option 1: Run Both Services (Recommended)

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # If using virtual environment
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Quick Start Script

```bash
# From project root, run both services
# Terminal 1
cd backend && python3 -m uvicorn main:app --reload &

# Terminal 2
cd frontend && npm run dev
```

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Usage

1. **Open the app** at http://localhost:5173
2. **Sign in** (or use bypass mode in development)
3. **Upload a CSV** file with your transactions, or click **"Use Sample Data"** to try with demo data
4. **View Dashboard** with insights, anomalies, and recurring charges
5. **Chat with Dinera** - Ask questions about your spending

### CSV Format

Your CSV file should have these columns (flexible naming):

| Column | Description | Example |
|--------|-------------|---------|
| date | Transaction date | 2024-01-15 |
| description | Merchant/description | AMAZON.COM |
| amount | Transaction amount | -49.99 |

Negative amounts = expenses, Positive amounts = income

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload CSV file |
| POST | `/sample` | Load sample data |
| POST | `/analyze/{session_id}` | Run analysis |
| GET | `/dashboard/{session_id}` | Get dashboard data |
| POST | `/chat/{session_id}/sync` | Chat with Dinera |
| GET | `/sessions` | List user sessions |

Full API documentation available at http://localhost:8000/docs

## Project Structure

```
smart-financial-coach/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Clerk authentication
│   ├── database.py          # Database setup
│   ├── requirements.txt     # Python dependencies
│   └── services/
│       ├── ai_service.py    # OpenAI integration
│       ├── chat_service.py  # Dinera chat service
│       ├── categorizer.py   # Transaction categorization
│       ├── anomaly_detector.py
│       ├── recurring_detector.py
│       └── insight_generator.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main application
│   │   ├── components/      # React components
│   │   ├── api/client.ts    # API client
│   │   └── types.ts         # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Troubleshooting

### Backend won't start
- Ensure Python 3.10+ is installed: `python3 --version`
- Check if port 8000 is available: `lsof -i :8000`
- Verify `.env` file exists with `OPENAI_API_KEY`

### Frontend won't start
- Ensure Node.js 18+ is installed: `node --version`
- Check if port 5173 is available: `lsof -i :5173`
- Run `npm install` to ensure dependencies are installed

### API calls failing
- Check backend is running at http://localhost:8000/health
- Verify CORS settings if using different ports
- Check browser console for error details

### Authentication issues
- For development, set `AUTH_BYPASS=true` in backend `.env`
- For production, ensure all Clerk keys are configured

## Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Code Style

- Backend: Follow PEP 8, use type hints
- Frontend: ESLint + Prettier configured

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Clerk for authentication
- FastAPI and React communities

---

Built with ❤️ for smarter financial decisions
