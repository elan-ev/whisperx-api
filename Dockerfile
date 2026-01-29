FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Install required packages
ENV DEBIAN_FRONTEND=noninteractive
ENV TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=true
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python-is-python3 \
    ffmpeg \
    sudo \
    rabbitmq-server \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy project into image
WORKDIR /app
COPY . .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use tini to handle zombies
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
