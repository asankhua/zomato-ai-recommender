# Deployment Guide

## Streamlit Cloud (Single Deployment – No Backend Needed)

The Streamlit app runs **standalone** on Streamlit Cloud. It bundles the recommendation logic and sample data—no separate backend deployment required.

### Deploy to Streamlit Cloud

1. **Push code to GitHub** (see GitHub section below).

2. **Go to [share.streamlit.io](https://share.streamlit.io/)** and sign in with GitHub.

3. **New app** → Select your repo `zomato-ai-recommender`.

4. **Main file path:** `streamlit_app.py`

5. **Advanced settings** → Secrets. Add (optional but recommended for AI recommendations):

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Without `GROQ_API_KEY`, the app still works and returns filtered recommendations with descriptive reasons (no Groq LLM call).

6. **Deploy.** Streamlit Cloud installs from `requirements.txt` and runs the app.

---

## Optional: API Mode (Local Development)

When running locally with `./run_backend.sh`, the Streamlit app uses the Phase 4 API. Set `API_BASE_URL` in `.env` or Streamlit secrets if your backend runs elsewhere.

---

## GitHub Setup & Push

```bash
cd zomato-ai-recommender
git init
git add .
git commit -m "Initial commit: Zomato AI Recommender"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/zomato-ai-recommender.git
git push -u origin main
```

Create the repo on GitHub first (github.com/new), then add the remote and push.
