# Stage 1: Frontend build
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY Hotel-Management-ui/package*.json ./
RUN npm install
COPY Hotel-Management-ui/ ./
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim
WORKDIR /app
COPY Backend-repo/ ./backend
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# Copy frontend from previous stage
COPY --from=frontend-build /app/frontend/build ./frontend

EXPOSE 5000
CMD ["/bin/bash", "-c", ". backend/venv/bin/activate && python backend/app.py"]
