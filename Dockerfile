FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ⚠️ service-account-key.json must exist in project root
# Do NOT push this image to public registries

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
