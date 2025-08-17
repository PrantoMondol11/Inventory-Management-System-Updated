# Use the official lightweight Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (if your app runs a server, e.g., Flask/FastAPI/Django)
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
