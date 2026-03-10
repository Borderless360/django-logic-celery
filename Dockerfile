FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc git \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -e .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "tests/manage.py", "runserver", "0.0.0.0:8000"]
