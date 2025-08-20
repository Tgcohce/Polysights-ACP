# 📋 STEP-BY-STEP PRODUCTION SETUP GUIDE

## 🔑 **1. GET POLYMARKET API CREDENTIALS**

### **Where to Go:**
- Visit: https://clob.polymarket.com/
- Click "Sign Up" or "Login" in top right

### **How to Get API Keys:**
1. **Create Account**: Sign up with email and verify
2. **Complete KYC**: Upload ID and complete verification (required for API access)
3. **Navigate to API Section**: 
   - Go to Account Settings → API Keys
   - Or look for "Developers" or "API" in the menu
4. **Generate API Credentials**:
   - Click "Create New API Key"
   - Save these 3 values securely:
     - `API Key` (public identifier)
     - `Secret` (private signing key)
     - `Passphrase` (additional security phrase)
5. **Whitelist IP Address**: Add your server's IP address to allowed IPs

### **What You'll Get:**
```bash
POLYMARKET_API_KEY=pk_live_1234567890abcdef...
POLYMARKET_SECRET=sk_live_abcdef1234567890...
POLYMARKET_PASSPHRASE=your_secure_passphrase_here
```

---

## 📊 **2. GET POLYSIGHTS ANALYTICS API**

### **Where to Go:**
- Visit: https://app.polysights.xyz/
- Click "Sign Up" or "Get Started"

### **How to Get API Key:**
1. **Create Account**: Register with email
2. **Choose Plan**: Select appropriate subscription tier
3. **Access API Section**:
   - Go to Dashboard → API Keys
   - Or Settings → Developer Tools
