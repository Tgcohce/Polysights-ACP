# 🚀 PRE-PRODUCTION CHECKLIST

## **CRITICAL: Complete ALL items before production deployment**

---

## 🔑 **1. API CREDENTIALS & ACCOUNTS**

### **Polymarket CLOB API**
- [ ] **Create Account**: Sign up at https://clob.polymarket.com/
- [ ] **Generate API Keys**: Create API key, secret, and passphrase
- [ ] **Set Environment Variables**:
  ```bash
  POLYMARKET_API_KEY=your_actual_api_key_here
  POLYMARKET_SECRET=your_actual_secret_here  
  POLYMARKET_PASSPHRASE=your_actual_passphrase_here
  ```
- [ ] **Test Authentication**: Verify API credentials work with test calls

### **Polysights Analytics API**
- [ ] **Create Account**: Sign up at https://app.polysights.xyz/
- [ ] **Generate API Key**: Get your analytics API key
- [ ] **Set Environment Variable**:
  ```bash
  POLYSIGHTS_API_KEY=your_polysights_api_key_here
  ```

### **Virtuals Protocol Platform**
- [ ] **Register Agent**: Sign up at https://app.virtuals.io/
- [ ] **Get API Credentials**: Obtain platform API key
- [ ] **Set Environment Variables**:
  ```bash
  VIRTUALS_API_KEY=your_virtuals_api_key_here
  AGENT_ID=your_unique_agent_id_here
  ```

### **Blockchain RPC Provider**
- [ ] **Choose Provider**: Alchemy, Infura, or QuickNode
- [ ] **Create Project**: Set up Base network project
- [ ] **Get RPC URL**: Copy your Base mainnet RPC URL
- [ ] **Set Environment Variable**:
  ```bash
  BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
  ```

---

## 💰 **2. WALLET & FUNDING**

### **Production Wallet Setup**
- [ ] **Generate New Wallet**: Create dedicated wallet for this agent
- [ ] **Secure Private Key**: Store private key securely (hardware wallet/vault)
- [ ] **Set Environment Variable**:
  ```bash
  WHITELISTED_WALLET_PRIVATE_KEY=0xYOUR_64_CHARACTER_PRIVATE_KEY
  ```
- [ ] **Verify Address**: Confirm wallet address is correct

### **Funding Requirements**
- [ ] **ETH for Gas**: Add 0.1-0.5 ETH to wallet for transaction fees
- [ ] **VIRTUAL Tokens**: Add sufficient VIRTUAL tokens for trading
- [ ] **Test Small Amount**: Start with small amounts ($50-100) for initial testing
- [ ] **Verify Balances**: Confirm all tokens are in wallet

---

## 🗄️ **3. DATABASE SETUP**

### **Production Database**
- [ ] **PostgreSQL Setup**: Install/configure PostgreSQL (NOT SQLite)
- [ ] **Create Database**: Create production database
- [ ] **Set Connection String**:
  ```bash
  DATABASE_URL=postgresql://user:pass@host:5432/acp_polymarket_prod
  ```
- [ ] **Run Migrations**: Execute database schema creation
- [ ] **Test Connection**: Verify database connectivity
- [ ] **Setup Backups**: Configure automated database backups

---

## 🛡️ **4. SECURITY & MONITORING**

### **Error Tracking**
- [ ] **Sentry Account**: Create account at https://sentry.io/
- [ ] **Create Project**: Set up error tracking project
- [ ] **Set Environment Variable**:
  ```bash
  SENTRY_DSN=https://your_key@sentry.io/project_id
  ```

### **Alerting Setup**
- [ ] **Discord Webhook**: Create Discord webhook for alerts
- [ ] **Slack Integration**: Setup Slack webhook (optional)
- [ ] **Set Environment Variables**:
  ```bash
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
  ```

---

## ⚙️ **5. CONFIGURATION**

### **Environment File Setup**
- [ ] **Copy Template**: `cp .env.production.template .env.production`
- [ ] **Fill All Values**: Replace ALL placeholder values with real credentials
- [ ] **Validate Config**: Ensure no test/fake values remain
- [ ] **Set Production Mode**:
  ```bash
  PRODUCTION_MODE=true
  ```

### **Financial Safety Limits**
- [ ] **Review Position Limits**: Confirm max position size is appropriate
- [ ] **Set Daily Loss Limits**: Configure maximum daily loss tolerance
- [ ] **Configure Stop-Loss**: Set stop-loss percentage (recommend ≤10%)
- [ ] **Validate Risk Controls**: Ensure all financial safeguards are active

---

## 🧪 **6. TESTING & VALIDATION**

### **Pre-Production Testing**
- [ ] **Run Basic Tests**: Execute `python tests/basic_validation_test.py`
- [ ] **Test API Connections**: Verify all API credentials work
- [ ] **Database Tests**: Confirm database operations function
- [ ] **Wallet Tests**: Test transaction signing and validation

