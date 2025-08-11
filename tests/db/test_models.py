"""
Unit tests for database models.

This module contains tests for the database models.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.models import (
    Job, Trade, Position, AnalysisCache, Event, EventTrigger,
    JobStatus, TradeStatus, TradeDirection, StrategyType, ExecutionPriority
)


class TestJobModel:
    """Tests for the Job model."""
    
    def test_create_job(self, db_session):
        """Test creating a job."""
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            requester_id="agent123",
            requester_name="Test Agent",
            title="Test Job",
            description="This is a test job",
            status=JobStatus.PENDING,
            deadline=datetime.utcnow() + timedelta(days=1),
            payment_amount=100.0,
            payment_token="VIRTUAL",
            payment_status="unpaid",
            metadata={"priority": "high"}
        )
        
        db_session.add(job)
        db_session.commit()
        
        saved_job = db_session.query(Job).filter(Job.job_id == job_id).first()
        
        assert saved_job is not None
        assert saved_job.job_id == job_id
        assert saved_job.requester_id == "agent123"
        assert saved_job.title == "Test Job"
        assert saved_job.status == JobStatus.PENDING
        assert saved_job.payment_amount == 100.0
        assert saved_job.metadata == {"priority": "high"}
    
    def test_job_status_enum(self):
        """Test job status enum values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.ACCEPTED.value == "accepted"
        assert JobStatus.IN_PROGRESS.value == "in_progress"
        assert JobStatus.COMPLETED.value == "completed"


