# Aries System Architecture

## Table of Contents
1. Project Structure
2. Client Architecture (Next.js)
3. Server Architecture (FastAPI)
4. Database Architecture
5. Authentication & Security
6. API Integration
7. Deployment Configuration

## 1. Project Structure

```
aries/
├── client/                 # Next.js Frontend Application
│   ├── src/
│   │   ├── app/           # Next.js 14 App Router
│   │   │   ├── [lang]/    # Internationalization
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── (private)/
│   │   │   │   │   │   ├── dme/
│   │   │   │   │   │   └── hme/
│   │   │   └── api/      # Next.js API routes
│   │   ├── components/    # React components
│   │   ├── contexts/      # Application contexts
│   │   ├── hooks/        # Custom hooks
│   │   ├── libs/         # Utility functions
│   │   └── views/        # Page components
│   ├── public/           # Static assets
│   ├── package.json
│   └── next.config.js
│
├── server/                # Python/FastAPI Backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   │   ├── dme/
│   │   │   ├── hme/
│   │   │   └── shared/
│   │   ├── core/         # Core functionality
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── main.py
```

## 2. Client Architecture (Next.js)

### Application Entry Point
```typescript
// client/src/app/[lang]/layout.tsx
export default function RootLayout({
  children,
  params: { lang }
}: {
  children: React.ReactNode
  params: { lang: string }
}) {
  return (
    <html lang={lang}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

### Providers Setup
```typescript
// client/src/components/Providers.tsx
export function Providers({ children }) {
  return (
    <NextAuthProvider>
      <SettingsProvider>
        <ThemeProvider>
          <FastAPIProvider>
            {children}
          </FastAPIProvider>
        </ThemeProvider>
      </SettingsProvider>
    </NextAuthProvider>
  )
}
```

### API Integration
```typescript
// client/src/libs/api-client.ts
export class APIClient {
  private baseUrl: string;
  
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL;
  }

  async request<T>(endpoint: string, options: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    return this.handleResponse(response);
  }
}
```

## 3. Server Architecture (FastAPI)

### Dependencies
```txt
# server/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
email-validator==2.1.0.post1
bcrypt==4.0.1
```

### Main Application
```python
# server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import dme, hme, shared

app = FastAPI(title="Aries API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dme.router, prefix="/api/dme", tags=["DME"])
app.include_router(hme.router, prefix="/api/hme", tags=["HME"])
app.include_router(shared.router, prefix="/api/shared", tags=["Shared"])
```

### Configuration
```python
# server/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aries"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    CORS_ORIGINS: List[str]

    class Config:
        env_file = ".env"

settings = Settings()
```

## 4. Database Architecture

### Database Configuration
```python
# server/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Migrations
```python
# server/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from alembic import context
from app.core.config import settings
from app.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = engine_from_config(configuration, prefix="sqlalchemy.")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()
```

## 5. Authentication & Security

### Security Configuration
```python
# server/app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from bcrypt import hashpw, gensalt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

### User Models
```python
# server/app/models/user.py
from sqlalchemy import Boolean, Column, String
from app.core.database import Base
from email_validator import validate_email, EmailNotValidError

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    @classmethod
    def validate_user_email(cls, email: str) -> bool:
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
```

## 6. API Integration

### API Routes
```python
# server/app/api/dme/endpoints.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.dme import Equipment, Order
from typing import List

router = APIRouter()

@router.get("/equipment", response_model=List[Equipment])
def get_equipment(db: Session = Depends(get_db)):
    # Implementation
    pass

@router.post("/orders")
def create_order(order: Order, db: Session = Depends(get_db)):
    # Implementation
    pass
```

## 7. Deployment Configuration

### Client Dockerfile
```dockerfile
# client/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

ENV NODE_ENV production
EXPOSE 3000
CMD ["node", "server.js"]
```

### Server Dockerfile
```dockerfile
# server/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  client:
    build: 
      context: ./client
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://server:8000

  server:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/aries
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: aries
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

This complete architecture document provides a comprehensive overview of the Aries system's structure and implementation. Would you like me to elaborate on any specific section or add more implementation details?