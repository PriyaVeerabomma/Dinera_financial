# 💰 Smart Financial Coach

> AI-powered financial analysis that helps you understand your spending, detect anomalies, and achieve your savings goals.

![Smart Financial Coach](https://img.shields.io/badge/AI-Powered-1C1C1C?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-1C1C1C?style=flat-square)
![React](https://img.shields.io/badge/React-18.2-1C1C1C?style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-1C1C1C?style=flat-square)

---

## ✨ Features

### 🏷️ Smart Categorization
- **Hybrid approach**: Rule-based patterns (~70% coverage) + GPT-4o for complex transactions
- **Confidence scores**: See how confident the AI is about each categorization
- **Source tracking**: Know if categorization came from rules, AI, or user input

### 🚨 Anomaly Detection
- **Statistical analysis**: Z-score based detection for unusual spending
- **Severity levels**: High, Medium, Low based on deviation from typical spending
- **Rich explanations**: Understand why each transaction was flagged

### 🔄 Recurring Charge Detection
- **Subscription tracking**: Automatically identifies monthly and weekly patterns
- **Gray charge alerts**: Flags small, unknown recurring charges you might have forgotten
- **Frequency analysis**: Shows how often each charge occurs

### 💡 AI-Powered Insights
- **Personalized advice**: GPT-4o generates actionable recommendations
- **Explainable AI**: Every insight includes reasoning for transparency
- **Priority ordering**: Most impactful insights shown first

### 🎯 Goal Forecasting (Stretch)
- **Savings targets**: Set a monthly savings goal
- **Smart suggestions**: AI recommends specific category cuts
- **Achievability check**: Honest assessment of goal feasibility

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)             │
│  Upload CSV → Dashboard → Insights → Goals                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  /upload  →  /analyze  →  /dashboard  →  /goal              │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐   │
│  │CSVProcessor │ │ Categorizer │ │  AnomalyDetector     │   │
│  └─────────────┘ └─────────────┘ └──────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐   │
│  │RecurringDet │ │InsightGen   │ │  GoalForecaster      │   │
│  └─────────────┘ └─────────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌───────────┐   ┌──────────┐
        │  SQLite  │   │  OpenAI   │   │  Pandas  │
        │ 8 tables │   │  GPT-4o   │   │ Analysis │
        └──────────┘   └───────────┘   └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key

### 1. Clone & Setup Backend

```bash
# Navigate to project
cd smart-financial-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start Backend

```bash
cd backend
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Setup & Start Frontend

```bash
# In a new terminal
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (API, DB, OpenAI status) |
| `POST` | `/upload` | Upload CSV file for processing |
| `POST` | `/sample` | Load synthetic sample data |
| `POST` | `/analyze/{session_id}` | Run full analysis pipeline |
| `GET` | `/dashboard/{session_id}` | Get consolidated dashboard data |
| `POST` | `/goal/{session_id}` | AI-powered savings recommendations |
| `GET` | `/transactions/{session_id}` | Get paginated transactions |
| `GET` | `/categories` | Get all categories |

### Example: Full Flow

```bash
# 1. Upload CSV
curl -X POST http://localhost:8000/upload \
  -F "file=@transactions.csv"
# Returns: {"session_id": "abc-123", ...}

# 2. Analyze
curl -X POST http://localhost:8000/analyze/abc-123
# Returns: {"status": "ready", "insights_generated": 5, ...}

# 3. Get Dashboard
curl http://localhost:8000/dashboard/abc-123
# Returns: {summary, insights, anomalies, recurring_charges, deltas}
```

---

## 📁 Project Structure

```
smart-financial-coach/
├── backend/
│   ├── main.py                    # FastAPI app & routes
│   ├── database.py                # SQLite + 8 tables
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic schemas
│   ├── synthetic_data.py          # Demo data generator
│   ├── requirements.txt           # Python dependencies
│   └── services/
│       ├── ai_service.py          # OpenAI wrapper
│       ├── csv_processor.py       # CSV parsing
│       ├── categorizer.py         # Hybrid categorization
│       ├── anomaly_detector.py    # Z-score detection
│       ├── recurring_detector.py  # Subscription detection
│       └── insight_generator.py   # AI insights
├── frontend/
│   ├── package.json               # Node dependencies
│   ├── vite.config.ts             # Vite config
│   ├── tailwind.config.js         # Design system colors
│   └── src/
│       ├── App.tsx                # Main app
│       ├── types.ts               # TypeScript interfaces
│       ├── api/client.ts          # API client
│       └── components/
│           ├── Upload.tsx         # File upload
│           ├── Dashboard.tsx      # Main dashboard
│           ├── InsightCard.tsx    # AI insights
│           └── SpendingChart.tsx  # Pie chart
├── .env.example                   # Environment template
├── .cursor/rules/                 # Development rules
│   ├── project-rules.mdc          # Coding standards
│   └── design.mdc                 # UI design system
└── README.md                      # This file
```

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `sessions` | Upload session tracking |
| `categories` | Transaction categories (12 defaults) |
| `transactions` | Core transaction data |
| `anomalies` | Detected unusual spending |
| `recurring_charges` | Subscriptions & recurring payments |
| `deltas` | Month-over-month changes |
| `insights` | AI-generated recommendations |
| `goals` | User savings goals |

---

## 🎨 Design System

The UI follows a **warm, editorial-style neutral palette**:

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#F7F5F2` | App background |
| `surface` | `#FFFFFF` | Cards, panels |
| `border` | `#E6E2DC` | Dividers |
| `textPrimary` | `#111111` | Main text |
| `textSecondary` | `#5F5B57` | Metadata |
| `muted` | `#8C877F` | Placeholders |
| `accent` | `#1C1C1C` | Emphasis |

**Philosophy**: Calm, premium, grounded — like a quiet, intelligent assistant.

---

## 📋 CSV Format

Your CSV file should have these columns:

```csv
date,description,amount
2024-01-15,STARBUCKS COFFEE,-5.75
2024-01-15,PAYCHECK DIRECT DEPOSIT,3200.00
2024-01-16,NETFLIX SUBSCRIPTION,-15.99
```

- **date**: Transaction date (supports multiple formats)
- **description**: Merchant/transaction description
- **amount**: Positive for income, negative for expenses

---

## 🧪 Demo Script (2-3 minutes)

1. **Open app** — Clean landing page
2. **Click "Use Sample Data"** — Instant upload
3. **See dashboard** — Spending chart animates in
4. **Scroll to Insights** — Point out confidence scores and "Why" explanations
5. **Show Gray Charges** — "The app found a $2.99 charge you might not remember"
6. **Emphasize** — "All insights are explainable — users know WHY the AI made each recommendation"

---

## 🔒 Privacy & Security

- **Local processing**: Transactions processed on your machine
- **No storage**: Data not persisted after session
- **Privacy-first AI**: Only aggregated data sent to OpenAI (no raw transactions)
- **Session-based**: Each upload creates an isolated session

---

## 🛠️ Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Code Quality

```bash
# Python
pip install black isort
black backend/
isort backend/

# TypeScript
cd frontend
npm run lint
```

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o powering the AI features
- **FastAPI** for the high-performance backend
- **React + Tailwind** for the beautiful frontend
- **Recharts** for the monochrome pie charts

---

<div align="center">
  <p>Built with ❤️ for better financial health</p>
  <p><em>"This UI should feel like a quiet, intelligent assistant — not a loud app asking for attention."</em></p>
</div>
