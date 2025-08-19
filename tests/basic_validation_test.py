#!/usr/bin/env python3
"""
BASIC VALIDATION TEST - Actually working test that can run
Tests basic system components without requiring real API credentials
"""
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all core modules can be imported."""
    logger.info("🔍 Testing Core Module Imports...")
    
    try:
        from app.utils.config import config
        logger.info("✅ Config module imported")
    except Exception as e:
        logger.error(f"❌ Config import failed: {e}")
        return False
    
    try:
        from app.db.models import Job, Trade, Position
        logger.info("✅ Database models imported")
    except Exception as e:
        logger.error(f"❌ Database models import failed: {e}")
        return False
    
    try:
        from app.wallet.erc6551 import SmartWallet
        logger.info("✅ Wallet module imported")
    except Exception as e:
        logger.error(f"❌ Wallet import failed: {e}")
        return False
    
    return True

def test_config_validation():
    """Test configuration loading and validation."""
    logger.info("⚙️ Testing Configuration...")
    
    try:
        from app.utils.config import config
        
        # Test basic config access
        assert hasattr(config, 'trading'), "Missing trading config"
        assert hasattr(config, 'polymarket'), "Missing polymarket config"
        assert hasattr(config, 'database'), "Missing database config"
        
        # Test trading config has required fields
        trading_config = config.trading
        required_fields = ['max_position_size', 'stop_loss_percentage', 'max_daily_loss']
        
        for field in required_fields:
            assert hasattr(trading_config, field), f"Missing trading config field: {field}"
        
        logger.info("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False

def test_database_models():
    """Test database model creation."""
    logger.info("🗄️ Testing Database Models...")
    
    try:
        from app.db.models import Job, Trade, Position, JobStatus
        
        # Test model creation
        test_job = Job(
            job_id="test_123",
            requester_id="0x" + "1" * 40,
            title="Test Job",
            description="Test Description",
            job_type="trade_execution",
            status=JobStatus.PENDING,
            parameters="{}"
        )
        
        assert test_job.job_id == "test_123"
        assert test_job.status == JobStatus.PENDING
        
        logger.info("✅ Database models working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database models test failed: {e}")
        return False

def test_environment_check():
    """Check environment setup."""
    logger.info("🌍 Testing Environment Setup...")
    
    # Check if we're in development mode (no real credentials required)
    has_real_creds = all([
        os.getenv('POLYMARKET_API_KEY') and os.getenv('POLYMARKET_API_KEY') != 'test_key',
        os.getenv('POLYMARKET_SECRET') and os.getenv('POLYMARKET_SECRET') != 'test_secret',
        os.getenv('WHITELISTED_WALLET_PRIVATE_KEY') and not os.getenv('WHITELISTED_WALLET_PRIVATE_KEY').startswith('0x' + '0' * 60)
    ])
    
    if has_real_creds:
        logger.info("✅ Real production credentials detected")
    else:
        logger.info("⚠️ Using test/development credentials")
    
    return True

def run_basic_validation():
    """Run all basic validation tests."""
    logger.info("🧪 RUNNING BASIC VALIDATION TESTS")
    logger.info("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config_validation),
        ("Database Models", test_database_models),
        ("Environment Check", test_environment_check),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'─' * 30}")
        logger.info(f"Testing: {test_name}")
        
        try:
            result = test_func()
            if result:
                passed += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                logger.error(f"❌ {test_name} - FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} - ERROR: {e}")
    
    logger.info(f"\n{'=' * 50}")
    logger.info(f"RESULTS: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        logger.info("🎉 ALL BASIC TESTS PASSED")
        return True
    else:
        logger.error(f"🚨 {total - passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_basic_validation()
    sys.exit(0 if success else 1)
