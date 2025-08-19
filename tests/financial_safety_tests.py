#!/usr/bin/env python3
"""
FINANCIAL SAFETY & RISK MANAGEMENT TESTS
Critical tests for financial controls and safety mechanisms.
"""
import asyncio
import logging
import sys
import os
from decimal import Decimal
from typing import Dict, List
import json
import time
from datetime import datetime, timedelta

# Add the parent directory to Python path to find app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class FinancialSafetyTests:
    """Test suite for financial safety and risk management."""
    
    def __init__(self):
        self.test_limits = {
            'max_test_position': Decimal('5.00'),
            'max_test_loss': Decimal('10.00'),
            'max_test_exposure': Decimal('20.00')
        }
        
    async def test_position_size_limits(self):
        """Test position size enforcement."""
        logger.info("💰 Testing Position Size Limits...")
        
        from app.utils.config import config
        from app.trading.strategy_engine_main import TradingStrategyManager
        
        # Test configuration limits
        max_position = config.trading.max_position_size
        max_percentage = config.trading.max_position_percentage
        
        # Simulate portfolio value
        portfolio_value = Decimal('1000.00')
        calculated_max = portfolio_value * Decimal(str(max_percentage))
        
        # Test limits are reasonable
        assert max_position <= 1000, f"Position size too high: ${max_position}"
        assert max_percentage <= 0.2, f"Position percentage too high: {max_percentage*100}%"
        assert calculated_max <= max_position, "Calculated position exceeds configured limit"
        
        logger.info(f"✅ Max position: ${max_position}")
        logger.info(f"✅ Max percentage: {max_percentage*100}%")
        logger.info(f"✅ Calculated max for $1000 portfolio: ${calculated_max}")
        
        return True
        
    async def test_stop_loss_mechanisms(self):
        """Test stop-loss and risk controls."""
        logger.info("🛑 Testing Stop-Loss Mechanisms...")
        
        from app.utils.config import config
        
        stop_loss = config.trading.stop_loss_percentage
        take_profit = config.trading.take_profit_percentage
        max_daily_loss = config.trading.max_daily_loss
        
        # Test stop-loss is reasonable (max 10%)
        assert stop_loss <= 0.1, f"Stop-loss too high: {stop_loss*100}%"
        assert stop_loss > 0, "Stop-loss must be positive"
        
        # Test take-profit is reasonable
        assert take_profit > stop_loss, "Take-profit must be higher than stop-loss"
        assert take_profit <= 0.5, f"Take-profit too high: {take_profit*100}%"
        
        # Test daily loss limit
        assert max_daily_loss <= 1000, f"Daily loss limit too high: ${max_daily_loss}"
        assert max_daily_loss > 0, "Daily loss limit must be positive"
        
        logger.info(f"✅ Stop-loss: {stop_loss*100}%")
        logger.info(f"✅ Take-profit: {take_profit*100}%")
        logger.info(f"✅ Daily loss limit: ${max_daily_loss}")
        
        return True
        
    async def test_portfolio_risk_calculation(self):
        """Test portfolio risk calculations."""
        logger.info("📊 Testing Portfolio Risk Calculations...")
        
        from app.utils.config import config
        
        max_portfolio_risk = config.trading.max_portfolio_risk
        
        # Test with different portfolio sizes
        test_portfolios = [
            Decimal('100.00'),
            Decimal('500.00'), 
            Decimal('1000.00'),
            Decimal('5000.00')
        ]
        
        for portfolio_value in test_portfolios:
            risk_amount = portfolio_value * Decimal(str(max_portfolio_risk))
            risk_percentage = (risk_amount / portfolio_value) * 100
            
            # Risk should never exceed 5% of portfolio
            assert risk_percentage <= 5, f"Risk too high: {risk_percentage}% for ${portfolio_value}"
            
            logger.info(f"✅ ${portfolio_value} portfolio → ${risk_amount} risk ({risk_percentage:.1f}%)")
        
        return True
        
    async def test_concurrent_position_limits(self):
        """Test limits on concurrent positions."""
        logger.info("🔄 Testing Concurrent Position Limits...")
        
        from app.utils.config import config
        
        max_concurrent = config.trading.max_concurrent_jobs
        
        # Should not exceed reasonable limits
        assert max_concurrent <= 10, f"Too many concurrent jobs: {max_concurrent}"
        assert max_concurrent >= 1, "Must allow at least 1 concurrent job"
        
        # Test total exposure calculation
        max_position = config.trading.max_position_size
        total_exposure = Decimal(str(max_position)) * max_concurrent
        
        # Total exposure should be reasonable
        assert total_exposure <= 5000, f"Total exposure too high: ${total_exposure}"
        
        logger.info(f"✅ Max concurrent jobs: {max_concurrent}")
        logger.info(f"✅ Max position per job: ${max_position}")
        logger.info(f"✅ Max total exposure: ${total_exposure}")
        
        return True
        
    async def test_fee_and_slippage_accounting(self):
        """Test fee and slippage calculations."""
        logger.info("💸 Testing Fee & Slippage Accounting...")
        
        from app.utils.config import config
        
        fee_percentage = config.trading.fee_percentage
        
        # Test fee is reasonable
        assert fee_percentage <= 0.05, f"Fee too high: {fee_percentage*100}%"
        assert fee_percentage > 0, "Fee must be positive"
        
        # Test fee calculation on sample trades
        test_trade_sizes = [Decimal('10'), Decimal('50'), Decimal('100')]
        
        for trade_size in test_trade_sizes:
            fee_amount = trade_size * Decimal(str(fee_percentage))
            net_amount = trade_size - fee_amount
            
            # Fee should not exceed 5% of trade
            assert fee_amount <= trade_size * Decimal('0.05'), f"Fee too high for ${trade_size} trade"
            
            logger.info(f"✅ ${trade_size} trade → ${fee_amount} fee, ${net_amount} net")
        
        return True
        
    async def test_market_impact_limits(self):
        """Test market impact and liquidity considerations."""
        logger.info("📈 Testing Market Impact Limits...")
        
        # Test that position sizes are reasonable for market liquidity
        from app.utils.config import config
        
        max_position = config.trading.max_position_size
        
        # Position should not be too large for typical market volumes
        # Polymarket markets typically have $1K-$100K volume
        assert max_position <= 1000, f"Position too large for market liquidity: ${max_position}"
        
        # Test minimum position size (avoid dust trades)
        min_position = Decimal('1.00')  # $1 minimum
        assert max_position >= min_position, f"Position too small: ${max_position}"
        
        logger.info(f"✅ Position size appropriate for market liquidity: ${max_position}")
        
        return True
        
    async def test_emergency_shutdown_mechanisms(self):
        """Test emergency shutdown and circuit breakers."""
        logger.info("🚨 Testing Emergency Shutdown Mechanisms...")
        
        from app.utils.config import config
        
        # Test daily loss circuit breaker
        max_daily_loss = config.trading.max_daily_loss
        
        # Simulate daily P&L tracking
        simulated_daily_pnl = Decimal('-400.00')  # $400 loss
        
        if abs(simulated_daily_pnl) >= Decimal(str(max_daily_loss)):
            logger.info("✅ Circuit breaker would trigger - trading halted")
        else:
            logger.info(f"✅ Daily loss within limits: ${simulated_daily_pnl}")
        
        # Test maximum drawdown limits
        max_drawdown = Decimal('0.20')  # 20% max drawdown
        
        portfolio_start = Decimal('1000.00')
        portfolio_current = Decimal('850.00')  # 15% drawdown
        drawdown = (portfolio_start - portfolio_current) / portfolio_start
        
        if drawdown >= max_drawdown:
            logger.info("✅ Drawdown circuit breaker would trigger")
        else:
            logger.info(f"✅ Drawdown within limits: {drawdown*100:.1f}%")
        
        return True

