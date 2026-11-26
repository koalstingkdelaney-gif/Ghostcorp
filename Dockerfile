FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    AGENCY_DB_PATH=/var/lib/ghostcorp/agency.db \
    AGENCY_SPEND_CAP_USD=0 \
    PAYMENTS_MODE=disabled \
    CALLING_ENABLED=0 \
    SMS_ENABLED=0

WORKDIR /srv/ghostcorp

RUN groupadd --system ghostcorp && useradd --system --gid ghostcorp --home-dir /srv/ghostcorp ghostcorp

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN mkdir -p /var/lib/ghostcorp && chown -R ghostcorp:ghostcorp /srv/ghostcorp /var/lib/ghostcorp
USER ghostcorp

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
