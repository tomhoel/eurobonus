# GitHub Actions Auto-Deploy Setup

This setup enables automatic deployment to your GCP VM every time you push code to GitHub.

## 🎯 What This Does

1. You push code to GitHub → `git push origin main`
2. GitHub Actions automatically:
   - SSH into your GCP VM
   - Pull latest code
   - Rebuild and restart containers
   - Report success/failure

## 📋 Prerequisites

- Google Cloud SDK (`gcloud`) installed locally
- GitHub repository already set up (✅ you have this)

## 🚀 Setup Instructions

### Step 1: Run the Setup Script

```bash
chmod +x setup_github_deploy.sh
./setup_github_deploy.sh
```

This script will:
- Get your VM's external IP
- Generate an SSH key for GitHub Actions
- Add the public key to your VM
- Tell you what secrets to add to GitHub

### Step 2: Add GitHub Secrets

The script will output 3 values. Add them as secrets at:
**`https://github.com/YOUR_USERNAME/eurobonus/settings/secrets/actions`**

| Secret Name | Value |
|-------------|-------|
| `GCP_VM_IP` | Your VM's external IP (e.g., `34.82.123.45`) |
| `GCP_VM_USER` | Your VM username (usually your local username) |
| `GCP_SSH_KEY` | The entire private key from `~/.ssh/github_actions_eurobonus` |

### Step 3: Push and Deploy!

```bash
# Commit the new files
git add .
git commit -m "Add /deals command and auto-deploy"

# Push to trigger deployment
git push origin main
```

### Step 4: Watch the Magic

Go to: **`https://github.com/YOUR_USERNAME/eurobonus/actions`**

You'll see the deployment running! 🎉

---

## 🔧 Manual Setup (If Script Fails)

### 1. Get VM IP
```bash
gcloud compute instances describe eurobonus-bot --zone=us-west1-b --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### 2. Generate SSH Key
```bash
ssh-keygen -t ed25519 -C "github-actions@eurobonus" -f ~/.ssh/github_actions_eurobonus -N ""
```

### 3. Add Key to VM
```bash
# Copy public key
cat ~/.ssh/github_actions_eurobonus.pub

# SSH into VM and add it
gcloud compute ssh eurobonus-bot --zone=us-west1-b
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
exit
```

### 4. Add Secrets to GitHub
Go to: `https://github.com/YOUR_USERNAME/eurobonus/settings/secrets/actions`

Add:
- `GCP_VM_IP` = your VM IP
- `GCP_VM_USER` = your username  
- `GCP_SSH_KEY` = contents of `~/.ssh/github_actions_eurobonus` (private key)

---

## 📝 What Files Were Added

| File | Purpose |
|------|---------|
| `.github/workflows/deploy.yml` | GitHub Actions workflow |
| `setup_github_deploy.sh` | Helper setup script |
| `GITHUB_AUTO_DEPLOY_SETUP.md` | This documentation |

---

## 🧪 Testing

After setup, test with a small change:

```bash
# Make a tiny change
echo "# Auto-deploy test" >> README.md

# Commit and push
git add README.md
git commit -m "Test auto-deploy"
git push
```

Check the Actions tab on GitHub to see it deploy!

---

## 🔄 Current Deployment (This Time)

Since we just set this up, you still need to push once. The setup script will tell you exactly what to do, or run:

```bash
git add .
git commit -m "Add /deals command and GitHub auto-deploy"
git push origin main
```

Then watch it deploy at: `https://github.com/tomhoel/eurobonus/actions`
