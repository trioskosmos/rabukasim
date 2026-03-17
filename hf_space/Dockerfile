# Use Python 3.12 slim for a smaller image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Install system dependencies including Rust toolchain requirements and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Copy the entire application early
COPY . .

# Ensure the user owns the app directory
RUN chown -R 1000:1000 /app

# Build the Rust engine and launcher
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache . && \
    python tools/sync_launcher_assets.py && \
    cd launcher && cargo build --release

# Diagnostic: Verify files are present
RUN ls -la /app && ls -la /app/launcher/target/release/loveca_launcher || echo "LAUNCHER BINARY MISSING"

# Compile card data
RUN python -m compiler.main

# Create a non-privileged user
RUN useradd -m -u 1000 user_tmp || true
RUN chown -R 1000:1000 /app

USER 1000
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port
EXPOSE 7860

# Run the high-performance Rust server
CMD ["./launcher/target/release/loveca_launcher"]
