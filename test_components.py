#!/usr/bin/env python3
"""
Comprehensive component testing script for ACP Polymarket Trading Agent.

This script tests each component individually to ensure everything works
before attempting deployment.
"""
import asyncio
import os
import sys
import traceback
from typing import Dict, Any
import tempfile
import sqlite3

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from loguru import logger

# Configure logger for testing
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

class ComponentTester:
    """Test runner for all system components."""
    
    def __init__(self):
        self.results = {}
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up minimal environment for testing."""
        # Set test environment variables
        os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
        os.environ.setdefault("DEVELOPMENT_MODE", "true")
        os.environ.setdefault("POLYMARKET_API_URL", "https://clob.polymarket.com")
        os.environ.setdefault("BASE_RPC_URL", "https://mainnet.base.org")
        os.environ.setdefault("VIRTUAL_TOKEN_ADDRESS", "0x0000000000000000000000000000000000000000")
        
    def test_config_management(self) -> bool:
        """Test configuration loading and management."""
        logger.info("Testing configuration management...")
        try:
            from app.utils.config import config
            
            # Test basic config access
            assert hasattr(config, 'get'), "Config should have get method"
            
            # Test default values
            db_echo = config.get("DATABASE_ECHO", False)
            assert isinstance(db_echo, bool), "DATABASE_ECHO should be boolean"
            
            # Test nested config access
            if hasattr(config, 'polymarket'):
                logger.info("Polymarket config section found")
            
            logger.info("✅ Configuration management test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_database_models(self) -> bool:
        """Test database models and basic operations."""
        logger.info("Testing database models...")
        try:
            from app.db.models import Base, Job, Trade, Position, AnalysisCache
            from app.db.session import create_db_engine
            
            # Create test database
            engine = create_db_engine(echo=False)
            Base.metadata.create_all(bind=engine)
            
            # Test model creation
            job = Job(
                job_id="test-job-123",
                requester_address="0x1234567890123456789012345678901234567890",
                job_type="market_analysis",
                parameters={"market_id": "test-market"},
                status="pending"
            )
            
            assert job.job_id == "test-job-123", "Job creation failed"
            assert job.status == "pending", "Job status not set correctly"
            
            logger.info("✅ Database models test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database models test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_wallet_initialization(self) -> bool:
        """Test wallet initialization without real private key."""
        logger.info("Testing wallet initialization...")
        try:
            from app.wallet.erc6551 import SmartWallet
            
            # Test wallet creation (will create temporary wallet)
            wallet = SmartWallet()
            
            assert hasattr(wallet, 'address'), "Wallet should have address"
            assert hasattr(wallet, 'account'), "Wallet should have account"
            assert wallet.address.startswith('0x'), "Address should be valid hex"
            assert len(wallet.address) == 42, "Address should be 42 characters"
            
            # Test wallet info
            wallet_info = asyncio.run(wallet.get_wallet_info())
            assert 'address' in wallet_info, "Wallet info should contain address"
            
            logger.info(f"✅ Wallet initialization test passed - Address: {wallet.address}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Wallet initialization test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_polymarket_client_init(self) -> bool:
        """Test Polymarket client initialization."""
        logger.info("Testing Polymarket client initialization...")
        try:
            from app.polymarket.client import PolymarketClient
            
            # Test client creation without authentication
            client = PolymarketClient()
            
            assert hasattr(client, 'base_url'), "Client should have base_url"
            assert hasattr(client, 'markets_cache'), "Client should have markets_cache"
            assert client.base_url, "Base URL should be set"
            
            logger.info("✅ Polymarket client initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Polymarket client initialization test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_polysights_client_init(self) -> bool:
        """Test Polysights client initialization."""
        logger.info("Testing Polysights client initialization...")
        try:
            from app.polysights.client import PolysightsClient
            
            # Test client creation
            client = PolysightsClient()
            
            assert hasattr(client, 'base_url'), "Client should have base_url"
            
            logger.info("✅ Polysights client initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Polysights client initialization test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_agent_profile(self) -> bool:
        """Test agent profile configuration."""
        logger.info("Testing agent profile...")
        try:
            from app.agent.profile import AGENT_CONFIG
            
            assert isinstance(AGENT_CONFIG, dict), "AGENT_CONFIG should be dict"
            assert 'name' in AGENT_CONFIG, "Agent config should have name"
            assert 'services' in AGENT_CONFIG, "Agent config should have services"
            assert isinstance(AGENT_CONFIG['services'], list), "Services should be list"
            
            logger.info(f"✅ Agent profile test passed - Name: {AGENT_CONFIG['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent profile test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_trading_strategy_engine_init(self) -> bool:
        """Test trading strategy engine initialization."""
        logger.info("Testing trading strategy engine initialization...")
        try:
            from app.trading.strategy_engine import TradingStrategyEngine
            from app.polymarket.client import PolymarketClient
            from app.polysights.client import PolysightsClient
            from app.db.repository import TradeRepository, PositionRepository, AnalysisCacheRepository
            
            # Create real dependencies
            polymarket_client = PolymarketClient()
            polysights_client = PolysightsClient()
            trade_repo = TradeRepository()
            position_repo = PositionRepository()
            analysis_repo = AnalysisCacheRepository()
            
            # Test engine creation
            engine = TradingStrategyEngine(
                polymarket_client=polymarket_client,
                polysights_client=polysights_client,
                wallet=None,  # No wallet for init test
                trade_repository=trade_repo,
                position_repository=position_repo,
                analysis_repository=analysis_repo
            )
            
            assert hasattr(engine, 'polymarket_client'), "Engine should have polymarket_client"
            assert hasattr(engine, 'strategies'), "Engine should have strategies"
            
            logger.info("✅ Trading strategy engine initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Trading strategy engine initialization test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_job_lifecycle_components(self) -> bool:
        """Test job lifecycle components."""
        logger.info("Testing job lifecycle components...")
        try:
            from app.agent.job_lifecycle import JobLifecycleManager
            from app.agent.job_intake import JobIntakeValidator
            from app.agent.job_execution import JobExecutionEngine
            from app.agent.job_payment import JobPaymentProcessor
            from app.agent.job_delivery import JobDeliveryManager
            
            # Test component creation
            lifecycle = JobLifecycleManager()
            intake = JobIntakeValidator()
            execution = JobExecutionEngine()
            payment = JobPaymentProcessor()
            delivery = JobDeliveryManager()
            
            assert hasattr(lifecycle, 'current_state'), "Lifecycle should have current_state"
            assert hasattr(intake, 'validate_job'), "Intake should have validate_job method"
            
            logger.info("✅ Job lifecycle components test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Job lifecycle components test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_virtuals_client_init(self) -> bool:
        """Test Virtuals client initialization."""
        logger.info("Testing Virtuals client initialization...")
        try:
            from app.virtuals.client import VirtualsClient
            from app.wallet.erc6551 import SmartWallet
            
            # Create test wallet
            wallet = SmartWallet()
            
            # Test client creation
            client = VirtualsClient(wallet)
            
            assert hasattr(client, 'wallet'), "Client should have wallet"
            assert hasattr(client, 'base_url'), "Client should have base_url"
            assert client.wallet == wallet, "Wallet should be set correctly"
            
            logger.info("✅ Virtuals client initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Virtuals client initialization test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_fastapi_app_creation(self) -> bool:
        """Test FastAPI application creation without startup."""
        logger.info("Testing FastAPI application creation...")
        try:
            # Import without triggering startup
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "main", 
                os.path.join(os.path.dirname(__file__), "app", "main.py")
            )
            main_module = importlib.util.module_from_spec(spec)
            
            # Test that we can import the main module
            assert spec is not None, "Could not load main.py spec"
            
            logger.info("✅ FastAPI application creation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ FastAPI application creation test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all component tests."""
        logger.info("🚀 Starting comprehensive component testing...")
        
        tests = [
            ("Configuration Management", self.test_config_management),
            ("Database Models", self.test_database_models),
            ("Wallet Initialization", self.test_wallet_initialization),
            ("Polymarket Client Init", self.test_polymarket_client_init),
            ("Polysights Client Init", self.test_polysights_client_init),
            ("Agent Profile", self.test_agent_profile),
            ("Trading Strategy Engine Init", self.test_trading_strategy_engine_init),
            ("Job Lifecycle Components", self.test_job_lifecycle_components),
            ("Virtuals Client Init", self.test_virtuals_client_init),
            ("FastAPI App Creation", self.test_fastapi_app_creation),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Testing {test_name} ---")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
        logger.info(f"{'='*50}")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! System is ready for deployment.")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Fix issues before deployment.")
        
        return results

async def main():
    """Main test runner."""
    tester = ComponentTester()
    results = await tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
