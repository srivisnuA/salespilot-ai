# SalesPilot AI — Product Requirements Document (PRD)

**Project:** AI Sales Automation Platform  
**Product:** SalesPilot AI  
**Version:** 1.0  
**Status:** Assignment Submission / Prototype  
**Deployment:** https://salespilot-ai-xv2otd.drytis.dev/  
**Repository:** https://github.com/srivisnuA/salespilot-ai

---

## 1. Product Overview

SalesPilot AI is a sales automation platform designed to help sales teams prioritize leads, generate personalized outreach, track engagement, manage pipeline activity, predict deal outcomes, and understand revenue performance from a single workspace.

The platform combines explainable lead scoring, AI-assisted email generation, engagement tracking, pipeline analytics, deal prediction, ROI analysis, and configurable automation rules.

The prototype is designed as an end-to-end sales workflow rather than a standalone machine-learning model.

---

## 2. Problem Statement

Sales teams often manage leads and opportunities across spreadsheets, email tools, CRM systems, and separate analytics dashboards. This creates several problems:

- Sales representatives spend significant time manually prioritizing leads.
- Generic outreach reduces personalization.
- Engagement signals such as opens, clicks, replies, and meetings are difficult to consolidate.
- Pipeline health is not always visible in one place.
- Sales teams lack an easy way to estimate deal outcomes and expected revenue.
- Follow-up activities can be missed or performed inconsistently.
- Campaign cost and revenue impact are difficult to connect.

SalesPilot AI addresses these problems through a unified sales workspace.

---

## 3. Goals

### Primary Goals

1. Provide transparent lead prioritization.
2. Generate personalized sales outreach quickly.
3. Capture and visualize lead engagement.
4. Provide an interactive sales pipeline.
5. Estimate deal win probability and expected revenue.
6. Automate common sales follow-up actions.
7. Provide pipeline, funnel, engagement, and ROI analytics.
8. Deliver a responsive SaaS experience usable on desktop and mobile.

### Success Criteria

The prototype should allow an evaluator to complete the following flow:

**Lead → Score → Personalized Outreach → Engagement → Pipeline → Deal Prediction → Analytics → Automation**

---

## 4. Target Users

### Sales Representative
Needs to identify high-value prospects, contact them, and manage follow-ups.

### Sales Manager
Needs visibility into pipeline health, conversion, revenue forecasts, team activity, and ROI.

### Sales Operations / Administrator
Needs configurable automation rules and a centralized view of sales processes.

---

## 5. Core Features

### 5.1 Lead Management

Users can:

- View leads in a searchable/filterable list.
- Inspect lead details.
- View company, industry, role, company size, budget, timeline, and engagement information.
- View lead activity history.
- Track associated deals and outreach.

### 5.2 Explainable Lead Scoring

Each lead receives a score from 0–100 and a temperature:

- Hot
- Warm
- Cold

The score is based on observable sales signals including:

- Seniority
- Company size
- Industry fit
- Budget
- Purchase timeline
- Email engagement
- Other interaction signals

The system exposes score factors so that users can understand why a lead received its score.

**Implementation choice:** The prototype uses an explainable weighted scoring engine rather than claiming a trained XGBoost model. This makes the result transparent and avoids training a supervised model on insufficient synthetic/demo history.

### 5.3 AI Personalized Outreach

Users can generate personalized emails using:

- Selected lead
- Tone
- Email length

Supported tones include professional, friendly, concise, and persuasive styles.

The platform supports an OpenAI-compatible provider when an API key is configured and provides a deterministic demo fallback for evaluation environments without an API key.

Users can:

- Generate
- Edit
- Approve
- Send/simulate sending
- Track outreach status

### 5.4 Engagement Tracking

The system records sales engagement events such as:

- Email opened
- Link clicked
- Reply
- Demo requested
- Meeting booked
- Follow-up completed
- Website visit

Engagement activity is reflected in the lead timeline and can influence scoring and automation.

### 5.5 Sales Pipeline

The pipeline provides an interactive Kanban-style view across:

- New
- Qualified
- Contacted
- Engaged
- Demo
- Negotiation
- Won
- Lost

Deal cards display relevant sales information such as:

- Company/contact
- Deal value
- Lead score
- Win probability
- Risk
- Close date
- Recent activity

### 5.6 Deal Outcome Prediction

For open opportunities, SalesPilot provides:

- Win probability
- Deal value
- Expected revenue
- Risk classification
- Positive/risk factors

The prototype uses explainable sales signals and historical stage baselines rather than presenting an unsupported trained-model accuracy claim.

### 5.7 Analytics

The analytics area provides:

- Win/loss rate
- Average deal value
- Sales cycle
- Pipeline velocity
- Predicted revenue
- Won revenue
- Open pipeline
- Weighted pipeline
- Lead source analysis
- Industry performance
- Funnel conversion
- Email engagement
- Score distribution

### 5.8 ROI Analytics

Campaign-level ROI is calculated using:

**ROI = ((Revenue − Cost) / Cost) × 100**

The dashboard provides campaign cost, attributed revenue, and ROI to connect sales activity with business outcomes.

### 5.9 Automation Engine

Users can configure rules based on sales events and conditions.

Example rules include:

- High-score lead → personalized outreach + follow-up task
- Multiple email opens → increase intent + notify
- No response for a defined period → create follow-up
- Demo request → route/notify

The system records automation execution history.

### 5.10 Settings

Users can configure application-level settings and receive save confirmation feedback.

---

## 6. User Journey

### Primary Evaluator Journey

