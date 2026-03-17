FROM python:3.10

WORKDIR /app

COPY Backend-repo/ .
COPY Hotel-Management-ui/build /app/static

RUN pip install -r requirements.txt

EXPOSE 4000

CMD ["python3", "app.py"]
