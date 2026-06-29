FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgdal-dev gdal-bin \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Install dependencies before copying source for better layer caching.
# uv pip install -e . requires the source tree, so we export deps from the
# lock file and install them first, then install the project itself after COPY.
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-hashes --no-dev -o /tmp/requirements.txt \
    && uv pip install --system -r /tmp/requirements.txt

COPY . .
RUN uv pip install --system -e . --no-deps

EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
