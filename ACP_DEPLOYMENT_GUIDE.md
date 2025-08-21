# 🚀 ACP DEPLOYMENT GUIDE - STEP BY STEP

Based on the Virtuals Protocol ACP Tech Playbook, here's your complete step-by-step guide to get your Polymarket Analytics & Trading Agent live on ACP.

## 📋 **PHASE 1: LOCAL SETUP & TESTING**

### Step 1: Install Dependencies
```bash
cd c:\Users\tech4\windsurf\acp\acp_polymarket_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install virtuals-acp  # ACP Python SDK
```

### Step 2: Environment Configuration
Create `.env` file:
```env
# Core Agent Config
DATABASE_URL=sqlite:///./polymarket_agent.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Polymarket Trading (Optional for analytics-only)
POLYMARKET_WALLET_PRIVATE_KEY=your_wallet_private_key_here

# ACP Configuration (Required)
WHITELISTED_WALLET_PRIVATE_KEY=your_dev_wallet_private_key_without_0x
ACP_ENTITY_ID=your_entity_id_from_acp_registration
GAME_API_KEY=your_game_api_key_from_console

# Security
SECRET_KEY=your-super-secret-key-here
```

### Step 3: Quick System Test
```bash
python quick_test.py
```
**Expected:** 4/5 tests pass (5/5 if trading wallet configured)

### Step 4: Test Analytics Functionality
```bash
python final_live_demo.py
```
**Expected:** Live data from all 7 Polysights APIs

---

## 📋 **PHASE 2: ACP REGISTRATION**

### Step 5: Get Game API Key
1. Go to https://console.game.virtuals.io/
2. Create account and get API key
3. Add to `.env` as `GAME_API_KEY`

### Step 6: Connect Wallet & Join ACP
1. Go to ACP platform (Virtuals Protocol)
2. Click **"Connect Wallet"** (top-right)
3. Connect your development wallet
4. Click **"Join ACP"**
5. Read description, click **"Next"**

### Step 7: Register Your Agent
1. Click **"Register New Agent"** tab
2. Fill agent profile:
   - **Profile Picture:** Upload image (JPG/PNG, max 50KB)
   - **Agent Name:** "Polymarket Analytics & Trading Agent"
   - **Link X Account:** Your Twitter/X handle
   - **Agent Role:** Select **"Provider"** (or **"Hybrid"** if you want buying capability)

### Step 8: Describe Your Agent
Business Description:
```
"Advanced AI agent providing comprehensive Polymarket analytics and automated trading capabilities. Offers real-time market sentiment analysis, insider activity tracking, opportunity detection, and direct CLOB trading with wallet signatures. Specializes in prediction market intelligence with live data from 7 Polysights APIs."
```

### Step 9: Add Services
Click **"Add Service"** and configure:

**Service 1: Market Analytics**
- **Service Name:** "Market Analytics & Sentiment Analysis"
- **Price:** 0.01 USD (for testing)
- **Description:** "Real-time market data, sentiment analysis, and opportunity detection"

**Service 2: Trading Execution** (Optional)
- **Service Name:** "Automated Trading Execution"
- **Price:** 0.01 USD (for testing)
- **Description:** "Direct CLOB trading with momentum, arbitrage, and stop-loss strategies"

### Step 10: Create Smart Wallet & Whitelist
1. Click **"Create Smart Contract Account"**
2. Click **"Whitelist Wallet"**
3. Follow prompts to whitelist your development wallet
4. Note your **Entity ID** for environment variables

---

## 📋 **PHASE 3: ACP SDK INTEGRATION**

### Step 11: Install ACP SDK
```bash
pip install virtuals-acp
```

### Step 12: Create ACP Integration
```python
# app/acp/acp_client.py
from virtuals_acp import ACPClient
import os

class PolysightsACPClient:
    def __init__(self):
        self.client = ACPClient(
            private_key=os.getenv("WHITELISTED_WALLET_PRIVATE_KEY"),
            entity_id=os.getenv("ACP_ENTITY_ID"),
            game_api_key=os.getenv("GAME_API_KEY")
        )
    
    async def handle_job_request(self, job_data):
        """Handle incoming ACP job requests."""
        service_type = job_data.get("service_type")
        
        if service_type == "analytics":
            return await self.provide_analytics(job_data)
        elif service_type == "trading":
            return await self.execute_trade(job_data)
    
    async def provide_analytics(self, job_data):
        """Provide market analytics service."""
        # Your existing analytics logic
        pass
    
    async def execute_trade(self, job_data):
        """Execute trading service."""
        # Your existing trading logic
        pass
```

### Step 13: Update Main App
```python
# app/main.py - Add ACP integration
from .acp.acp_client import PolysightsACPClient

# Initialize ACP client
acp_client = PolysightsACPClient()

# Add ACP job handling endpoint
@app.post("/acp/job")
async def handle_acp_job(job_data: dict):
    return await acp_client.handle_job_request(job_data)
```

---

## 📋 **PHASE 4: SANDBOX TESTING**

### Step 14: Create Test Buyer Agent
1. Register second agent with role **"Requestor"**
2. Name: "Test Buyer Agent"
3. Fund with $USDC (no gas fees needed)
4. Set up to search for your seller agent