class TestTradeModel:
    """Tests for the Trade model."""
    
    def test_create_trade(self, db_session):
        """Test creating a trade."""
        trade_id = str(uuid4())
        job_id = str(uuid4())
        
        # Create a job first since Trade references Job
        job = Job(
            job_id=job_id,
            requester_id="agent123",
            requester_name="Test Agent",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        trade = Trade(
            trade_id=trade_id,
            market_id="market123",
            market_name="Test Market",
            outcome_id="outcome456",
            outcome_name="Yes",
            direction=TradeDirection.BUY,
            size=10.0,
            price=0.65,
            status=TradeStatus.PENDING,
            strategy=StrategyType.EVENT_DRIVEN,
            job_id=job_id,
            signal_id="signal789",
            execution_priority=ExecutionPriority.NORMAL,
            metadata={"confidence": 0.85}
        )
        
        db_session.add(trade)
        db_session.commit()
        
        saved_trade = db_session.query(Trade).filter(Trade.trade_id == trade_id).first()
        
        assert saved_trade is not None
        assert saved_trade.trade_id == trade_id
        assert saved_trade.market_id == "market123"
        assert saved_trade.direction == TradeDirection.BUY
        assert saved_trade.size == 10.0
        assert saved_trade.price == 0.65
        assert saved_trade.status == TradeStatus.PENDING
        assert saved_trade.job_id == job_id
        assert saved_trade.metadata == {"confidence": 0.85}
    
    def test_trade_direction_enum(self):
        """Test trade direction enum values."""
        assert TradeDirection.BUY.value == "buy"
        assert TradeDirection.SELL.value == "sell"


class TestPositionModel:
    """Tests for the Position model."""
    
    def test_create_position(self, db_session):
        """Test creating a position."""
        position_id = str(uuid4())
        trade_id = str(uuid4())
        job_id = str(uuid4())
        
        # Create a job first since Trade references Job
        job = Job(
            job_id=job_id,
            requester_id="agent123",
            requester_name="Test Agent",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        # Create a trade since Position references Trade
        trade = Trade(
            trade_id=trade_id,
            market_id="market123",
            market_name="Test Market",
            outcome_id="outcome456",
            outcome_name="Yes",
            direction=TradeDirection.BUY,
            size=10.0,
            price=0.65,
            status=TradeStatus.FILLED,
            strategy=StrategyType.EVENT_DRIVEN,
            job_id=job_id
        )
        db_session.add(trade)
        db_session.commit()
        
        position = Position(
            position_id=position_id,
            market_id="market123",
            market_name="Test Market",
            outcome_id="outcome456",
            outcome_name="Yes",
            direction=TradeDirection.BUY,
            size=10.0,
            entry_price=0.65,
            current_price=0.70,
            strategy=StrategyType.EVENT_DRIVEN,
            trade_id=trade_id,
            unrealized_pnl=0.5,
            unrealized_pnl_percentage=7.69,
            stop_loss=0.5,
            take_profit=0.8,
            is_active=True
        )
        
        db_session.add(position)
        db_session.commit()
        
        saved_position = db_session.query(Position).filter(Position.position_id == position_id).first()
        
        assert saved_position is not None
        assert saved_position.position_id == position_id
        assert saved_position.market_id == "market123"
        assert saved_position.direction == TradeDirection.BUY
        assert saved_position.size == 10.0
        assert saved_position.entry_price == 0.65
        assert saved_position.current_price == 0.70
        assert saved_position.unrealized_pnl == 0.5
        assert saved_position.is_active == True


class TestAnalysisCacheModel:
    """Tests for the AnalysisCache model."""
    
    def test_create_analysis_cache(self, db_session):
        """Test creating an analysis cache entry."""
        market_id = "market123"
        analysis_type = "liquidity_analysis"
        now = datetime.utcnow()
        
        analysis_cache = AnalysisCache(
            market_id=market_id,
            analysis_type=analysis_type,
            timestamp=now,
            expiration=now + timedelta(hours=1),
            data={"liquidity_score": 0.85, "details": {"depth": "high"}},
            parameters={"time_window": "1h"}
        )
        
        db_session.add(analysis_cache)
        db_session.commit()
        
        saved_cache = db_session.query(AnalysisCache).filter(
            AnalysisCache.market_id == market_id,
            AnalysisCache.analysis_type == analysis_type
        ).first()
        
        assert saved_cache is not None
        assert saved_cache.market_id == market_id
        assert saved_cache.analysis_type == analysis_type
        assert saved_cache.data["liquidity_score"] == 0.85
        assert saved_cache.data["details"]["depth"] == "high"
        assert saved_cache.parameters["time_window"] == "1h"


class TestEventModel:
    """Tests for the Event model."""
    
    def test_create_event(self, db_session):
        """Test creating an event."""
        event_id = str(uuid4())
        now = datetime.utcnow()
        
        event = Event(
            event_id=event_id,
            timestamp=now,
            category="price",
            source="polymarket",
            severity="medium",
            title="Price Alert",
            description="Significant price movement detected",
            data={"old_price": 0.65, "new_price": 0.75},
            market_id="market123",
            outcome_id="outcome456",
            processed=False
        )
        
        db_session.add(event)
        db_session.commit()
        
        saved_event = db_session.query(Event).filter(Event.event_id == event_id).first()
        
        assert saved_event is not None
        assert saved_event.event_id == event_id
        assert saved_event.category == "price"
        assert saved_event.source == "polymarket"
        assert saved_event.severity == "medium"
        assert saved_event.title == "Price Alert"
        assert saved_event.market_id == "market123"
        assert saved_event.processed == False
        assert saved_event.data["old_price"] == 0.65
        assert saved_event.data["new_price"] == 0.75


class TestEventTriggerModel:
    """Tests for the EventTrigger model."""
    
    def test_create_event_trigger(self, db_session):
        """Test creating an event trigger."""
        trigger_id = str(uuid4())
        now = datetime.utcnow()
        
        trigger = EventTrigger(
            trigger_id=trigger_id,
            name="Price Movement Alert",
            description="Detects significant price movements",
            enabled=True,
            categories=["price"],
            sources=["polymarket"],
            min_severity="low",
            conditions=[{"field": "price_change", "operator": "gt", "value": 0.05}],
            condition_type="all",
            actions=[{"action_type": "notify", "params": {"title": "Price Alert"}}],
            cooldown_seconds=300,
            created_at=now,
            updated_at=now,
            market_ids=["market123"],
            tags=["price", "alert"]
        )
        
        db_session.add(trigger)
        db_session.commit()
        
        saved_trigger = db_session.query(EventTrigger).filter(EventTrigger.trigger_id == trigger_id).first()
        
        assert saved_trigger is not None
        assert saved_trigger.trigger_id == trigger_id
        assert saved_trigger.name == "Price Movement Alert"
        assert saved_trigger.enabled == True
        assert saved_trigger.categories == ["price"]
        assert saved_trigger.min_severity == "low"
        assert len(saved_trigger.conditions) == 1
        assert saved_trigger.conditions[0]["field"] == "price_change"
        assert len(saved_trigger.actions) == 1
        assert saved_trigger.actions[0]["action_type"] == "notify"