4. **Generate API Key**:
   - Click "Generate New Key"
   - Copy the API key immediately (won't be shown again)
5. **Test API Access**: Use their API documentation to test

### **What You'll Get:**
```bash
POLYSIGHTS_API_KEY=ps_1234567890abcdef...
```

---

## 🤖 **3. GET VIRTUALS PLATFORM CREDENTIALS**

### **Where to Go:**
- Visit: https://app.virtuals.io/
- Look for "Agent Registration" or "Developer Portal"

### **How to Register Agent:**
1. **Create Developer Account**: Sign up for platform access
2. **Register Your Agent**:
   - Go to "Create Agent" or "Register Agent"
   - Fill in agent details:
     - Name: "ACP Polymarket Trading Agent"
     - Description: Your agent's purpose
     - Category: "Trading" or "Finance"
3. **Get Agent ID**: Platform will assign unique agent ID
4. **Generate API Key**: Create API key for platform integration
5. **Configure Webhooks**: Set up callback URLs for job notifications

### **What You'll Get:**
```bash
VIRTUALS_API_KEY=virt_1234567890abcdef...
AGENT_ID=agent_abc123def456...
```

---

## 🌐 **4. SETUP BLOCKCHAIN RPC PROVIDER**

### **Option A: Alchemy (Recommended)**
1. **Visit**: https://www.alchemy.com/
2. **Sign Up**: Create free account
3. **Create App**:
   - Click "Create App"
   - Choose "Base" network
   - Select "Mainnet" for production
4. **Get RPC URL**:
   - Go to app dashboard
   - Copy the HTTPS URL
   - Format: `https://base-mainnet.g.alchemy.com/v2/YOUR_KEY`

### **Option B: Infura**
1. **Visit**: https://infura.io/
2. **Create Project**: Choose "Web3 API"
3. **Select Base Network**: Add Base mainnet
4. **Copy Endpoint**: Get HTTPS endpoint URL

### **Option C: QuickNode**
1. **Visit**: https://www.quicknode.com/
2. **Create Endpoint**: Choose Base mainnet
3. **Copy URL**: Get your dedicated RPC URL

### **What You'll Get:**
```bash
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
```

---

## 💰 **5. CREATE PRODUCTION WALLET**

### **Generate New Wallet:**
```bash
# Option 1: Using Python
python -c "
from eth_account import Account
account = Account.create()
print(f'Address: {account.address}')
print(f'Private Key: {account.key.hex()}')
"

# Option 2: Using MetaMask
# Create new wallet in MetaMask
# Export private key from Account Details
```

### **Security Steps:**
1. **Save Private Key Securely**:
   - Use password manager or hardware wallet
   - NEVER commit to git or share
2. **Fund Wallet**:
   - Send 0.1-0.5 ETH for gas fees
   - Send VIRTUAL tokens for trading
3. **Test Wallet**:
   - Verify you can sign transactions
   - Check balances on Base explorer

### **What You'll Set:**
```bash
WHITELISTED_WALLET_PRIVATE_KEY=0x1234567890abcdef... # 64 characters
```

---

## 🗄️ **6. SETUP PRODUCTION DATABASE**

### **Option A: Local PostgreSQL**
```bash
# Install PostgreSQL
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
CREATE DATABASE acp_polymarket_prod;
CREATE USER acp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE acp_polymarket_prod TO acp_user;
```

### **Option B: Cloud Database (Recommended)**

#### **Supabase (Free tier available):**
1. Visit: https://supabase.com/
2. Create project
3. Get connection string from Settings → Database

#### **AWS RDS:**
1. Go to AWS Console → RDS
2. Create PostgreSQL instance
3. Configure security groups
4. Get connection endpoint

#### **Google Cloud SQL:**
1. Go to Google Cloud Console → SQL
2. Create PostgreSQL instance
3. Set up connection

### **What You'll Get:**
```bash
DATABASE_URL=postgresql://user:password@host:5432/database_name
```

---

## 🛡️ **7. SETUP MONITORING & ALERTS**

### **Sentry (Error Tracking):**
1. **Visit**: https://sentry.io/
2. **Create Account**: Sign up for free
3. **Create Project**:
   - Choose "Python" platform
   - Name it "ACP-Polymarket-Agent"
4. **Get DSN**: Copy the DSN from project settings
5. **Install SDK**: `pip install sentry-sdk`

### **Discord Webhooks (Alerts):**
1. **Open Discord**: Go to your server
2. **Server Settings** → Integrations → Webhooks
3. **Create Webhook**:
   - Name: "ACP Trading Alerts"
   - Choose channel for alerts
4. **Copy Webhook URL**

### **Slack Webhooks (Optional):**
1. **Go to**: https://api.slack.com/apps
2. **Create App**: Choose your workspace
3. **Incoming Webhooks**: Enable and create webhook
4. **Copy Webhook URL**

### **What You'll Get:**
```bash
SENTRY_DSN=https://your_key@sentry.io/project_id
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## ⚙️ **8. CONFIGURE ENVIRONMENT**

### **Create Production Environment File:**
```bash
# Copy template
cp .env.production.template .env.production

# Edit with your values
nano .env.production  # or use any text editor
```

### **Fill in ALL Values:**
- Replace every `your_*_here` with actual credentials
- Set appropriate financial limits
- Configure production settings

### **Validate Configuration:**
```bash
# Test configuration loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
print('✅ All required vars set:')
required = ['POLYMARKET_API_KEY', 'POLYSIGHTS_API_KEY', 'BASE_RPC_URL']
for var in required:
    print(f'{var}: {\"✅\" if os.getenv(var) else \"❌\"}')"
```

---

## 🧪 **9. RUN PRODUCTION TESTS**

### **Load Environment:**
```bash
# Windows PowerShell
Get-Content .env.production | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Linux/Mac
export $(cat .env.production | xargs)
```

### **Run Test Suites:**
```bash
# Basic validation
python tests/basic_validation_test.py

# Financial safety tests
python tests/financial_safety_tests.py

# Full production test suite
python tests/production_test_suite.py
```

### **Expected Results:**
- All tests should pass (100% success rate)
- Any failures indicate missing credentials or configuration issues

---

## 🏗️ **10. DEPLOY TO PRODUCTION**

### **Option A: Cloud Deployment (Recommended)**

#### **Heroku:**
```bash
# Install Heroku CLI
# Create app
heroku create acp-polymarket-agent

# Set environment variables
heroku config:set POLYMARKET_API_KEY=your_key
heroku config:set POLYMARKET_SECRET=your_secret
# ... set all other vars

# Deploy
git push heroku main
```

#### **AWS/GCP/Azure:**
1. Create VM instance
2. Install Python and dependencies
3. Upload code and set environment variables
4. Configure reverse proxy (nginx)
5. Setup SSL certificate
6. Configure auto-restart (systemd)

### **Option B: Local Production:**
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production settings
export PRODUCTION_MODE=true
python app/main.py
```

---

## 📊 **11. MONITORING SETUP**

### **Health Check Endpoint:**
- Your app will have `/health` endpoint
- Monitor this URL for uptime

### **Log Monitoring:**
```bash
# View logs
tail -f logs/app.log

# Monitor errors in Sentry dashboard
# Check Discord/Slack for alerts
```

### **Financial Monitoring:**
- Check daily P&L reports
- Monitor position sizes and risk metrics
- Set up alerts for large losses

---

## 🚨 **12. EMERGENCY PROCEDURES**

### **Emergency Shutdown:**
```bash
# Set emergency flag
export EMERGENCY_SHUTDOWN=true

# Or modify environment file
echo "EMERGENCY_SHUTDOWN=true" >> .env.production

# Restart application to pick up change
```

### **Quick Fixes:**
```bash
# Check system status
python tests/basic_validation_test.py

# Restart application
sudo systemctl restart acp-agent  # if using systemd

# Check logs for errors
tail -100 logs/app.log
```

---

## ✅ **VERIFICATION CHECKLIST**

Before going live, verify each step:

```bash
# 1. Test API connections
curl -H "Authorization: Bearer $POLYMARKET_API_KEY" https://clob.polymarket.com/markets

# 2. Test database connection
python -c "from app.db.session import create_db_engine; print('DB OK' if create_db_engine() else 'DB FAIL')"

# 3. Test wallet
python -c "from app.wallet.erc6551 import SmartWallet; w=SmartWallet(); print(f'Wallet: {w.address}')"

# 4. Run full test suite
python tests/production_test_suite.py
```

**🎯 All tests must pass before production deployment!**