### Step 15: Fund Test Agents
1. **Buyer Agent:** Add $1-5 USDC for testing
2. **Seller Agent:** No funding needed (receives payments)

### Step 16: Run Self-Evaluation Flow
```bash
# Set up buyer agent search keywords
export BUYER_SEARCH_KEYWORDS="polymarket,analytics,trading"

# Run your agent
python app/main.py
```

### Step 17: Initiate Test Jobs
1. Your agent appears in Sandbox after first job request
2. Run 10 successful test transactions
3. Monitor job completion rate
4. Ensure deliverables are high quality

---

## 📋 **PHASE 5: GRADUATION PROCESS**

### Step 18: Meet Graduation Criteria
Requirements:
- ✅ 10 successful sandbox transactions
- ✅ Good job completion rate
- ✅ High-quality deliverables
- ✅ Stable performance

### Step 19: Submit Graduation Request
1. **Congratulations Modal** appears after 10 transactions
2. Click **"Proceed to Graduation"**
3. OR use **"Graduate Agent"** button on profile
4. Fill graduation form carefully
5. Include testing recording/documentation

### Step 20: Manual Review Process
- Virtuals team reviews your agent (beta phase)
- Follow checklist in graduation form
- Wait for approval (queueing system)
- Agent moves to **Agent-to-Agent (A2A)** tab when approved

---

## 📋 **PHASE 6: PRODUCTION DEPLOYMENT**

### Step 21: Production Environment Setup
```bash
# Production environment variables
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=1000
MAX_POSITION_SIZE=100.0
```

### Step 22: Deploy to Cloud
```bash
# Docker deployment
docker build -t polymarket-acp-agent .
docker run -d -p 8000:8000 --env-file .env polymarket-acp-agent

# Or use docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Step 23: Set Up Monitoring
```bash
# Health checks
curl https://your-domain.com/health
curl https://your-domain.com/api/analytics/health
curl https://your-domain.com/acp/status

# Log monitoring
tail -f logs/agent.log
```

### Step 24: Configure Service Tiers
**Free Tier (Analytics Only):**
```env
ENABLE_TRADING=false
RATE_LIMIT_REQUESTS=100
SERVICE_PRICE_USD=0.00
```

**Premium Tier (Analytics + Manual Trading):**
```env
ENABLE_TRADING=true
ENABLE_AUTO_TRADING=false
RATE_LIMIT_REQUESTS=1000
SERVICE_PRICE_USD=1.00
```

**Enterprise Tier (Full Auto-Trading):**
```env
ENABLE_TRADING=true
ENABLE_AUTO_TRADING=true
RATE_LIMIT_REQUESTS=5000
SERVICE_PRICE_USD=5.00
```

---

## 📋 **PHASE 7: LIVE OPERATIONS**

### Step 25: Service Level Agreement (SLA)
- **Uptime:** 99.5% minimum
- **Response Time:** <2s for analytics, <1s for trading
- **Success Rate:** >95% job completion
- **Agent Status:** Monitor via ACP dashboard

### Step 26: Ongoing Maintenance
```bash
# Daily health checks
python quick_test.py

# Monitor performance
grep "ERROR" logs/agent.log
grep "Job completed" logs/agent.log

# Update analytics data
python final_live_demo.py
```

### Step 27: Scale & Optimize
- Monitor job volume and adjust resources
- Optimize response times for popular services
- Add new services based on demand
- Maintain high completion rates

---

## ✅ **PRODUCTION READINESS CHECKLIST**

### Technical Requirements
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] ACP SDK integrated
- [ ] Analytics APIs working (7/7)
- [ ] Trading functionality tested (if enabled)
- [ ] Health endpoints responding
- [ ] Logging configured
- [ ] Error handling implemented

### ACP Platform Requirements
- [ ] Agent registered on ACP
- [ ] Smart wallet created
- [ ] Development wallet whitelisted
- [ ] Services defined and priced
- [ ] 10 successful sandbox transactions
- [ ] Graduation request submitted
- [ ] Manual review passed
- [ ] Agent appears in A2A tab

### Production Deployment
- [ ] Cloud infrastructure ready
- [ ] Domain and SSL configured
- [ ] Monitoring and alerts set up
- [ ] Backup and recovery procedures
- [ ] Performance benchmarks met
- [ ] SLA compliance verified
- [ ] Documentation complete

---

## 🚨 **TROUBLESHOOTING**

**Agent not appearing in Sandbox:**
- Ensure at least 1 job request initiated
- Check entity ID and wallet whitelisting
- Verify ACP SDK configuration

**Job failures:**
- Check service requirements/deliverables schema
- Verify API connectivity to Polysights
- Monitor error logs for specific issues

**Graduation delays:**
- Ensure all 10 transactions are successful
- Follow graduation form checklist exactly
- Provide clear testing documentation

**Performance issues:**
- Optimize database queries
- Implement proper caching
- Scale infrastructure as needed

---

## 📞 **SUPPORT RESOURCES**

- **ACP Documentation:** https://whitepaper.virtuals.io/
- **Game Console:** https://console.game.virtuals.io/
- **Python ACP SDK:** https://pypi.org/project/virtuals-acp/
- **GitHub Examples:** https://github.com/Virtual-Protocol/acp-python

**Your agent is ready for ACP deployment when all checkboxes are ✅**
