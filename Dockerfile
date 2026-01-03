FROM python:3.10-slim-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/
COPY requirements.txt .

RUN python3 -m pip install --upgrade pip setuptools \
    && pip3 install --no-cache-dir --upgrade --requirement requirements.txt

COPY . .
CMD ["python3", "-m", "BrandrdXMusic"]
