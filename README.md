# 🏢 AskBase - Internal Knowledge Base System

**AskBase** is an AI-powered internal knowledge base designed for companies to manage and query their organizational documents. Administrators upload company policies, handbooks, procedures, and other critical documents, then grant access to specific employees or roles. Employees can then ask natural language questions and get instant, accurate answers powered by RAG (Retrieval Augmented Generation) technology.

## 🎯 Use Case

AskBase solves the problem of finding information scattered across company documents. Instead of searching through hundreds of pages of policies, handbooks, or procedures, employees can simply ask questions and get AI-powered answers instantly.

**Example Scenarios:**
- Admin uploads the employee handbook → All employees get access → "What is the sick leave policy?"
- Admin uploads engineering guidelines → Only engineers get access → "What's our code review process?"
- Admin uploads company policies → HR gets access → "How do we handle remote work requests?"

## ✨ Key Features

### For Administrators
- 📤 **Document Upload** - Upload PDF documents (policies, handbooks, procedures)
- 🔐 **Access Control** - Grant document access to specific users or entire roles
- 📊 **Document Management** - View all documents, permissions, and usage
- 👥 **User Management** - Control who has access to what information

### For Employees
- 📄 **Access Granted Documents** - See only documents they have permission to view
- 💬 **AI-Powered Q&A** - Ask questions in natural language about accessible documents
- 🎯 **Confidence Scores** - AI responses include confidence indicators
- 📝 **Conversation History** - Track previous questions and conversations
- 🔍 **Semantic Search** - Get relevant answers even with vague questions

### Technical Features
- 🧠 **RAG Technology** - FAISS vector store with semantic search for accurate retrieval
- 🔐 **Secure Authentication** - JWT-based authentication with role-based access
- ⚡ **Rate Limiting** - API protection against abuse
- 🎨 **Modern UI** - Clean, responsive interface built with Material-UI

## 🏗️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL database ORM
- **FAISS** - Facebook AI Similarity Search for vector storage
- **LangChain** - Framework for LLM applications
- **Groq API** - Fast LLM inference
- **HuggingFace** - Embedding models (BAAI/bge-small-en-v1.5)
- **JWT** - JSON Web Tokens for authentication

### Frontend
- **React 19** - Modern React with TypeScript
- **Material-UI (MUI)** - Component library
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Vite** - Fast build tool

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- Groq API key ([Get one here](https://console.groq.com/))

## 🚀 Quick Start

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

# Groq API
GROQ_API_KEY=your-groq-api-key

# CORS
CORS_ORIGINS=http://localhost:5173

# Embeddings
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# RAG Configuration
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
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

## � User Roles & Permissions

### Roles
- **Admin** - Full system access: upload documents, manage permissions, access all documents
- **HR** - Standard employee with access to HR-related documents when granted
- **Engineer** - Standard employee with access to engineering documents when granted
- **Intern** - Standard employee with limited access when granted

### Default Test Users

The system comes with seeded users for testing:

| Email | Password | Role | Capabilities |
|-------|----------|------|-------------|
| admin@example.com | admin123 | admin | Upload docs, grant access, view all |
| hr@example.com | hr123 | hr | View accessible docs, ask questions |
| engineer@example.com | engineer123 | engineer | View accessible docs, ask questions |

> **Note:** Change these passwords in production!

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development

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

## 🎯 Usage Guide

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

## � Permission System

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

## �🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Document-level permissions
- API rate limiting
- CORS protection
- Input validation

## 🚀 Deployment

### Production Considerations

#### Backend Deployment

1. **Database Setup**
   ```bash
   # Use PostgreSQL for production
   DATABASE_URL=postgresql://user:password@localhost:5432/askbase_prod
   ```

2. **Environment Variables**
   - Generate secure `JWT_SECRET` (32+ characters)
   - Set `ENV=production`
   - Configure proper `CORS_ORIGINS` for your domain
   - Set up production Groq API key

3. **Server Setup**
   ```bash
   # Install production dependencies
   pip install -r requirements.txt
   
   # Run with Gunicorn (recommended for production)
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

4. **Reverse Proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Enable HTTPS** with Let's Encrypt or your organization's SSL certificate

#### Frontend Deployment

```bash
cd frontend

# Build for production
npm run build

# Deploy the 'dist' folder to:
# - Your organization's web server
# - Static hosting (S3, Azure Blob Storage, etc.)
# - CDN service
```

Update frontend `.env` for production:
```env
VITE_API_URL=https://api.your-company.com
```

### Maintenance

- **Database Backups** - Set up regular automated backups
- **Log Monitoring** - Monitor `askbase.log` for errors
- **Vector Store Backups** - Backup the `vector_store/` directory regularly
- **Update Dependencies** - Keep packages up to date for security

## 💡 Common Use Cases

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

## 🤝 Contributing

This is an internal company system. For feature requests or bug reports, please contact your IT administrator or create an issue in your internal repository.

## 📧 Support

For technical support:
- Check the API documentation at `/docs`
- Review application logs at `backend/askbase.log`
- Contact your system administrator

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend library
- [LangChain](https://www.langchain.com/) - LLM application framework
- [Groq](https://groq.com/) - Fast LLM inference
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search by Meta AI
- [Material-UI](https://mui.com/) - React component library
- [HuggingFace](https://huggingface.co/) - Embedding models and AI community

---

**AskBase** - Making company knowledge accessible to everyone, one question at a time. 🚀