1. Open SalesPilot AI dashboard.
2. Review current sales KPIs.
3. Navigate to Leads.
4. Search/select a lead.
5. Review the explainable AI lead score.
6. Generate a personalized email.
7. Send/simulate the outreach.
8. Record an engagement event.
9. Review the updated activity timeline.
10. Open Pipeline.
11. Move/review a deal.
12. Inspect deal prediction.
13. Open Analytics.
14. Review funnel, sources, revenue, and ROI.
15. Open Automations.
16. Review rules and execution history.

---

## 7. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Display sales dashboard KPIs | High |
| FR-02 | Create/read/update/delete leads | High |
| FR-03 | Search and filter leads | High |
| FR-04 | Calculate 0–100 explainable lead score | High |
| FR-05 | Classify leads as Hot/Warm/Cold | High |
| FR-06 | Display conversion probability | High |
| FR-07 | Generate personalized outreach | High |
| FR-08 | Track outreach status | High |
| FR-09 | Record engagement events | High |
| FR-10 | Display lead engagement timeline | High |
| FR-11 | Manage pipeline stages | High |
| FR-12 | Display deal win probability | High |
| FR-13 | Calculate expected revenue | High |
| FR-14 | Display deal risk and factors | High |
| FR-15 | Display pipeline and funnel analytics | High |
| FR-16 | Calculate campaign ROI | High |
| FR-17 | Configure automation rules | High |
| FR-18 | Record automation execution history | Medium |
| FR-19 | Support responsive mobile layouts | Medium |
| FR-20 | Provide seeded demo data | High |

---

## 8. Non-Functional Requirements

### Performance
- Dashboard and navigation should remain responsive during normal prototype usage.
- API operations should provide clear loading/error states.

### Usability
- Sales information should be readable without technical knowledge.
- Scores and predictions should include understandable explanations.
- Common actions should be accessible from lead and pipeline views.

### Responsiveness
The interface should support desktop and mobile viewport sizes with responsive navigation, charts, tables, cards, and modals.

### Reliability
- Backend API and frontend should operate as an integrated application.
- Demo mode should remain functional when external AI credentials are unavailable.

### Security
- API credentials are provided through environment variables.
- Sensitive credentials are not hard-coded into the application.
- Database access is handled through the backend.

---

## 9. Technical Architecture

### Frontend
- React
- Vite
- Recharts
- Responsive SaaS dashboard UI

### Backend
- Python
- FastAPI
- SQLAlchemy
- REST API

### Database
- Relational database using SQLAlchemy
- MySQL/PyMySQL in the deployed prototype

### AI
- OpenAI-compatible provider for AI-assisted email generation
- Deterministic fallback for demo environments

### Prediction / Scoring
- Explainable weighted lead scoring
- Explainable deal prediction using sales signals and historical stage baselines

### Deployment
- Drytis AI Studio deployment

---

## 10. Data Model

The application is organized around core sales entities including:

- Leads
- Companies
- Deals
- Emails
- Engagement events
- Automation rules
- Automation executions
- Campaign/ROI information

Relationships allow lead activity to influence scoring, outreach, pipeline visibility, and analytics.

---

## 11. AI and Predictive Design Decisions

The assignment listed technologies such as XGBoost as suggested options. The prototype deliberately uses explainable scoring and prediction instead of claiming a trained ML model.

### Reason

A reliable supervised model requires sufficient historical, labeled CRM data. The prototype's seeded data is primarily demonstration data, so presenting an XGBoost model trained on it as production-quality would be misleading.

The current architecture can later replace or augment the scoring engine with a trained classifier once sufficient historical data becomes available.

---

## 12. Demo Data

The application includes seeded sales data across multiple industries and pipeline stages so the evaluator can immediately explore:

- Lead scoring
- Outreach
- Engagement
- Pipeline
- Predictions
- Analytics
- ROI
- Automation

Demo metrics are intended to demonstrate application behavior and should not be interpreted as real-world production performance benchmarks.

---

## 13. Evaluation Alignment

| Assignment Evaluation Area | SalesPilot AI Implementation |
|---|---|
| Lead scoring accuracy | Explainable scoring based on sales signals |
| Email personalization | AI-assisted contextual email generation |
| Pipeline insights | Funnel, pipeline, source, industry, and revenue analytics |
| Automation quality | Configurable trigger/action rules with execution history |
| ROI metrics | Campaign cost, revenue, and ROI calculations |
| End-to-end usability | Lead-to-revenue workflow across integrated modules |

---

## 14. Future Enhancements

With production CRM history and additional infrastructure, future versions could include:

1. XGBoost/LightGBM-based lead conversion prediction.
2. Model training and evaluation using historical won/lost opportunities.
3. PostgreSQL for production-scale deployment.
4. Model monitoring and drift detection.
5. A/B testing for outreach messages.
6. Multi-user authentication and role-based access.
7. Integration with Gmail/Outlook and CRM platforms.
8. Advanced sequence scheduling.
9. Real-time event ingestion.
10. Human-in-the-loop approval workflows.

---

## 15. Deliverables

### Live Application
https://salespilot-ai-xv2otd.drytis.dev/

### Source Repository
https://github.com/srivisnuA/salespilot-ai

### Project Documentation
This PRD documents the product goals, requirements, architecture, implementation decisions, and future roadmap.

---

## 16. Conclusion

SalesPilot AI provides an end-to-end sales automation workspace that combines lead prioritization, personalized outreach, engagement tracking, pipeline management, predictive deal insights, analytics, ROI measurement, and automation.

The prototype prioritizes transparent and demonstrable sales intelligence while maintaining a clear path toward more advanced machine-learning models when sufficient real-world historical data becomes available.
