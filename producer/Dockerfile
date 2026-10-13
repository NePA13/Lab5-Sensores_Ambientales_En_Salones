FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir boto3
COPY simulador.py .
CMD ["python", "-u", "simulador.py"]
