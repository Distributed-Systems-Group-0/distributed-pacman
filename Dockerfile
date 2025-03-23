FROM python:3.12

ENV REDIS_HOST=132.164.200.4
ENV REDIS_PASSWORD=<REDIS_PASSWORD>

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server
COPY UI ./UI

EXPOSE 80

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "80"]
