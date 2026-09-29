# SalesPilot AI

**AI-powered sales automation platform for lead scoring, personalized outreach, engagement tracking, pipeline intelligence, and ROI analytics.**

SalesPilot AI is a full-stack sales operations platform built with **Drytis Studio**. It turns lead and engagement data into explainable prioritization, personalized outreach, deal forecasts, automation actions, and business insights.

> **Live Demo:** https://salespilot-ai-xv2otd.drytis.dev/  
> **Repository:** https://github.com/srivisnuA/salespilot-ai

## Overview

Sales teams often lose time deciding which leads to prioritize, writing repetitive follow-ups, tracking engagement, and estimating which opportunities are likely to close.

SalesPilot AI connects those workflows into one system:

**Lead data → Explainable scoring → Personalized outreach → Engagement tracking → Pipeline movement → Deal prediction → Analytics & ROI → Automated follow-up**

## Core Features

### Explainable Lead Scoring

Every lead receives a **0–100 score** and a temperature classification: Hot, Warm, or Cold.

Signals include:
- Job seniority
- Company size
- Industry fit
- Declared budget
- Buying timeline
- Email opens and link clicks
- Replies
- Demo/meeting requests
- Website activity
- Pricing-page interest
- Intent score

Each score includes a factor-by-factor explanation.

> **Implementation note:** The current scoring backend is an explainable weighted rules engine, not a claimed trained ML model. Its interface is structured so a validated scikit-learn/XGBoost backend can be introduced when sufficient historical outcomes are available.

### AI Personalized Email Generation

Generate outreach using:
- Professional, Friendly, Concise, or Consultative tone
- Short, Medium, or Detailed length
- Lead name, role, company, industry, pain point, timeline, budget, and previous engagement

The system supports an OpenAI-compatible provider when configured and includes a deterministic personalization fallback for demo environments.

### Engagement Tracking

Tracked events include:
- Email opened
- Link clicked
- Reply
- Demo requested
- Meeting booked
- Follow-up completed
- Website visit
- Pricing-page visit

Events appear in the lead timeline and can trigger score recomputation and automation rules.

### Sales Pipeline

Interactive Kanban stages:

**NEW → QUALIFIED → CONTACTED → ENGAGED → DEMO → NEGOTIATION → WON / LOST**

Deal cards expose value, lead score, win probability, risk, expected close date, and recent activity.

Pipeline metrics include open pipeline, weighted pipeline, won revenue, and predicted revenue.

### Explainable Deal Prediction

Each deal can show:
- Win probability
- Expected revenue
- Risk level
- Positive and negative contributing factors

Expected revenue:

**Expected Revenue = Deal Value × Win Probability**

The current implementation is a transparent heuristic model and does not claim trained-model accuracy.

### Outreach & Automation

Outreach supports Draft, Approved, and Sent states.

Automation examples:
- High-score lead → generate personalized outreach + follow-up task
- Multiple email opens → increase intent + notify representative
- No response → create follow-up
- Demo request → route the lead

Execution history is available for triggered rules.

### Analytics & ROI

Analytics includes:
- Win/loss rate
- Average deal value
- Sales cycle
- Pipeline velocity
- Predicted and won revenue
- Open and weighted pipeline
- Lead-source performance
- Score distribution
- Industry performance
- Email engagement
- Funnel conversion
- Campaign ROI

ROI formula:

**ROI = ((Revenue Generated − Campaign Cost) / Campaign Cost) × 100**

## Architecture

    SalesPilot AI UI
    React + Vite + Tailwind CSS + Recharts
                    |
                 REST API
                    |
             FastAPI Backend
                    |
       +------------+-------------+
       |            |             |
   Scoring     Prediction      Email
       |            |             |
       +------------+-------------+
                    |
          Relational Database

## Technology Stack

### Frontend
- React
- Vite
- Tailwind CSS
- Recharts
- React Router

### Backend
- Python
- FastAPI
- SQLAlchemy-compatible relational database layer
- Pydantic-style schemas
- PyMySQL

