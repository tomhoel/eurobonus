# GCP e2-micro Deployment Guide

Deploy the SAS EuroBonus Bot to Google Cloud Platform's **Always Free** e2-micro VM.

## Prerequisites

- Google Cloud account (free to create)
- Credit card (for verification only - you won't be charged for free tier)
- Your Telegram bot token and chat ID

---

## Step 1: Create GCP Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Name: `eurobonus-bot`
4. Click **Create**

---

## Step 2: Create the VM

1. Go to **Compute Engine** → **VM instances**
2. Click **Create Instance**
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `eurobonus-bot` |
| **Region** | `us-west1` (free tier eligible) |
| **Zone** | `us-west1-b` |
| **Machine type** | `e2-micro` (free tier) |
| **Boot disk** | Click **Change** |
| - OS | Ubuntu 22.04 LTS |
| - Size | 20 GB (standard) |
| **Firewall** | ✅ Allow HTTP, ✅ Allow HTTPS |

4. Click **Create**

---

## Step 3: Connect to VM

1. In the VM list, click **SSH** button next to your VM
2. A browser terminal will open

---

## Step 4: Install Docker

Copy and paste these commands in the SSH terminal:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
```

**Reconnect via SSH** after running `exit`.

---

## Step 5: Clone Repository

```bash
# Clone your repo
git clone https://github.com/tomhoel/eurobonus.git
cd eurobonus
```

---

## Step 6: Configure Environment

```bash
# Create data directory
mkdir -p data

# Create .env file with your credentials
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
EOF

# Edit the file to add your actual values
nano .env
```

**Important:** Replace `YOUR_BOT_TOKEN_HERE` and `YOUR_CHAT_ID_HERE` with your actual values.

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## Step 7: Copy Cookies File

You need to copy your `cookies.txt` from your Mac to the VM.

**Option A: Using the GCP Console**
1. In the SSH window, click the gear icon → **Upload file**
2. Select your `cookies.txt` file

**Option B: Using scp from your Mac**
```bash
# On your Mac
gcloud compute scp cookies.txt eurobonus-bot:~/eurobonus/ --zone=us-west1-b
```

---

## Step 8: Start the Bot

```bash
# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

You should see both `sas-monitor` and `sas-telegram-bot` running!

---

## Step 9: Verify It's Working

1. Open Telegram
2. Send `/status` to your bot
3. You should get a response!

---

## Useful Commands

```bash
# View live logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Start services
docker-compose up -d

# Check container status
docker-compose ps

# Update to latest code
git pull && docker-compose up -d --build
```

---

## Auto-Restart on VM Reboot

Docker Compose with `restart: unless-stopped` will automatically restart the containers when the VM reboots.

---

## Estimated Costs

| Resource | Free Tier Limit | Your Usage |
|----------|-----------------|------------|
| e2-micro VM | 1 instance/month | ✅ 1 instance |
| Boot disk | 30 GB | ✅ 20 GB |
| Network egress | 1 GB/month to most regions | ✅ Minimal |

**Total monthly cost: $0** (within free tier)

---

## Troubleshooting

### Bot not responding?
```bash
docker-compose logs bot
```

### Monitor not sending alerts?
```bash
docker-compose logs monitor
```

### Cookies expired?
Upload new `cookies.txt` and restart:
```bash
docker-compose restart
```

### Check disk space:
```bash
df -h
```
