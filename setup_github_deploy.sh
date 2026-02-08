#!/bin/bash
# Setup GitHub Actions auto-deployment to GCP VM
# Run this ONCE to configure everything

set -e

echo "🔧 Setting up GitHub Actions auto-deployment..."
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get VM details
echo "📋 VM Configuration:"
read -p "Enter your VM name [eurobonus-bot]: " VM_NAME
VM_NAME=${VM_NAME:-eurobonus-bot}

read -p "Enter your zone [us-west1-b]: " ZONE
ZONE=${ZONE:-us-west1-b}

read -p "Enter your GitHub username: " GITHUB_USER

# Get VM external IP
echo ""
echo "🔍 Getting VM external IP..."
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "✅ VM IP: $VM_IP"

# Generate SSH key for GitHub Actions
echo ""
echo "🔑 Generating SSH key for GitHub Actions..."
KEY_PATH="~/.ssh/github_actions_eurobonus"
KEY_PATH="${KEY_PATH/#\~/$HOME}"

if [ -f "$KEY_PATH" ]; then
    echo "Key already exists at $KEY_PATH"
else
    ssh-keygen -t ed25519 -C "github-actions@eurobonus" -f "$KEY_PATH" -N ""
    echo "✅ SSH key generated"
fi

# Show public key
echo ""
echo "📋 Public key to add to VM:"
cat "${KEY_PATH}.pub"

# Add key to VM
echo ""
echo "🚀 Adding SSH key to VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="mkdir -p ~/.ssh && echo '\$(cat ${KEY_PATH}.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Test connection
echo ""
echo "🧪 Testing SSH connection..."
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" $VM_IP "echo 'SSH connection successful!'"

# Output the private key for GitHub secret
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE! Now add these GitHub Secrets:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Go to: https://github.com/$GITHUB_USER/eurobonus/settings/secrets/actions"
echo ""
echo "Add these 3 secrets:"
echo ""
echo "1️⃣  Name: GCP_VM_IP"
echo "    Value: $VM_IP"
echo ""
echo "2️⃣  Name: GCP_VM_USER"
echo "    Value: $USER"
echo ""
echo "3️⃣  Name: GCP_SSH_KEY"
echo "    Value: (copy the entire key below)"
echo "────────────────────────────────────────────────────────────────"
cat "$KEY_PATH"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "🎉 After adding secrets, push any change to deploy!"
echo ""
echo "Test it:"
echo "   git add ."
echo "   git commit -m 'Add /deals command'"
echo "   git push"
