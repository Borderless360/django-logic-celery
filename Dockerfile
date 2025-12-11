FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Install the package in development mode
RUN pip install -e .

# Disable bytecode compilation
ENV PYTHONDONTWRITEBYTECODE=1
# Unbuffer stdout and stderr
ENV PYTHONUNBUFFERED=1
# Set default command
CMD ["python", "tests/manage.py", "runserver", "0.0.0.0:8000"]

