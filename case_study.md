**Zomato AI Recommender**  
*AI-powered personalized restaurant recommendations for Bangalore*

**Author:** Ashish Kumar Sankhua | Product Manager  
**Date:** March 2026 | **Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Technology Justification](#4-technology-justification)
5. [Success Metrics](#5-success-metrics)
6. [Risk Assessment](#6-risk-assessment)
7. [Technical Architecture](#7-technical-architecture)
8. [Go-to-Market Strategy](#8-go-to-market-strategy)
9. [Lessons Learned & Roadmap](#9-lessons-learned--roadmap)
10. [Conclusion](#10-conclusion)

---

## 1. Executive Summary

**Product:** Zomato AI Recommender  
**Author:** [Your Name] | **Status:** [Draft / In Review / Complete]  
**Last Updated:** [Date]

Zomato AI Recommender is an AI-powered restaurant recommendation service designed to solve the "where should we eat?" problem for users in Bangalore. By combining traditional filtering (location, rating, price, cuisine) with Large Language Model (LLM) intelligence, the product delivers personalized, context-aware restaurant suggestions with natural-language reasoning.

**Key Highlights:**
- Serves ~1000 curated restaurants across 29 Bangalore locations and 63 cuisines
- Sub-1-second response time with Groq LLM integration
- Dual UI: React app for development, Streamlit for rapid cloud deployment
- Graceful fallback when AI is unavailable (no service degradation)

---

## 2. Problem Statement

### The User Pain Point

Users face decision fatigue when choosing restaurants, especially in dense urban markets like Bangalore. Existing solutions rely on simple filtering (rating, price) but fail to provide *personalized, contextual recommendations* that explain *why* a restaurant matches the user's needs.

| Pain Point | User Impact | Current State |
|------------|-------------|---------------|
| **Information Overload** | Too many options, hard to decide | Static lists with no personalization |
| **Lack of Context** | Unclear why a restaurant is recommended | No reasoning provided |
| **Generic Filters** | Filters don't capture nuanced preferences | Basic price/rating sliders only |
| **Decision Fatigue** | Users give up or default to known options | High bounce rates on discovery pages |

### Target User
- **Primary:** Urban professionals in Bangalore (ages 25-40)
- **Use Case:** Finding restaurants for dining out, ordering in, or exploring new neighborhoods
- **Pain Intensity:** Medium-High (occurs frequently, causes measurable friction)

---

## 3. Solution Overview

### What We Built

An end-to-end recommendation system with three layers:

1. **Smart Filtering Layer:** Pre-filters ~1000 restaurants by location, minimum rating, price range, and cuisine preferences
2. **AI Recommendation Engine:** Uses Groq LLM to analyze filtered candidates and generate personalized, ranked recommendations with natural-language reasoning
3. **Dual Interface:** React UI for rich interactions; Streamlit UI for rapid deployment and sharing

### Key Features

- **Dynamic Rating Filter:** Rating options adapt based on selected location (shows only available ratings)
- **Natural Language Explanations:** Each recommendation includes a "Why you'll like it" section
- **Fallback Mode:** App works without API key by returning top-rated filtered results
- **Lightweight Dataset:** Optimized ~1000-row CSV (172KB) for fast startup and minimal hosting costs

### User Flow

```
User Input (Place + Rating + Price + Cuisine)
    ↓
Filter Layer (matches ~1000 restaurant dataset)
    ↓
LLM Processing (Groq generates ranked recommendations)
    ↓
Display Results (cards with reasoning)
```

---

## 4. Technology Justification

### Why Generative AI?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Traditional Software** (rules-based) | Fast, deterministic, no API costs | Cannot generate natural-language reasoning; rigid matching logic | ❌ Rejected |
| **Collaborative Filtering** (ML-based) | Scalable, learns user preferences | Requires large user interaction dataset; cold start problem | ❌ Rejected (no user data available) |
| **Generative AI** (LLM) | Natural explanations, understands nuanced preferences, no training data needed | API costs, latency, hallucination risk | ✅ **Selected** |

### Build vs. AI Decision Matrix

| Feature | Traditional Build | AI-Powered | Rationale |
|---------|-------------------|------------|-----------|
| Ranking restaurants by rating | ✅ Easy (sort function) | ❌ Overkill | Built with traditional filtering |
| Explaining *why* a restaurant matches | ❌ Requires hardcoded templates | ✅ LLM generates dynamic explanations | AI justifies the recommendation |
| Handling edge cases ("romantic dinner", "family-friendly") | ❌ Complex rule engine | ✅ LLM understands context | AI captures nuanced intent |
| Personalization without user history | ❌ Impossible | ✅ LLM infers from query context | AI enables zero-shot personalization |

### AI Provider Choice: Groq

- **Speed:** Sub-second inference (critical for UX)
- **Cost:** Competitive pricing for production workloads
- **Fallback:** Built-in fallback when API unavailable (service continuity)

---

## 5. Success Metrics

### North Star Metric
**Recommendation Acceptance Rate:** % of users who act on a recommendation (click through, visit, or save)

### Key Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Task Completion Rate** | >70% | Users who get recommendations after starting a search |
| **Response Time (p95)** | <2 seconds | API latency logging |
| **User Satisfaction Score** | >4.0/5 | Post-recommendation thumbs up/down |
| **Fallback Trigger Rate** | <10% | Monitor API failure / missing key scenarios |
| **Recommendation Diversity** | >3 unique cuisines per session | Track recommendation variety |

### Secondary Metrics
- **Coverage:** % of locations with at least 10 recommendations available
- **Error Rate:** % of requests returning 500 errors (target: <1%)
- **Session Duration:** Time from search to result (shorter = better UX)

---

## 6. Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| **AI Hallucination** | Medium | High | Structured prompt engineering; fallback to filtered results if LLM output malformed; validate restaurant names against dataset |
| **API Rate Limits / Downtime** | Medium | High | Graceful fallback mode: return top-rated filtered results with static descriptions when LLM unavailable |
| **Data Staleness** | Low | Medium | Dataset timestamped; pipeline exists to refresh from Hugging Face source; recommend quarterly updates |
| **Slow Response Times** | Low | Medium | Cached dataset at startup; optimized 1000-row subset; async LLM calls with timeout handling |
| **Incorrect Recommendations** | Medium | Medium | Pre-filter validation; LLM only ranks pre-validated candidates; user feedback loop for model refinement |

### Mitigation Details

**Hallucination Mitigation:**
- LLM only sees pre-filtered candidates (not entire dataset), reducing scope for invention
- Structured JSON output schema enforced
- Restaurant names validated against dataset before display

**API Failure Mitigation:**
- Environment variable check: if `GROQ_API_KEY` missing, skip LLM call
- Static ranking logic (rating → votes → cost) provides deterministic fallback
- No 500 errors; service degrades gracefully

---

## 7. Technical Architecture

### System Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│ Filter & Process │────▶│ LLM Processing  │────▶│  UI (Display)   │
│  (Place, etc.)  │     │  (Pre-loaded CSV)│     │ (Groq API)      │     │ Recommendations │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Source** | Optimized CSV (~1000 rows) | Fast startup, no external API dependency |
| **Data Cleaning** | Python pipeline | Normalize price, rating, cuisine fields |
| **Filtering** | Pandas | Location, rating, price, cuisine filters |
| **LLM** | Groq API (llama-3.1-8b-instant) | Generate recommendations with reasoning |
| **Backend API** | FastAPI | RESTful endpoints, CORS, OpenAPI docs |
| **Primary UI** | React + Vite | Rich client-side experience |
| **Deployment UI** | Streamlit | Rapid cloud deployment |

### Implementation Phases

1. **Phase 1:** Project setup, data acquisition (Hugging Face)
2. **Phase 2:** Data cleaning pipeline (price, rating, cuisine normalization)
3. **Phase 3:** Filtering + LLM integration with fallback
4. **Phase 4:** FastAPI backend with dynamic rating endpoints
5. **Phase 5:** React UI + Streamlit UI

---

## 8. Go-to-Market Strategy

### Target Segments

| Segment | Characteristics | Value Proposition |
|---------|-----------------|-------------------|
| **Primary:** Urban Explorers | 25-40, new to area, active on weekends | "Discover hidden gems in your neighborhood" |
| **Secondary:** Busy Professionals | Limited time, order/dine out frequently | "Get curated picks in under 2 seconds" |
| **Tertiary:** Food Enthusiasts | Seek variety, try new cuisines | "AI-powered suggestions that understand your mood" |

### Distribution Channels

- **Streamlit Cloud:** Zero-cost hosting for MVP and demos
- **GitHub:** Open-source visibility, portfolio showcase
- **Personal Network:** Bangalore-based peers for beta testing

### Pricing
- **Current:** Free (portfolio project)
- **Future:** API usage costs covered by subscription or per-query pricing

---

## 9. Lessons Learned & Roadmap

### Lessons Learned

1. **Dataset Optimization Matters:** Reducing from 51K to 1K rows improved startup time from ~5s to <1s without sacrificing coverage
2. **Fallback Design is Essential:** LLM APIs are unreliable; graceful degradation maintains UX
3. **Prompt Engineering is Iterative:** Structured outputs require explicit JSON schema in prompts
4. **Dual UI Strategy Works:** React for development richness, Streamlit for deployment simplicity

### Roadmap

| Phase | Timeline | Features |
|-------|----------|----------|
| **MVP (Current)** | Complete | Core recommendation, Streamlit deployment |
| **V1.1** | [Q2] | User feedback collection (thumbs up/down) |
| **V1.2** | [Q3] | Expand dataset to other Indian cities |
| **V2.0** | [Q4] | User accounts, recommendation history, personalization |
| **V2.1** | [Future] | Integration with Zomato/Swiggy APIs for live data |

### Open Questions
- How to collect implicit feedback (dwell time, click-through) without user accounts?
- What is the cost-per-recommendation at scale?
- Should we expand to other cities or deepen Bangalore coverage first?

---

## 10. Conclusion

Zomato AI Recommender demonstrates that **Generative AI can enhance traditional software** without replacing it. By combining deterministic filtering (location, rating, price) with LLM-powered reasoning, we deliver personalized recommendations that explain themselves—something pure rule-based systems cannot achieve.

**Key Takeaway:** AI is most effective when it augments existing workflows, not replaces them. The fallback mode ensures reliability; the LLM adds delight.

**Next Steps:**
1. Deploy to Streamlit Cloud for public access
2. Collect user feedback to validate recommendation quality
3. Iterate on prompt engineering to reduce hallucination further

---

## Appendix

### Links & References

- **Live Demo:** [https://zomato-ai-recommender.streamlit.app](https://zomato-ai-recommender.streamlit.app) (update when deployed)
- **GitHub Repository:** [github.com/[username]/zomato-ai-recommender](https://github.com/[username]/zomato-ai-recommender)
- **Architecture Doc:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deployment Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)

### Data Source
- **Original Dataset:** `ManikaSaini/zomato-restaurant-recommendation` (Hugging Face)
- **Optimized Dataset:** `phase4/data/cleaned.csv` (~1000 rows, 29 locations, 63 cuisines)

### API Provider
- **Groq:** [https://groq.com](https://groq.com) — Fast LLM inference

---

*[Document Status: Draft — Update placeholders in brackets before review]*
