FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    MISTRAL_API_KEY=dkMKu81kFgJeP7HmIqjztosQTxyiynW6 \
    HF_TOKEN=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

# we need some build tools for installing additional python pip packages
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    software-properties-common \
    git \
    python3-dev

WORKDIR /app

# if we have a packages.txt, install it here, uncomment the two lines below
# be aware that packages.txt must have LF endings only!
COPY packages.txt packages.txt
RUN xargs -a packages.txt apt-get install --yes

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8501

COPY . .

# Définir la commande pour exécuter Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