### AI / Intelligence
- Explainable weighted lead scoring
- Explainable deal prediction
- OpenAI-compatible email generation
- Deterministic personalized fallback generator
- ML-ready scoring interface for future scikit-learn/XGBoost integration

### Development
- Drytis Studio
- GitHub
- Automated backend tests
- Responsive web UI

## Project Structure

    salespilot-ai/
    ├── backend/
    │   ├── app/
    │   │   ├── routers/
    │   │   ├── services/
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   ├── main.py
    │   │   ├── models.py
    │   │   ├── schemas.py
    │   │   └── seed.py
    │   ├── tests/
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   ├── lib/
    │   │   └── pages/
    │   ├── package.json
    │   └── vite.config.js
    └── .gitignore

## End-to-End Demo Flow

1. Open Dashboard and review sales KPIs.
2. Open Leads and search for a lead.
3. Inspect the AI Lead Score and factor explanations.
4. Generate a personalized outreach email.
5. Record an engagement event such as a reply or demo request.
6. Observe the timeline and score update.
7. Open Pipeline and inspect the opportunity.
8. Review win probability, expected revenue, and risk factors.
9. Open Analytics for pipeline and engagement insights.
10. Review campaign ROI.
11. Open Automations and inspect active rules and execution history.
12. Update Settings and verify the save flow.

## Testing

Backend tests:

    cd backend
    pytest

Frontend build and lint:

    cd frontend
    npm install
    npm run build
    npm run lint

## Local Development

Create an environment file based on:

    backend/.env.example

Install backend dependencies:

    cd backend
    pip install -r requirements.txt

Install and run the frontend:

    cd frontend
    npm install
    npm run dev

The frontend communicates with the backend through the /api route.

## Environment Variables

The backend supports:

    DB_HOST
    DB_PORT
    DB_NAME
    DB_USER
    DB_PASSWORD
    OPENAI_API_KEY
    OPENAI_BASE_URL
    MODEL_BACKEND
    CORS_ORIGINS
    SEED_ON_START

Never commit real API keys, passwords, database credentials, or other secrets.

## Data & Demo Mode

The application includes seeded sample data across multiple industries so the complete sales workflow can be demonstrated without an external CRM.

The deployed environment is intended as a **demo/evaluation workspace**, not as a production CRM handling real customer data.

## Design Principles

- **Explainability:** users can understand why a lead or deal receives a prediction.
- **Actionability:** analytics should lead to a clear next sales action.
- **Automation with control:** generated outreach can be reviewed before sending.
- **Data-driven prioritization:** engagement signals influence lead and deal intelligence.
- **Graceful fallback:** core demo workflows remain usable when an external AI provider is unavailable.
- **Responsive UX:** the application is designed for desktop and mobile use.

## Current Limitations & Future Improvements

- Train and validate a supervised lead-conversion model when sufficient historical outcomes exist.
- Add precision, recall, F1 and ROC-AUC only after validating an actual ML model.
- Add richer multi-step campaign sequencing.
- Add CRM integrations.
- Add authentication and role-based access control.
- Add real email provider integrations and webhook tracking.
- Add model monitoring and prediction drift analysis.
- Add historical score trends backed by persisted score snapshots.

These are future improvements and are intentionally not presented as existing functionality.

## Assignment Alignment

| Requirement | Implementation |
|---|---|
| Lead scoring model | Explainable 0–100 scoring engine with factor breakdown |
| Email generation engine | Personalized AI/deterministic outreach generator |
| Engagement tracker | Event recording, timeline, score recomputation |
| Pipeline analytics | Kanban pipeline, forecasting, funnel and performance analytics |
| Email personalization | Lead/company/industry/pain/engagement-aware generation |
| Automation quality | Rule-based triggers and execution history |
| ROI metrics | Campaign cost, revenue attribution and ROI analytics |

## Built With Drytis Studio

This project was developed using **Drytis Studio** as required by the assignment workflow.

**Live Demo:** https://salespilot-ai-xv2otd.drytis.dev/

**Source Code:** https://github.com/srivisnuA/salespilot-ai

## Author

**Srivisnu A**

GitHub: https://github.com/srivisnuA