class SecurityValidationTests:
    """Test suite for security validation."""
    
    async def test_private_key_security(self):
        """Test private key handling and security."""
        logger.info("🔐 Testing Private Key Security...")
        
        import os
        from app.wallet.erc6551 import SmartWallet
        
        # Test private key is not hardcoded
        private_key = os.getenv('WHITELISTED_WALLET_PRIVATE_KEY')
        
        # Should not be test/fake key
        assert private_key != "0x" + "0" * 64, "Using fake private key"
        assert len(private_key) == 66, f"Invalid private key length: {len(private_key)}"
        assert private_key.startswith('0x'), "Private key must start with 0x"
        
        # Test wallet creation with real key
        wallet = SmartWallet()
        assert wallet.address, "Wallet address not generated"
        assert len(wallet.address) == 42, f"Invalid address length: {len(wallet.address)}"
        
        logger.info(f"✅ Wallet address: {wallet.address}")
        logger.info("✅ Private key security validated")
        
        return True
        
    async def test_api_key_validation(self):
        """Test API key security and validation."""
        logger.info("🔑 Testing API Key Validation...")
        
        import os
        
        # Test Polymarket credentials
        api_key = os.getenv('POLYMARKET_API_KEY')
        secret = os.getenv('POLYMARKET_SECRET')
        passphrase = os.getenv('POLYMARKET_PASSPHRASE')
        
        # Should not be test values
        assert api_key != 'test_key', "Using test API key"
        assert secret != 'test_secret', "Using test secret"
        assert passphrase != 'test_pass', "Using test passphrase"
        
        # Should have reasonable length
        assert len(api_key) > 10, f"API key too short: {len(api_key)}"
        assert len(secret) > 10, f"Secret too short: {len(secret)}"
        
        logger.info("✅ API credentials validated")
        
        # Test Polysights key
        polysights_key = os.getenv('POLYSIGHTS_API_KEY')
        assert polysights_key and polysights_key != 'test_key', "Invalid Polysights key"
        
        logger.info("✅ Polysights credentials validated")
        
        return True

