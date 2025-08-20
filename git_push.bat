@echo off
echo Adding all files to git...
git add .

echo Committing changes...
git commit -m "feat: Add comprehensive trading functionality and enhanced analytics

- Implement CLOB API trading client with wallet signatures (no KYC required)
- Add automated trading strategies: momentum, arbitrage, stop-loss
- Integrate py-clob-client SDK for direct Polymarket trading
- Create trading API endpoints for manual and automated trading
- Add real-time market analytics with live Polysights data integration
- Implement sentiment analysis, insider tracking, and opportunity detection
- Update agent manifest to support analytics + trading capabilities
- Add comprehensive demos for both analytics and trading functionality
- Support three service tiers: Analytics Only, Manual Trading, Auto-Trading
- Add portfolio risk management and position monitoring
- Integrate all 7 Polysights APIs for complete market intelligence"

echo Pushing to GitHub...
git push origin main

echo Done! All changes pushed to GitHub.
pause
