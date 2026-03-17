# base image
FROM python:3.11-slim

# set workdir
WORKDIR /app

# copy backend
COPY Backend-repo/ ./backend

# install backend dependencies
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# copy frontend build
COPY Hotel-Management-ui/build ./frontend

# expose port your backend listens on
EXPOSE 5000

# run backend server
CMD ["/bin/bash", "-c", ". backend/venv/bin/activate && python backend/app.py"]