### **Production Test Suite**
- [ ] **Load Environment**: `export $(cat .env.production | xargs)`
- [ ] **Run Full Tests**: `python tests/production_test_suite.py`
- [ ] **Financial Safety Tests**: `python tests/financial_safety_tests.py`
- [ ] **100% Pass Rate**: ALL tests must pass before deployment

---

## 🏗️ **7. INFRASTRUCTURE**

### **Server Setup**
- [ ] **Cloud Provider**: Choose AWS, GCP, or Azure
- [ ] **Server Instance**: Deploy appropriate server size
- [ ] **SSL Certificate**: Install valid SSL certificate
- [ ] **Firewall Rules**: Configure security groups/firewall
- [ ] **Load Balancer**: Setup load balancing (if needed)

### **Application Deployment**
- [ ] **Docker Images**: Build production Docker containers
- [ ] **Environment Variables**: Set all production env vars on server
- [ ] **Health Checks**: Configure application health endpoints
- [ ] **Log Management**: Setup centralized logging
- [ ] **Monitoring**: Deploy system monitoring tools

---

## 📊 **8. PAPER TRADING PHASE** (HIGHLY RECOMMENDED)

### **Pre-Live Testing**
- [ ] **Enable Paper Trading**: Set `PAPER_TRADING_MODE=true`
- [ ] **Run for 1-2 Weeks**: Monitor performance without real money
- [ ] **Track Metrics**: Monitor P&L, win rate, drawdown, performance
- [ ] **Validate Strategies**: Ensure trading logic is profitable
- [ ] **Fix Issues**: Address any problems discovered
- [ ] **Team Review**: Have team review paper trading results

---

## 🚀 **9. PRODUCTION DEPLOYMENT**

### **Final Pre-Launch**
- [ ] **Code Review**: Complete final code review
- [ ] **Security Audit**: Review all security measures
- [ ] **Backup Plan**: Prepare rollback procedures
- [ ] **Team Notification**: Alert team of deployment
- [ ] **Emergency Contacts**: Ensure emergency shutdown procedures ready

### **Launch Process**
- [ ] **Deploy Application**: Deploy to production environment
- [ ] **Verify Deployment**: Confirm all services running
- [ ] **Run Smoke Tests**: Execute basic functionality tests
- [ ] **Start Small**: Begin with minimal position sizes
- [ ] **Monitor Closely**: Watch system for first 24-48 hours

---

## 📈 **10. POST-DEPLOYMENT**

### **Ongoing Monitoring**
- [ ] **24/7 Monitoring**: Monitor system continuously for first week
- [ ] **Performance Tracking**: Track all key business metrics
- [ ] **Error Monitoring**: Watch for and address any errors
- [ ] **Financial Tracking**: Monitor P&L and risk metrics
- [ ] **User Feedback**: Collect and address any issues

### **Maintenance Schedule**
- [ ] **Daily Health Checks**: Verify system health daily
- [ ] **Weekly Performance Review**: Analyze trading performance
- [ ] **Monthly Security Review**: Review and rotate credentials
- [ ] **Quarterly Updates**: Plan feature updates and improvements

---

## 🚨 **CRITICAL SUCCESS CRITERIA**

### **Must Have Before Launch:**
1. ✅ **ALL API credentials working and validated**
2. ✅ **Production wallet funded and tested**
3. ✅ **Database production-ready with backups**
4. ✅ **100% test pass rate on production test suite**
5. ✅ **Financial safety limits configured and tested**
6. ✅ **Monitoring and alerting fully operational**
7. ✅ **Paper trading results satisfactory (if applicable)**
8. ✅ **Emergency shutdown procedures tested**

### **Launch Readiness Verification:**
```bash
# Final verification commands
export $(cat .env.production | xargs)
python tests/production_test_suite.py
python tests/financial_safety_tests.py
```

**🎯 TARGET: 100% pass rate on ALL tests before production deployment**

---

## 📞 **EMERGENCY PROCEDURES**

### **Emergency Shutdown:**
```bash
# Immediate shutdown commands
export EMERGENCY_SHUTDOWN=true
# Stop all trading activities
# Close all open positions
# Notify team via emergency channels
```

### **Incident Response:**
1. **Assess Impact**: Determine severity and scope
2. **Immediate Action**: Take steps to minimize damage  
3. **Team Notification**: Alert relevant team members
4. **Documentation**: Document incident and response
5. **Post-Mortem**: Conduct thorough post-incident review

---

**🚀 READY FOR PRODUCTION when ALL checkboxes are ✅**

**⚠️ DO NOT DEPLOY TO PRODUCTION until EVERY item is completed and verified**
