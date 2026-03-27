https://github.com/user-attachments/assets/f61de3fa-c657-4da9-b1f8-19749978ba23

# Zomato AI Recommender

AI-powered restaurant recommendation service for Bangalore. Get personalized restaurant suggestions based on locality, rating, price, and cuisine.

## 🌐 Live Demo

**Streamlit App:** https://zomato-ai-recommender.streamlit.app

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv phase1/.venv phase2/.venv phase3/.venv phase4/.venv
phase1/.venv/bin/pip install -r phase1/requirements.txt
phase2/.venv/bin/pip install -r phase2/requirements.txt
phase3/.venv/bin/pip install -r phase3/requirements.txt
phase4/.venv/bin/pip install -r phase4/requirements.txt
cd phase5 && npm install

# 2. Add GROQ_API_KEY to .env (see .env.example)

# 3. Run full stack
./run_all.sh
# → UI: http://localhost:5173

# Or run Streamlit (starts backend automatically)
./run_streamlit.sh
# → Streamlit: http://localhost:5175
```

## API Endpoints

### Health Check
- `GET /` - API info
- `GET /health` - Health check endpoint

### Recommendation APIs
- `POST /api/recommendations` - Get restaurant recommendations
- `GET /api/locations` - Get all available locations
- `GET /api/cuisines` - Get all available cuisines

### Example Request
```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"place": "JP Nagar", "rating": 4.0, "price_range": "₹300 - ₹600"}'
```

## Features

✅ **Optimized Dataset**: ~1000 restaurants covering 29 locations, 63 cuisines  
✅ **Dynamic Filters**: Rating options based on selected location  
✅ **Fast Performance**: <1s startup, instant recommendations  
✅ **AI-Powered**: Groq LLM for intelligent recommendations  
✅ **Fallback Mode**: Works without API key (filtered results)  
✅ **Light Theme**: Clean, modern UI with red accents

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → Select repo, main file: `streamlit_app.py`
4. Add secret: `API_BASE_URL` = your deployed backend URL

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

## Project Structure

- **Phase 1**: Data fetch (Hugging Face)
- **Phase 2**: Data cleaning pipeline
- **Phase 3**: Filter + LLM (Groq)
- **Phase 4**: FastAPI backend
- **Phase 5**: React UI
- **streamlit_app.py**: Streamlit UI (for deployment)

## Technical Details

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture and [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

## Footer

Zomato-AI-Recommender  
© 2026 Ashish Kumar Sankhua. All rights reserved.
