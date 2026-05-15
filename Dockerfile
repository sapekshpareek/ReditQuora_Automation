FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) Since we are using the Playwright image, browsers are pre-installed.
# But running playwright install just in case of version mismatch between pip and image.
RUN playwright install chromium

# Copy the rest of the application
COPY . /app/

# Expose port (Cloud Run uses PORT environment variable, defaults to 8080)
ENV PORT=8080
EXPOSE $PORT

# Command to run the application using uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
