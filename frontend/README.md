# AskBase Frontend

React frontend for the RAG-based AskBase application. Built with React 18, TypeScript, Material-UI, and TanStack Query.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Material-UI (MUI)** - Component library with dark theme
- **React Router v6** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management for authentication
- **Axios** - HTTP client

## Project Structure

```
src/
├── api/              # API client functions
│   ├── client.ts     # Axios instance with interceptors
│   ├── auth.ts       # Authentication endpoints
│   ├── documents.ts  # Document management endpoints
│   └── chat.ts       # Conversation and messaging endpoints
├── components/       # Reusable UI components
│   ├── Layout.tsx    # Navigation bar and page wrapper
│   └── ProtectedRoute.tsx  # Route guard for authentication
├── pages/            # Full page components
│   ├── LoginPage.tsx       # Login form
│   ├── DocumentsPage.tsx   # Document list and management
│   ├── ChatPage.tsx        # Chat interface
│   └── NotFoundPage.tsx    # 404 page
├── store/            # Zustand stores
│   └── authStore.ts  # Authentication state
├── types/            # TypeScript interfaces
│   └── index.ts      # All type definitions
├── config.ts         # Environment configuration
├── theme.ts          # MUI dark theme
├── App.tsx           # Router setup
└── main.tsx          # Entry point
```

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

The `.env.local` file is already configured with:
```
VITE_API_URL=http://localhost:8000
```

### 3. Update Backend CORS

Before running the frontend, update your backend's CORS configuration to allow requests from the frontend.

**In your backend `app/config.py`:**
```python
CORS_ORIGINS = [
    "http://localhost:5173",  # Add this line
    # ... other origins
]
```

Or update the existing CORS setting in `app/main.py` if you're using "*":
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace "*" with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Start Development Server

```bash
npm run dev
```

The app will be available at: **http://localhost:5173**

## Testing the Application

### Prerequisites
1. Backend server must be running on `http://localhost:8000`
2. Database seeded with test users (run `python seed_users.py` in backend)

### Test Users
- **Admin**: `admin@example.com` / `admin123`
- **Engineer**: `engineer@example.com` / `engineer123`
- **HR**: `hr@example.com` / `hr123`

### User Flow Testing

#### As Admin User:
1. **Login**
   - Navigate to http://localhost:5173
   - Login with `admin@example.com` / `admin123`
   - Should redirect to Documents page

2. **Upload Document**
   - Click "Upload Document" button
   - Select a PDF file (max 10MB)
   - Upload should succeed and document appears in list

3. **View All Documents**
   - Switch to "All Documents" tab
   - Should see all documents in the system

4. **Delete Document**
   - Click delete icon (trash can) next to a document
   - Confirm deletion
   - Document should be removed from list

5. **Start Chat**
   - Click "Start Chat" on any document
   - Should redirect to chat page
   - Type a question about the document
   - Should receive AI response

#### As Regular User (Engineer/HR):
1. **Login**
   - Login with `engineer@example.com` / `engineer123`
   - Should redirect to Documents page

2. **View Documents**
   - Should only see documents shared with this user
   - No "Upload Document" button
   - No "All Documents" tab
   - No delete buttons

3. **Start Chat**
   - Click "Start Chat" on accessible document
   - Ask questions about the document
   - Verify AI responses use document context

### Feature Checklist

#### Authentication:
- ✅ Login page loads
- ✅ Invalid credentials show error
- ✅ Successful login redirects to /documents
- ✅ Token persists across page refreshes
- ✅ Logout clears token and redirects to login
- ✅ Protected routes redirect to login if not authenticated

#### Documents Page:
- ✅ Lists accessible documents
- ✅ Shows document name, size, upload date
- ✅ Pagination works (if >10 documents)
- ✅ "Start Chat" creates conversation and navigates to chat
- ✅ Empty state shown when no documents

#### Documents Page (Admin Only):
- ✅ "Upload Document" button visible
- ✅ File selection validates PDF and size
- ✅ Upload progress shown
- ✅ Success/error messages displayed
- ✅ Tabs switch between "My Documents" and "All Documents"
- ✅ Delete button removes documents
- ✅ Confirmation dialog before deletion

#### Chat Page:
- ✅ Conversations list shown in left sidebar
- ✅ Messages displayed in conversation
- ✅ User messages right-aligned (blue)
- ✅ AI messages left-aligned (gray)
- ✅ Message input field at bottom
- ✅ Send button disabled when input empty
- ✅ "AI is typing..." indicator during API call
- ✅ Auto-scroll to new messages
- ✅ Delete conversation works
- ✅ Switch between conversations preserves state

#### Error Handling:
- ✅ Network errors show user-friendly messages
- ✅ API errors display properly
- ✅ 401 errors trigger auto-logout
- ✅ Loading states prevent multiple submissions

## Common Issues

### "Network Error" on Login
- **Cause**: Backend server not running or CORS not configured
- **Fix**: Start backend with `uvicorn app.main:app --reload` and verify CORS settings

### "Failed to load documents"
- **Cause**: Not authenticated or backend endpoint error
- **Fix**: Check browser console for errors, verify token in localStorage

### Token Expired
- **Cause**: JWT token expired (check backend JWT_EXPIRATION setting)
- **Fix**: Logout and login again, or increase token expiration in backend

### Upload Fails
- **Cause**: File too large, not PDF, or admin-only endpoint
- **Fix**: Verify file is PDF <10MB and user is admin

## Development

### Building for Production
```bash
npm run build
```

Output will be in `dist/` folder.

### Preview Production Build
```bash
npm run preview
```

### Type Checking
```bash
npm run tsc -- --noEmit
```

## API Integration

All API calls go through the Axios client in `src/api/client.ts` which:
- Adds `Authorization: Bearer <token>` header automatically
- Handles 401 errors by logging out and redirecting to login
- Uses base URL from environment variable

## State Management

- **Authentication**: Zustand store in `src/store/authStore.ts`
  - Persisted to localStorage
  - Provides `login()`, `logout()`, and `isAuthenticated` state
  
- **API Data**: TanStack Query
  - Automatic caching and background refetching
  - Loading and error states built-in
  - Query invalidation on mutations

## Next Steps

### Optional Enhancements:
1. **Share Document Feature**: Add UI for admins to share documents with specific users
2. **Dark/Light Mode Toggle**: Add theme switcher
3. **Message Markdown**: Render AI responses with markdown formatting
4. **File Preview**: Show PDF preview before chatting
5. **Conversation Search**: Search through conversation history
6. **Export Chat**: Download conversation as PDF/text
7. **Real-time Updates**: WebSocket for live message updates
8. **User Management**: Admin panel to manage users

## Notes

- JWT token includes user role for authorization
- All protected routes wrapped with `ProtectedRoute` component
- Material-UI dark theme configured in `src/theme.ts`
- TypeScript strict mode enabled for type safety
- Hot module replacement (HMR) enabled for fast development

## Support

If you encounter issues:
1. Check browser console for errors
2. Verify backend is running and accessible
3. Check Network tab in DevTools for failed requests
4. Ensure environment variables are set correctly
5. Try clearing localStorage and logging in again


Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances.

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
