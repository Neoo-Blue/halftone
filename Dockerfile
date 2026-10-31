FROM python:3.13-slim

# ssh is only for the Other machines desk. No secret is ever built into this image: they arrive at run time, through
# the environment or the settings page, and live in the /data volume.
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --home-dir /data --no-create-home --shell /usr/sbin/nologin paper \
    && install -d -o paper -g paper -m 700 /data

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY paper /app/paper
COPY web /app/web

ENV PAPER_DATA=/data PAPER_BIND=0.0.0.0 PYTHONUNBUFFERED=1
USER paper
VOLUME /data
EXPOSE 8095
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8095/healthz', timeout=4)"]
CMD ["python", "/app/paper/server.py"]
