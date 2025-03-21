FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server
COPY UI ./UI

EXPOSE 80

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "80"]
