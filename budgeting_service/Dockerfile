FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Expose ports for Streamlit and API
EXPOSE 8501
EXPOSE 5000

# Start both the API and Streamlit app
CMD ["sh", "-c", "python api.py & streamlit run app.py"] 