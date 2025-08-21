# 🚀 PRODUCTION READY CHECKLIST

## 📋 **STEP 1: Environment Setup**

### Install Dependencies
```bash
# Navigate to project directory
cd c:\Users\tech4\windsurf\acp\acp_polymarket_agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Environment Variables Setup
Create `.env` file in project root:
```bash
# Copy example file
cp .env.example .env

# Edit .env file with your values:
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=sqlite:///./polymarket_agent.db

# Polymarket Trading (REQUIRED for trading functionality)
POLYMARKET_WALLET_PRIVATE_KEY=your_private_key_here
POLYMARKET_BASE_URL=https://clob.polymarket.com
POLYMARKET_WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws/

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/agent.log

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Optional: External APIs
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

---

## 📋 **STEP 2: Database Setup**

```bash
# Initialize database
python -c "from app.db.database import init_db; init_db()"

# Or run the initialization script
python app/db/init_database.py
```

---

## 📋 **STEP 3: Testing - Analytics Only**

### Test Analytics APIs
```bash
# Test live analytics data
python final_live_demo.py
```

**Expected Output:**
- ✅ 58+ recent trades from Top Buys API
- ✅ 5,482+ orderbook entries
- ✅ 366+ insider records
- ✅ 8,640+ chart records
- ✅ Market sentiment analysis
- ✅ Insider activity tracking
- ✅ Opportunity detection

### Test Analytics Endpoints
```bash
# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test endpoints:
curl http://localhost:8000/api/analytics/health
curl http://localhost:8000/api/analytics/markets
curl http://localhost:8000/api/analytics/sentiment
curl http://localhost:8000/api/analytics/insider-activity
curl http://localhost:8000/api/analytics/opportunities
```

---

## 📋 **STEP 4: Testing - Trading Functionality**

### Prerequisites for Trading
1. **Wallet Setup:**
   - Create Ethereum wallet
   - Fund with USDC on Polygon network
   - Export private key (keep secure!)
   - Set `POLYMARKET_WALLET_PRIVATE_KEY` in `.env`

2. **Network Setup:**
   - Ensure Polygon RPC access
   - Verify wallet has USDC balance

### Test Trading Client
```bash
# Test trading functionality (requires funded wallet)
python trading_demo.py
```

**Expected Output:**
- ✅ CLOB client initialized with wallet address
- ✅ Wallet balances retrieved
- ✅ Available markets fetched
- ✅ Orderbook data accessible
- ✅ Auto-trader initialized

### Test Trading Endpoints
```bash
# Test trading API endpoints
curl http://localhost:8000/api/trading/health
curl http://localhost:8000/api/trading/balances
curl http://localhost:8000/api/trading/markets
curl http://localhost:8000/api/trading/orders

# Test order placement (with valid token_id)
curl -X POST http://localhost:8000/api/trading/buy/yes \
  -H "Content-Type: application/json" \
  -d '{"token_id":"your_token_id","amount_usdc":10.0,"max_price":0.95}'
```

---

## 📋 **STEP 5: Full System Test**

### Run Complete Test Suite
```bash
# Run all tests
python run_full_tests.py
```

### Manual Integration Test
```bash
# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test complete workflow:
# 1. Get market analytics
curl http://localhost:8000/api/analytics/opportunities

# 2. Get specific market data
curl http://localhost:8000/api/analytics/markets/trending

# 3. Check trading account
curl http://localhost:8000/api/trading/balances

# 4. Place test order (small amount)
curl -X POST http://localhost:8000/api/trading/buy/yes \
  -H "Content-Type: application/json" \
  -d '{"token_id":"token_id_from_analytics","amount_usdc":5.0}'

# 5. Monitor order
curl http://localhost:8000/api/trading/orders
```

---

## 📋 **STEP 6: Production Deployment**

### Docker Deployment
```bash
# Build Docker image
docker build -t polymarket-agent .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Manual Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Health Checks
```bash
# System health
curl http://your-domain.com/health

# Analytics health
curl http://your-domain.com/api/analytics/health

# Trading health (if enabled)
curl http://your-domain.com/api/trading/health
```

---

## 📋 **STEP 7: Monitoring & Alerts**

### Log Monitoring
```bash
# Check application logs
tail -f logs/agent.log

# Check error logs
grep "ERROR" logs/agent.log

# Monitor trading activity
grep "Order placed" logs/agent.log
```

### Performance Monitoring
```bash
# Check API response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/api/analytics/markets

# Monitor database performance
sqlite3 polymarket_agent.db ".schema"
```

---

## 📋 **STEP 8: Security Checklist**

### Environment Security
- [ ] Private keys stored securely (not in code)
- [ ] Environment variables properly configured
- [ ] CORS origins restricted to known domains
- [ ] Rate limiting enabled
- [ ] HTTPS enabled in production
- [ ] Database access restricted

### Wallet Security
- [ ] Private key encrypted at rest
- [ ] Wallet funded with minimal amounts for testing
- [ ] Trading limits configured appropriately
- [ ] Stop-loss mechanisms enabled

---

## 📋 **STEP 9: Service Tier Configuration**

### Analytics Only (Free Tier)
```env
ENABLE_TRADING=false
RATE_LIMIT_REQUESTS=100
FEATURES=["analytics","sentiment","opportunities"]
```

### Analytics + Manual Trading (Premium)
```env
ENABLE_TRADING=true
ENABLE_AUTO_TRADING=false
RATE_LIMIT_REQUESTS=1000
MAX_POSITION_SIZE=100.0
```

### Full Auto-Trading (Enterprise)
```env
ENABLE_TRADING=true
ENABLE_AUTO_TRADING=true
RATE_LIMIT_REQUESTS=5000
MAX_POSITION_SIZE=1000.0
AUTO_TRADING_STRATEGIES=["momentum","arbitrage","stop_loss"]
```

---

## ✅ **PRODUCTION READY VERIFICATION**

### Final Checklist
- [ ] All environment variables configured
- [ ] Database initialized and accessible
- [ ] Analytics APIs returning live data
- [ ] Trading client connects to wallet (if enabled)
- [ ] All endpoints responding correctly
- [ ] Logs writing properly
- [ ] Error handling working
- [ ] Rate limiting active
- [ ] Security measures in place
- [ ] Monitoring configured
- [ ] Backup procedures established

### Performance Benchmarks
- [ ] Analytics endpoints < 2s response time
- [ ] Trading endpoints < 1s response time
- [ ] System handles 100+ concurrent requests
- [ ] Memory usage < 1GB under normal load
- [ ] CPU usage < 50% under normal load

---

## 🚨 **TROUBLESHOOTING**

### Common Issues

**Analytics not working:**
```bash
# Check Polysights API connectivity
curl https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api
```

**Trading not working:**
```bash
# Verify wallet private key format
python -c "from eth_account import Account; print(Account.from_key('your_key').address)"

# Check USDC balance on Polygon
# Use Polygonscan.com with your wallet address
```

**Database issues:**
```bash
# Reset database
rm polymarket_agent.db
python app/db/init_database.py
```

**Port conflicts:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Use different port
uvicorn app.main:app --port 8001
```

---

## 📞 **Support**

If you encounter issues:
1. Check logs in `logs/agent.log`
2. Verify environment variables
3. Test individual components
4. Check network connectivity
5. Verify wallet funding (for trading)

**Ready for production when all checkboxes are ✅**
