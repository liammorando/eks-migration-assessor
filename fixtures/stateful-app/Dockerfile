# BAD: Latest tag (not pinned)
FROM python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# BAD: Runs as root (no USER directive)
# BAD: No HEALTHCHECK

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]