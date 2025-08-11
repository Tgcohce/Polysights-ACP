"""
Unit tests for database repositories.

This module contains tests for the database repository classes.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.models import (
    Job, Trade, Position, AnalysisCache, Event, EventTrigger,
    JobStatus, TradeStatus, TradeDirection, StrategyType
)
from app.db.repository import (
    BaseRepository, JobRepository, TradeRepository, 
    PositionRepository, AnalysisCacheRepository, EventRepository,
    TriggerRepository
)


class TestBaseRepository:
    """Tests for the BaseRepository class."""
    
    def test_get_by_id(self, db_session):
        """Test getting an entity by ID."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Create a test job
        job = Job(
            job_id=str(uuid4()),
            requester_id="agent123",
            requester_name="Test Agent",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        # Test get_by_id
        result = repo.get_by_id(job.id, db_session)
        assert result is not None
        assert result.id == job.id
        assert result.job_id == job.job_id
        
        # Test with non-existent ID
        result = repo.get_by_id(9999, db_session)
        assert result is None
    
    def test_list_all(self, db_session):
        """Test listing all entities."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Create test jobs
        for i in range(5):
            job = Job(
                job_id=str(uuid4()),
                requester_id=f"agent{i}",
                title=f"Test Job {i}",
                status=JobStatus.PENDING
            )
            db_session.add(job)
        db_session.commit()
        
        # Test list_all
        results = repo.list_all(limit=3, session=db_session)
        assert len(results) == 3
        
        # Test with different limit and offset
        all_results = repo.list_all(limit=10, session=db_session)
        assert len(all_results) >= 5
        
        offset_results = repo.list_all(limit=2, offset=2, session=db_session)
        assert len(offset_results) == 2
        assert offset_results[0].id == all_results[2].id
    
    def test_create(self, db_session):
        """Test creating an entity."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Test data
        job_data = {
            "job_id": str(uuid4()),
            "requester_id": "agent123",
            "title": "New Test Job",
            "status": JobStatus.PENDING
        }
        
        # Test create
        job = repo.create(job_data, db_session)
        assert job is not None
        assert job.job_id == job_data["job_id"]
        assert job.requester_id == "agent123"
        assert job.title == "New Test Job"
        
        # Verify it was saved to the database
        saved_job = db_session.query(Job).filter(Job.job_id == job_data["job_id"]).first()
        assert saved_job is not None
        assert saved_job.id == job.id
    
    def test_update(self, db_session):
        """Test updating an entity."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Create a test job
        job = Job(
            job_id=str(uuid4()),
            requester_id="agent123",
            title="Original Title",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        # Test update
        updated_data = {
            "title": "Updated Title",
            "status": JobStatus.IN_PROGRESS,
            "description": "New description"
        }
        
        updated_job = repo.update(job.id, updated_data, db_session)
        assert updated_job is not None
        assert updated_job.id == job.id
        assert updated_job.title == "Updated Title"
        assert updated_job.status == JobStatus.IN_PROGRESS
        assert updated_job.description == "New description"
        
        # Verify changes were saved
        db_session.expire_all()
        saved_job = db_session.query(Job).get(job.id)
        assert saved_job.title == "Updated Title"
        assert saved_job.status == JobStatus.IN_PROGRESS
        
        # Test updating non-existent entity
        result = repo.update(9999, {"title": "Should not exist"}, db_session)
        assert result is None
    
    def test_delete(self, db_session):
        """Test deleting an entity."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Create a test job
        job = Job(
            job_id=str(uuid4()),
            requester_id="agent123",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        job_id = job.id
        
        # Test delete
        result = repo.delete(job_id, db_session)
        assert result is True
        
        # Verify it was deleted
        deleted_job = db_session.query(Job).get(job_id)
        assert deleted_job is None
        
        # Test deleting non-existent entity
        result = repo.delete(9999, db_session)
        assert result is False
    
    def test_count(self, db_session):
        """Test counting entities."""
        # Create a test repository for Job
        repo = BaseRepository(Job)
        
        # Clear existing jobs
        db_session.query(Job).delete()
        
        # Create test jobs
        for i in range(5):
            job = Job(
                job_id=str(uuid4()),
                requester_id=f"agent{i}",
                title=f"Test Job {i}",
                status=JobStatus.PENDING
            )
            db_session.add(job)
        db_session.commit()
        
        # Test count
        count = repo.count(db_session)
        assert count == 5


class TestJobRepository:
    """Tests for the JobRepository class."""
    
    def test_get_by_job_id(self, db_session):
        """Test getting a job by job ID."""
        repo = JobRepository()
        job_id = str(uuid4())
        
        # Create a test job
        job = Job(
            job_id=job_id,
            requester_id="agent123",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        # Test get_by_job_id
        result = repo.get_by_job_id(job_id, db_session)
        assert result is not None
        assert result.job_id == job_id
        
        # Test with non-existent job ID
        result = repo.get_by_job_id("non-existent", db_session)
        assert result is None
    
    def test_get_by_requester(self, db_session):
        """Test getting jobs by requester ID."""
        repo = JobRepository()
        requester_id = "agent123"
        
        # Clear existing jobs
        db_session.query(Job).delete()
        db_session.commit()
        
        # Create test jobs
        for i in range(3):
            job = Job(
                job_id=str(uuid4()),
                requester_id=requester_id,
                title=f"Test Job {i}",
                status=JobStatus.PENDING
            )
            db_session.add(job)
        
        # Add job for different requester
        other_job = Job(
            job_id=str(uuid4()),
            requester_id="other_agent",
            title="Other Job",
            status=JobStatus.PENDING
        )
        db_session.add(other_job)
        db_session.commit()
        
        # Test get_by_requester
        results = repo.get_by_requester(requester_id, session=db_session)
        assert len(results) == 3
        for job in results:
            assert job.requester_id == requester_id
    
    def test_get_by_status(self, db_session):
        """Test getting jobs by status."""
        repo = JobRepository()
        
        # Clear existing jobs
        db_session.query(Job).delete()
        db_session.commit()
        
        # Create jobs with different statuses
        for status in [JobStatus.PENDING, JobStatus.IN_PROGRESS, JobStatus.COMPLETED]:
            for i in range(2):
                job = Job(
                    job_id=str(uuid4()),
                    requester_id="agent123",
                    title=f"Test Job {status.value} {i}",
                    status=status
                )
                db_session.add(job)
        db_session.commit()
        
        # Test get_by_status
        pending_jobs = repo.get_by_status(JobStatus.PENDING, session=db_session)
        assert len(pending_jobs) == 2
        for job in pending_jobs:
            assert job.status == JobStatus.PENDING
        
        in_progress_jobs = repo.get_by_status(JobStatus.IN_PROGRESS, session=db_session)
        assert len(in_progress_jobs) == 2
        for job in in_progress_jobs:
            assert job.status == JobStatus.IN_PROGRESS
    
    def test_create_job(self, db_session):
        """Test creating a job with UUID generation."""
        repo = JobRepository()
        
        # Test data without job_id
        job_data = {
            "requester_id": "agent123",
            "title": "New Test Job",
            "status": JobStatus.PENDING
        }
        
        # Test create_job
        job = repo.create_job(job_data, db_session)
        assert job is not None
        assert job.requester_id == "agent123"
        assert job.title == "New Test Job"
        assert job.job_id is not None  # Should have generated a UUID
        
        # Test with provided job_id
        job_id = str(uuid4())
        job_data["job_id"] = job_id
        job = repo.create_job(job_data, db_session)
        assert job.job_id == job_id
    
    def test_update_status(self, db_session):
        """Test updating job status."""
        repo = JobRepository()
        job_id = str(uuid4())
        
        # Create a test job
        job = Job(
            job_id=job_id,
            requester_id="agent123",
            title="Test Job",
            status=JobStatus.PENDING
        )
        db_session.add(job)
        db_session.commit()
        
        # Test update_status
        updated_job = repo.update_status(job_id, JobStatus.IN_PROGRESS, db_session)
        assert updated_job is not None
        assert updated_job.status == JobStatus.IN_PROGRESS
        
        # Verify changes were saved
        db_session.expire_all()
        saved_job = db_session.query(Job).filter(Job.job_id == job_id).first()
        assert saved_job.status == JobStatus.IN_PROGRESS
        
        # Test updating non-existent job
        result = repo.update_status("non-existent", JobStatus.COMPLETED, db_session)
        assert result is None


class TestTradeRepository:
    """Tests for the TradeRepository class."""
    
    def test_get_by_trade_id(self, db_session):
        """Test getting a trade by trade ID."""
        repo = TradeRepository()
        trade_id = str(uuid4())
        
        # Create a test trade
        trade = Trade(
            trade_id=trade_id,
            market_id="market123",
            outcome_id="outcome456",
            direction=TradeDirection.BUY,
            size=10.0,
            price=0.65,
            status=TradeStatus.PENDING,
            strategy=StrategyType.MOMENTUM
        )
        db_session.add(trade)
        db_session.commit()
        
        # Test get_by_trade_id
        result = repo.get_by_trade_id(trade_id, db_session)
        assert result is not None
        assert result.trade_id == trade_id
        
        # Test with non-existent trade ID
        result = repo.get_by_trade_id("non-existent", db_session)
        assert result is None
    
    def test_get_by_market(self, db_session):
        """Test getting trades by market ID."""
        repo = TradeRepository()
        market_id = "market123"
        
        # Clear existing trades
        db_session.query(Trade).delete()
        db_session.commit()
        
        # Create test trades for market
        for i in range(3):
            trade = Trade(
                trade_id=str(uuid4()),
                market_id=market_id,
                outcome_id=f"outcome{i}",
                direction=TradeDirection.BUY,
                size=10.0,
                price=0.65,
                status=TradeStatus.PENDING,
                strategy=StrategyType.MOMENTUM
            )
            db_session.add(trade)
        
        # Add trade for different market
        other_trade = Trade(
            trade_id=str(uuid4()),
            market_id="other_market",
            outcome_id="outcome1",
            direction=TradeDirection.SELL,
            size=5.0,
            price=0.75,
            status=TradeStatus.PENDING,
            strategy=StrategyType.MOMENTUM
        )
        db_session.add(other_trade)
        db_session.commit()
        
        # Test get_by_market
        results = repo.get_by_market(market_id, session=db_session)
        assert len(results) == 3
        for trade in results:
            assert trade.market_id == market_id


class TestPositionRepository:
    """Tests for the PositionRepository class."""
    
    def test_get_active_positions(self, db_session):
        """Test getting active positions."""
        repo = PositionRepository()
        
        # Clear existing positions
        db_session.query(Position).delete()
        db_session.commit()
        
        # Create active positions
        for i in range(3):
            position = Position(
                position_id=str(uuid4()),
                market_id=f"market{i}",
                outcome_id=f"outcome{i}",
                direction=TradeDirection.BUY,
                size=10.0,
                entry_price=0.65,
                current_price=0.70,
                strategy=StrategyType.MOMENTUM,
                is_active=True
            )
            db_session.add(position)
        
        # Create inactive position
        inactive = Position(
            position_id=str(uuid4()),
            market_id="inactive_market",
            outcome_id="outcome1",
            direction=TradeDirection.SELL,
            size=5.0,
            entry_price=0.75,
            current_price=0.70,
            strategy=StrategyType.MOMENTUM,
            is_active=False
        )
        db_session.add(inactive)
        db_session.commit()
        
        # Test get_active_positions
        results = repo.get_active_positions(session=db_session)
        assert len(results) == 3
        for position in results:
            assert position.is_active == True


class TestAnalysisCacheRepository:
    """Tests for the AnalysisCacheRepository class."""
    
    def test_get_valid_cache(self, db_session):
        """Test getting valid cache entries."""
        repo = AnalysisCacheRepository()
        market_id = "market123"
        analysis_type = "liquidity_analysis"
        
        # Clear existing cache
        db_session.query(AnalysisCache).delete()
        db_session.commit()
        
        now = datetime.utcnow()
        
        # Create valid cache entry (not expired)
        valid_cache = AnalysisCache(
            market_id=market_id,
            analysis_type=analysis_type,
            timestamp=now,
            expiration=now + timedelta(hours=1),
            data={"score": 0.85}
        )
        db_session.add(valid_cache)
        
        # Create expired cache entry
        expired_cache = AnalysisCache(
            market_id=market_id,
            analysis_type="volatility_analysis",
            timestamp=now - timedelta(hours=2),
            expiration=now - timedelta(hours=1),
            data={"score": 0.75}
        )
        db_session.add(expired_cache)
        db_session.commit()
        
        # Test get_valid_cache
        result = repo.get_valid_cache(market_id, analysis_type, db_session)
        assert result is not None
        assert result.market_id == market_id
        assert result.analysis_type == analysis_type
        
        # Test with expired cache
        result = repo.get_valid_cache(market_id, "volatility_analysis", db_session)
        assert result is None
    
    def test_update_or_create(self, db_session):
        """Test updating or creating cache entries."""
        repo = AnalysisCacheRepository()
        market_id = "market123"
        analysis_type = "liquidity_analysis"
        
        # Clear existing cache
        db_session.query(AnalysisCache).delete()
        db_session.commit()
        
        now = datetime.utcnow()
        expiration = now + timedelta(hours=1)
        
        # Test creating new cache entry
        data = {"score": 0.85, "details": {"depth": "high"}}
        parameters = {"time_window": "1h"}
        
        cache = repo.update_or_create(
            market_id=market_id,
            analysis_type=analysis_type,
            data=data,
            expiration=expiration,
            parameters=parameters,
            session=db_session
        )
        
        assert cache is not None
        assert cache.market_id == market_id
        assert cache.analysis_type == analysis_type
        assert cache.data == data
        assert cache.parameters == parameters
        
        # Test updating existing cache entry
        new_data = {"score": 0.90, "details": {"depth": "very high"}}
        new_expiration = now + timedelta(hours=2)
        
        updated_cache = repo.update_or_create(
            market_id=market_id,
            analysis_type=analysis_type,
            data=new_data,
            expiration=new_expiration,
            session=db_session
        )
        
        assert updated_cache.id == cache.id
        assert updated_cache.data == new_data
        assert updated_cache.expiration == new_expiration