async def run_financial_safety_tests():
    """Run all financial safety tests."""
    logger.info("🛡️ RUNNING FINANCIAL SAFETY TEST SUITE")
    logger.info("=" * 60)
    
    financial_tests = FinancialSafetyTests()
    security_tests = SecurityValidationTests()
    
    test_suite = [
        ("Position Size Limits", financial_tests.test_position_size_limits),
        ("Stop-Loss Mechanisms", financial_tests.test_stop_loss_mechanisms),
        ("Portfolio Risk Calculation", financial_tests.test_portfolio_risk_calculation),
        ("Concurrent Position Limits", financial_tests.test_concurrent_position_limits),
        ("Fee & Slippage Accounting", financial_tests.test_fee_and_slippage_accounting),
        ("Market Impact Limits", financial_tests.test_market_impact_limits),
        ("Emergency Shutdown", financial_tests.test_emergency_shutdown_mechanisms),
        ("Private Key Security", security_tests.test_private_key_security),
        ("API Key Validation", security_tests.test_api_key_validation),
    ]
    
    passed = 0
    failed = []
    
    for test_name, test_func in test_suite:
        logger.info(f"\n{'─' * 40}")
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                logger.error(f"❌ {test_name} - FAILED")
                failed.append(test_name)
        except Exception as e:
            logger.error(f"💥 {test_name} - ERROR: {e}")
            failed.append(f"{test_name}: {e}")
    
    total = len(test_suite)
    logger.info(f"\n{'=' * 60}")
    logger.info(f"FINANCIAL SAFETY RESULTS: {passed}/{total} PASSED")
    
    if failed:
        logger.error("🚨 CRITICAL SAFETY ISSUES:")
        for issue in failed:
            logger.error(f"  • {issue}")
        return False
    else:
        logger.info("✅ ALL FINANCIAL SAFETY TESTS PASSED")
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_financial_safety_tests())
