FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Expose port for Streamlit
EXPOSE 8501

# Start Streamlit app
CMD ["streamlit", "run", "app.py"] 