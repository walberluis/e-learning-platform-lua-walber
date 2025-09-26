# E-Learning System Architecture

## Project Structure Based on Package Diagram

```
e-learning/
├── infrastructure/           # Infrastructure Layer
│   ├── database/            # Database Package
│   ├── security/            # Security Package
│   └── integration/         # Integration Package
├── data_access/             # Data Access Layer
│   ├── repositories/        # Repository Package
│   └── external_services/   # External Services Package
├── business/                # Business Logic Layer
│   ├── core/               # Core Package
│   ├── learning/           # Learning Package
│   └── ai/                 # AI Package
├── presentation/            # Presentation Layer
│   ├── api/                # FastAPI endpoints
│   └── web/                # HTML/CSS frontend
├── config/                 # Configuration files
├── scripts/                # Setup scripts
└── docs/                   # Documentation
```

## Feature Implementation Plan

Implementing a complete learning path recommendation system that traverses all architectural layers:

1. **Infrastructure Layer**: Database setup, security, API integrations
2. **Data Access Layer**: User, Course, Progress repositories
3. **Business Layer**: Learning analytics, AI recommendations, user management
4. **Presentation Layer**: Web interface and API endpoints

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: HTML/CSS/JavaScript
- **Database**: PostgreSQL
- **AI/LLM**: Google Gemini API
- **Process Management**: Systemd/PM2
- **Language**: Lua scripts for business logic
