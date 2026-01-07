FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ot_ids.py .
CMD ["python", "-u", "ot_ids.py"]
