FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data
ENV PORT=5000
ENV FLASK_DEBUG=0
ENV BEHIND_PROXY=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py database.py network.py words.py ./
COPY templates/ templates/
COPY static/ static/

RUN mkdir -p /data

VOLUME ["/data"]
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]