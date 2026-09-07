FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite lives here for now (see docs/decision_log.md - Supabase/Neon later).
# Mount a volume onto this path to persist data across container restarts.
RUN mkdir -p /app/data/local

EXPOSE 8501

ENTRYPOINT ["sh", "docker/entrypoint.sh"]
