FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-alpine@sha256:e6dae589c1c05976188fd3bd019afd091445fc533ed2ea29001beddc7368a9c8
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE=/data/notevault.db DEMO_MODE=false
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && addgroup -g 10001 notevault \
    && adduser -D -H -u 10001 -G notevault notevault \
    && mkdir /data && chown 10001:10001 /data
COPY backend/ ./backend/
COPY team.json ./
COPY --from=frontend /ui/dist ./frontend/dist
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=2)"
CMD ["gunicorn", "backend.app:create_app()", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/tmp", "--control-socket", "/tmp/gunicorn.ctl", "--access-logfile", "-"]
