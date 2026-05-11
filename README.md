# 🏢 AskBase - Internal Knowledge Base System

**AskBase** is an AI-powered internal knowledge base designed for companies to manage and query their organizational documents. Administrators upload company policies, handbooks, procedures, and other critical documents, then grant access to specific employees or roles. Employees can then ask natural language questions and get instant, accurate answers powered by RAG (Retrieval Augmented Generation) technology.

## Live Demo

- **Frontend**: https://ask-base-kappa.vercel.app
- **Backend API**: https://askbase-backend.onrender.com
- **API Docs**: https://askbase-backend.onrender.com/docs

**Demo Credentials:**
- Admin: `admin@example.com` / `admin123`
- HR: `hr@example.com` / `hr123`
- Engineer: `engineer@example.com` / `engineer123`
- Intern: `intern@example.com` / `intern123`

## Use Case

AskBase solves the problem of finding information scattered across company documents. Instead of searching through hundreds of pages of policies, handbooks, or procedures, employees can simply ask questions and get AI-powered answers instantly.

**Example Scenarios:**
- Admin uploads the employee handbook → All employees get access → "What is the sick leave policy?"
- Admin uploads engineering guidelines → Only engineers get access → "What's our code review process?"
- Admin uploads company policies → HR gets access → "How do we handle remote work requests?"

## Key Features

### For Administrators
- **Document Upload** - Upload PDF documents (policies, handbooks, procedures)
- **Access Control** - Grant document access to specific users or entire roles
- **Document Management** - View all documents, permissions, and usage
- **User Management** - Control who has access to what information

### For Employees
- **Access Granted Documents** - See only documents they have permission to view
- **AI-Powered Q&A** - Ask questions in natural language about accessible documents
- **Confidence Scores** - AI responses include confidence indicators
- **Conversation History** - Track previous questions and conversations
- **Semantic Search** - Get relevant answers even with vague questions

### Technical Features
- **RAG Technology** - FAISS vector store with semantic search for accurate retrieval
- **Secure Authentication** - JWT-based authentication with role-based access
- **Rate Limiting** - API protection against abuse
- **Modern UI** - Clean, responsive interface built with Material-UI

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL database ORM with PostgreSQL
- **FAISS** - Facebook AI Similarity Search for vector storage
- **LangChain** - Framework for LLM applications
- **Groq API** - Fast LLM inference (llama-3.3-70b-versatile)
- **Cohere API** - Fast embeddings API (embed-english-light-v3.0, free tier)
- **JWT** - JSON Web Tokens for authentication
- **Gunicorn** - Production WSGI server

### Frontend
- **React 19** - Modern React with TypeScript
- **Material-UI (MUI)** - Component library
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Vite** - Fast build tool

