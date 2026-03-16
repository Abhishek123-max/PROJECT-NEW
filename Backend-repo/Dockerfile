FROM python:3.10

WORKDIR /app

COPY Backend-repo/ .

RUN pip install -r requirements.txt

EXPOSE 4000

CMD ["python3","app.py"]
