# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Build with empty API base (same origin)
ENV VITE_API_BASE=
RUN npm run build

# Stage 2: Backend with frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build from first stage
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

RUN chmod +x start.sh
CMD ["bash", "start.sh"]
