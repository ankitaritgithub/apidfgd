FROM python:3.11-slim

# Set the working directory to / inside the container
WORKDIR /

# Install curl (optional, but may be needed for your app)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app  

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the root directory (/)
COPY . .

# Create a non-root user (optional for security) before changing file ownership
RUN useradd -m appuser

# Create the log file and set permissions for appuser to write to it
RUN touch /app.log && chown appuser:appuser /app.log

# Change ownership of the entire /app folder to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port for the FastAPI app
EXPOSE 8000

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
