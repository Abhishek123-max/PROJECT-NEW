# =========================
# Stage 1: Build React frontend
# =========================
FROM node:18 AS frontend-build

# Set working directory inside Docker
WORKDIR /app/frontend

# Copy package.json and package-lock.json
COPY Hotel-Management-ui/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of frontend source
COPY Hotel-Management-ui/ ./

# Build the frontend
RUN npm run build

# =========================
# Stage 2: Build final Python backend image
# =========================
FROM python:3.11-slim

# Set working directory for backend
WORKDIR /app

# Copy backend code
COPY Backend-repo/ ./backend

# Create virtual environment and install backend dependencies
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# Copy built frontend from first stage
COPY --from=frontend-build /app/frontend/build ./frontend

# Expose backend port (change if your Python app listens on a different port)
EXPOSE 5000

# Start the backend (adjust app.py if different)
CMD ["/bin/bash", "-c", ". backend/venv/bin/activate && python backend/app.py"]
