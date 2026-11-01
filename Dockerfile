FROM python:3.12-slim-trixie@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: --upgrade pip==26.2.2 && python -m pip install --no-cache-dir --only-binary=:all: -r requirements.lock && python -m pip check
RUN groupadd --gid 10001 pilot && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin pilot
COPY app.py serve.py /app/
RUN chmod 0555 /app && chmod 0444 /app/*.py /app/requirements.lock
USER 10001:10001
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import os,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/health',timeout=2); assert r.status==200 and r.read()==b'{\"status\":\"ok\",\"service\":\"connectivity-pilot\"}'"]
CMD ["python", "serve.py"]
