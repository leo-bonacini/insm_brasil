FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgdal-dev gdal-bin \
    libspatialindex-dev \
    curl wget \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install uv && uv pip install --system -e .

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
