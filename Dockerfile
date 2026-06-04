# ============================================
# Weather App – Dockerfile
# Base: slim Python 3.12 (small footprint)
# ============================================

# 1. Base image
FROM python:3.12-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy dependency list first (layer caching — faster rebuilds)
COPY requirements.txt .

# 4. Install dependencies (no cache kept = smaller image)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the app
COPY . .

# 6. Tell Docker which port Flask listens on
EXPOSE 5000

# 7. Set Flask environment variables
ENV FLASK_APP=app.py

# 8. Run the app
CMD ["python", "app.py"]