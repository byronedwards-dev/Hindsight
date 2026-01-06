# Hindsight Economics

A forecasting prediction game that tests users' economic intuition by presenting them with historical macroeconomic data (with dates obscured) and asking them to predict what happens next.

## Features

- **Historical Data Visualization**: View 24 months of indexed asset prices and macro indicators
- **Market Predictions**: Predict probability of various stock return thresholds
- **Asset Allocation**: Allocate a hypothetical $100,000 portfolio
- **Calibration Scoring**: Brier score measures prediction accuracy
- **Benchmark Comparison**: Compare against 60/40 portfolio
- **Leaderboard**: Track top forecasters

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + Recharts
- **Data**: FRED API + Shiller dataset

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL)
- FRED API key ([get one here](https://fred.stlouisfed.org/docs/api/api_key.html))

### 1. Clone and Setup

```bash
cd C:\Users\byron\Hindsight
```

### 2. Create Environment File

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://hindsight:hindsight_dev@localhost:5432/hindsight
REDIS_URL=redis://localhost:6379
FRED_API_KEY=your_fred_api_key_here
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=development
```

### 3. Start Database

```bash
docker-compose up -d
```

### 4. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Fetch and process data
python scripts/fetch_data.py
python scripts/normalize_data.py
python scripts/compute_scenarios.py --clear

# Validate scenarios
python scripts/validate_scenarios.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 5. Setup Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 6. Play the Game

Open http://localhost:3000 in your browser.

## Project Structure

```
hindsight/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── scripts/          # Data pipeline
│   │   ├── fetch_data.py
│   │   ├── normalize_data.py
│   │   ├── compute_scenarios.py
│   │   └── validate_scenarios.py
│   ├── alembic/          # Database migrations
│   └── data/             # Data files (gitignored)
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   └── lib/              # Utilities
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios/random` | Get random scenario |
| GET | `/api/scenarios/{id}/history` | Get 24-month historical data |
| POST | `/api/games` | Create game with predictions |
| GET | `/api/games/{token}/reveal` | Get game results |
| POST | `/api/games/{token}/leaderboard` | Join leaderboard |
| GET | `/api/leaderboard` | Get leaderboard |

## Data Sources

- **Stocks**: S&P 500 Total Return (Shiller dataset)
- **Bonds**: 10-Year Treasury (FRED: DGS10)
- **Cash**: 3-Month T-Bills (FRED: TB3MS)
- **Gold**: Gold Spot Price (FRED: GOLDAMGBD228NLBM)
- **Macro**: GDP, Unemployment, Inflation, Fed Funds, Industrial Production

## Scoring

### Brier Score
Measures prediction calibration:
- 0.00: Perfect
- 0.25: Random guessing
- Lower is better

### Portfolio Metrics
- Real returns (inflation-adjusted)
- Sharpe ratio (risk-adjusted)
- Comparison to 60/40 benchmark

## Adding Custom Scenarios

Create a JSON file with start dates:

```json
[
  "1973-01-01",
  "1987-06-01",
  "2008-06-01"
]
```

Then run:

```bash
python scripts/compute_scenarios.py --start-dates custom_dates.json --clear
```

## License

MIT


