# Use Python 3.11 with full Chrome for nodriver support
FROM python:3.11-slim

# Install system dependencies and Google Chrome in one layer to save space
# Added xvfb and other libs for headed-in-docker support
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates procps libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libxshmfence1 fonts-liberation \
    xdg-utils curl xvfb xauth \
    && curl -fSsL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg > /dev/null \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m botuser

WORKDIR /home/botuser/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=botuser:botuser . .
RUN mkdir -p /home/botuser/app/data && chown botuser:botuser /home/botuser/app/data
USER botuser
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DISPLAY=:99
CMD ["python", "telegram_bot.py"]