### Deployment
- **Frontend**: Vercel (free tier)
- **Backend**: Render (free tier)
- **Database**: PostgreSQL (Render managed)
- **Vector Store**: FAISS (ephemeral on free tier)

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- Groq API key ([Get one here](https://console.groq.com/))
- Cohere API key ([Get free tier here](https://dashboard.cohere.com/))

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd AskBase
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from example and fill in values)
cp .env.example .env

# Initialize database and seed users
python seed_users.py

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (optional, defaults to http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# Application
APP_NAME=AskBase
ENV=dev

# Security
JWT_SECRET=your-secret-key-change-this
JWT_ALGORITHM=HS256

# Database
DATABASE_URL=sqlite:///./askbase.db

# Groq API (LLM for chat responses)
GROQ_API_KEY=your-groq-api-key

# Cohere API (Embeddings - Free tier: 100 calls/min)
COHERE_API_KEY=your-cohere-api-key

# CORS
CORS_ORIGINS=http://localhost:5173

# RAG Configuration (optimized for free tier)
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_K=6
USE_MMR=true
MMR_DIVERSITY=0.3

# LLM Configuration
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1500

# File Upload
MAX_FILE_SIZE_MB=10
```

### Frontend Environment Variables

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000
```

## User Roles & Permissions

### Roles
- **Admin** - Full system access: upload documents, manage permissions, access all documents
- **HR** - Standard employee with access to HR-related documents when granted
- **Engineer** - Standard employee with access to engineering documents when granted
- **Intern** - Standard employee with limited access when granted

### Default Test Users

The system comes with seeded users for testing (create via `/seed-admin` endpoint):

| Email | Password | Role | Capabilities |
|-------|----------|------|-------------|
| admin@example.com | admin123 | admin | Upload docs, grant access, view all |
| hr@example.com | hr123 | hr | View accessible docs, ask questions |
| engineer@example.com | engineer123 | engineer | View accessible docs, ask questions |
| intern@example.com | intern123 | intern | View accessible docs, ask questions |

> **Note:** Change these passwords in production!

To create/recreate users in production:
- Visit: `https://askbase-backend.onrender.com/seed-admin?force=true`
- Or locally: `http://localhost:8000/seed-admin`

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend tests (if available)
cd backend
pytest

# Frontend linting
cd frontend
npm run lint
```

## 📁 Project Structure

```
AskBase/
├── backend/
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── core/         # Configuration and database
│   │   ├── models/       # SQLAlchemy and Pydantic models
│   │   ├── llm/          # LLM integration (Groq)
│   │   ├── vector/       # Vector store operations
│   │   └── main.py       # FastAPI application
│   ├── uploads/          # Uploaded PDF files
│   ├── vector_store/     # FAISS index storage
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/          # API client functions
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── store/        # Zustand stores
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx       # Main app component
│   └── package.json
│
└── README.md
```

## Usage Guide

### For Administrators

1. **Login** - Use admin credentials (admin@example.com / admin123)
2. **Upload Documents** - Navigate to Documents page and upload company PDFs
   - Company policies
   - Employee handbooks
   - Procedures and guidelines
   - Training materials
3. **Grant Access** - Click "Share" on any document to:
   - Grant access to specific users (e.g., user ID)
   - Grant access to entire roles (e.g., "engineer", "hr")
4. **Manage Permissions** - View and revoke access as needed
5. **Monitor Usage** - Track document status and conversations

### For Employees

1. **Login** - Use your company credentials
2. **View Accessible Documents** - See all documents you have permission to access
3. **Create Conversation** - Click on any document to start asking questions
4. **Ask Questions** - Type natural language questions:
   - "What is the remote work policy?"
   - "How many vacation days do I get?"
   - "What's the code review process?"
5. **Review History** - Access previous conversations about documents

## Permission System

### How Access Control Works

AskBase implements a flexible permission system with two types of access grants:

1. **User-Level Permissions** - Grant access to specific individual users
   - Example: Grant document "Q4 Sales Report" to user ID 5
   - Use case: Confidential documents for specific people

2. **Role-Level Permissions** - Grant access to all users with a specific role
   - Example: Grant document "Engineering Guidelines" to role "engineer"
   - Use case: Department or team-wide documents

### Access Rules

A user can access a document if ANY of these conditions are met:
- ✅ User is an **admin** (admins see all documents)
- ✅ User **uploaded** the document
- ✅ User has been granted **user-level permission**
- ✅ User's role has been granted **role-level permission**

### Example Workflows

#### Scenario 1: Company-Wide Policy
```
Admin uploads: "Company Code of Conduct.pdf"
Admin grants access to: role "hr", role "engineer", role "intern"
Result: All employees can access and ask questions
```

#### Scenario 2: Department-Specific Document
```
Admin uploads: "Engineering Best Practices.pdf"
Admin grants access to: role "engineer"
Result: Only engineers can access this document
```

#### Scenario 3: Individual Access
```
Admin uploads: "Performance Review - John Doe.pdf"
Admin grants access to: user "John Doe" (user ID: 3)
Result: Only John Doe and admins can access this document
```

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Document-level permissions
- API rate limiting
- CORS protection
- Input validation

## Deployment

### Current Deployment (Free Tier)

**Live URLs:**
- **Frontend**: https://ask-base-kappa.vercel.app (Vercel)
- **Backend**: https://askbase-backend.onrender.com (Render)
- **Database**: PostgreSQL (Render managed)


### Production Deployment Guide

#### Backend Deployment (Render)

1. **Create Render Account** - Sign up at https://render.com

2. **Create PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - Free tier selected
   - Note the Internal Database URL

3. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect your GitHub repository
   - Settings:
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `cd backend && gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
     - **Python Version**: Set environment variable `PYTHON_VERSION=3.11.9`

4. **Environment Variables** (Render Dashboard → Environment)
   ```env
   APP_NAME=AskBase
   ENV=production
   JWT_SECRET=<generate-secure-random-string>
   JWT_ALGORITHM=HS256
   GROQ_API_KEY=<your-groq-api-key>
   COHERE_API_KEY=<your-cohere-api-key>
   DATABASE_URL=<postgres-internal-url-from-render>
   CORS_ORIGINS=https://your-frontend-url.vercel.app
   CHUNK_SIZE=500
   CHUNK_OVERLAP=50
   PYTHON_VERSION=3.11.9
   ```

5. **Deploy**
   - Render auto-deploys on git push
   - Monitor logs in Render dashboard

6. **Create Users**
   - Visit: `https://your-backend.onrender.com/seed-admin?force=true`

#### **Getting API Keys**

**Groq API Key (for LLM chat responses):**
1. Go to https://console.groq.com/
2. Sign up for free account
3. Navigate to API Keys section
4. Create new API key
5. Copy and save securely

**Cohere API Key (for document embeddings - FREE):**
1. Go to https://dashboard.cohere.com/
2. Sign up for free account (no credit card required)
3. Navigate to API Keys section
4. Copy your default API key
5. **Free tier includes: 100 API calls/minute** (more than enough for most use cases)

> **Why Cohere?** We use Cohere's free embedding API instead of local models to avoid memory issues and worker timeouts on free hosting tiers. This makes document processing 10x faster and eliminates cold start problems.

#### Frontend Deployment (Vercel)

1. **Create Vercel Account** - Sign up at https://vercel.com

2. **Import Project**
   - New Project → Import Git Repository
   - Select your repository
   - Framework Preset: Vite
   - **Root Directory**: `frontend`

3. **Environment Variables**
   ```env
   VITE_API_URL=https://your-backend.onrender.com
   ```

4. **Build Settings** (automatically detected)
   - **Build Command**: `npm install && npm run build`
   - **Output Directory**: `dist`

5. **Deploy**
   - Click Deploy
   - Vercel auto-deploys on git push to main

#### DNS & Custom Domain (Optional)

1. **Vercel**: Settings → Domains → Add your domain
2. **Render**: Settings → Custom Domain → Add your API domain

### Production Considerations

#### Security
- ✅ Use strong JWT secrets (32+ characters, randomly generated)
- ✅ Enable HTTPS (Render/Vercel provide this automatically)
- ✅ Configure proper CORS origins
- ✅ Change default user passwords immediately
- ✅ Regular security audits

#### Scaling Beyond Free Tier

**Backend (Render):**
- Upgrade to paid plan for:
  - Persistent disk (vector store survives restarts)
  - More CPU/RAM (faster processing)
  - Multiple workers
  - Background jobs

**Database:**
- Monitor connection limits (free tier: 20 connections)
- Consider dedicated database for production scale
- Enable automated backups (available on paid plans)

**Vector Store:**
- For production: Use managed vector database
  - Pinecone (easy setup, generous free tier)
  - Supabase (PostgreSQL with pgvector)
  - Weaviate (self-hosted or cloud)

**Alternative: Self-Hosted**
- Deploy on your own infrastructure
- Use dedicated server for vector store
- Implement Redis for caching
- Set up Celery for background tasks

#### Free Tier Limitations

**Current Setup (Render Free + Vercel Free + Cohere Free):**
- ✅ **Cost**: $0/month (completely free)
- ✅ **Document Processing**: Fast with Cohere API (no timeouts!)
- ⚠️ **Vector Store**: Resets on backend restarts/redeploys (ephemeral filesystem)
- ✅ **Documents**: Persist in PostgreSQL (survives restarts)
- ⚠️ **Performance**: Limited CPU/RAM (512MB)
- ✅ **Uptime**: Good for demo/testing
- ⚠️ **Cold Starts**: Backend sleeps after 15 min inactivity (~30 sec wake-up)
- ✅ **Cohere API**: 100 calls/min free (enough for 100+ documents/hour)
- ⚠️ **Re-upload**: Documents need re-processing after restarts to rebuild vector store

**What Cohere Solves:**
- **Before**: 80MB model download on every restart → worker timeouts → stuck in "processing"
- **After**: External API → no downloads → documents process in 10-30 seconds → reliable

**Workarounds:**
1. Keep backend warm with uptime monitoring service (e.g., UptimeRobot)
2. Re-upload documents as needed after restarts (they're saved in DB, just need re-processing)
3. For production, upgrade to paid tier ($7-25/month) for persistent filesystem

#### Monitoring

**Render Logs:**
```bash
# View logs in Render dashboard
# Or use Render CLI
render logs -s your-service-name
```

**Health Checks:**
- Backend health: `https://your-backend.onrender.com/health`
- API docs: `https://your-backend.onrender.com/docs`

#### Backup Strategy

**Database Backups:**
- Render PostgreSQL: Automatic backups on paid plans
- Manual: Use `pg_dump` command
- Store backups in S3 or cloud storage

**Document Backups:**
- Backend files in `uploads/` directory
- On free tier: Download before restarts
- Production: Use cloud storage (S3, Azure Blob)

**Vector Store Backups:**
- `vector_store/faiss_index` directory
- Not needed if using managed vector DB
- Can regenerate from documents if lost


## Common Use Cases

### HR Department
- Employee Handbook Q&A
- Benefits and policies information
- Leave policies and procedures
- Onboarding documentation

### Engineering Teams
- Technical documentation
- Coding standards and best practices
- Architecture decisions
- API documentation

### Company-Wide
- Company policies
- Safety guidelines
- Compliance documents
- Training materials


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend library
- [LangChain](https://www.langchain.com/) - LLM application framework
- [Groq](https://groq.com/) - Fast LLM inference
- [Cohere](https://cohere.com/) - Fast, reliable embeddings API (free tier)
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search by Meta AI
- [Material-UI](https://mui.com/) - React component library

---

**AskBase** - Making company knowledge accessible to everyone, one question at a time. 🚀
