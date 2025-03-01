FROM python:3.9-slim

# Install dependencies, set Chrome repo, and install Chrome
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && \
    apt-get clean && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get -y install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip/*

# Copy application files
COPY main.py run_func.py campaigns / /app/

# Create a directory inside /app
RUN mkdir -p /app/chrome_user_data && \
    mkdir /app/reports

# Add current directory to PYTHONPATH
ENV PYTHONPATH=/app

# Define the default command
CMD ["python", "main.py"]
