"""
Database repository for ACP Polymarket Trading Agent.

This module provides repository classes for database access.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type, Union
import uuid

from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session

from app.db.models import (
    Job, Trade, Position, AnalysisCache, MarketData,
    Event, EventTrigger, TriggerResult, AgentProfile, 
    Collaboration, Message, SystemMetrics
)
from app.db.session import get_db_session

# Type variable for generic repository
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository for common database operations.
    
    Provides common CRUD operations for database models.
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get_by_id(self, entity_id: int, session: Optional[Session] = None) -> Optional[T]:
        """
        Get entity by primary ID.
        
        Args:
            entity_id: Entity ID
            session: Database session (optional)
            
        Returns:
            Entity if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(self.model).filter(self.model.id == entity_id).first()
    
    def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[T]:
        """
        List all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of entities
        """
        session = session or get_db_session()
        return session.query(self.model).limit(limit).offset(offset).all()
    
    def create(self, data: Dict[str, Any], session: Optional[Session] = None) -> T:
        """
        Create new entity.
        
        Args:
            data: Entity data
            session: Database session (optional)
            
        Returns:
            Created entity
        """
        session = session or get_db_session()
        entity = self.model(**data)
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity
    
    def update(
        self, 
        entity_id: int, 
        data: Dict[str, Any], 
        session: Optional[Session] = None
    ) -> Optional[T]:
        """
        Update entity by ID.
        
        Args:
            entity_id: Entity ID
            data: Updated data
            session: Database session (optional)
            
        Returns:
            Updated entity if found, None otherwise
        """
        session = session or get_db_session()
        entity = self.get_by_id(entity_id, session)
        if not entity:
            return None
        
        for key, value in data.items():
            setattr(entity, key, value)
        
        session.commit()
        session.refresh(entity)
        return entity
    
    def delete(self, entity_id: int, session: Optional[Session] = None) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity ID
            session: Database session (optional)
            
        Returns:
            True if entity was deleted, False otherwise
        """
        session = session or get_db_session()
        entity = self.get_by_id(entity_id, session)
        if not entity:
            return False
        
        session.delete(entity)
        session.commit()
        return True
    
    def count(self, session: Optional[Session] = None) -> int:
        """
        Count total entities.
        
        Args:
            session: Database session (optional)
            
        Returns:
            Total entity count
        """
        session = session or get_db_session()
        return session.query(func.count(self.model.id)).scalar()


class JobRepository(BaseRepository[Job]):
    """
    Repository for Job operations.
    
    Provides job-specific database operations.
    """
    
    def __init__(self):
        super().__init__(Job)
    
    def get_by_job_id(self, job_id: str, session: Optional[Session] = None) -> Optional[Job]:
        """
        Get job by job ID.
        
        Args:
            job_id: Job ID
            session: Database session (optional)
            
        Returns:
            Job if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(Job).filter(Job.job_id == job_id).first()
    
    def get_by_requester(
        self, 
        requester_id: str, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Job]:
        """
        Get jobs by requester ID.
        
        Args:
            requester_id: Requester ID
            limit: Maximum number of jobs to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of jobs
        """
        session = session or get_db_session()
        return (
            session.query(Job)
            .filter(Job.requester_id == requester_id)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_by_status(
        self, 
        status: str, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Job]:
        """
        Get jobs by status.
        
        Args:
            status: Job status
            limit: Maximum number of jobs to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of jobs
        """
        session = session or get_db_session()
        return (
            session.query(Job)
            .filter(Job.status == status)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_recent(
        self, 
        limit: int = 10,
        session: Optional[Session] = None
    ) -> List[Job]:
        """
        Get recent jobs.
        
        Args:
            limit: Maximum number of jobs to return
            session: Database session (optional)
            
        Returns:
            List of recent jobs
        """
        session = session or get_db_session()
        return (
            session.query(Job)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .all()
        )
    
    def create_job(self, job_data: Dict[str, Any], session: Optional[Session] = None) -> Job:
        """
        Create a new job with UUID generation.
        
        Args:
            job_data: Job data
            session: Database session (optional)
            
        Returns:
            Created job
        """
        session = session or get_db_session()
        
        # Generate job_id if not provided
        if "job_id" not in job_data:
            job_data["job_id"] = str(uuid.uuid4())
        
        return self.create(job_data, session)
    
    def update_status(
        self, 
        job_id: str, 
        status: str, 
        session: Optional[Session] = None
    ) -> Optional[Job]:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            session: Database session (optional)
            
        Returns:
            Updated job if found, None otherwise
        """
        session = session or get_db_session()
        job = self.get_by_job_id(job_id, session)
        if not job:
            return None
        
        job.status = status
        job.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(job)
        return job


class TradeRepository(BaseRepository[Trade]):
    """
    Repository for Trade operations.
    
    Provides trade-specific database operations.
    """
    
    def __init__(self):
        super().__init__(Trade)
    
    def get_by_trade_id(self, trade_id: str, session: Optional[Session] = None) -> Optional[Trade]:
        """
        Get trade by trade ID.
        
        Args:
            trade_id: Trade ID
            session: Database session (optional)
            
        Returns:
            Trade if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(Trade).filter(Trade.trade_id == trade_id).first()
    
    def get_by_market(
        self, 
        market_id: str, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Trade]:
        """
        Get trades by market ID.
        
        Args:
            market_id: Market ID
            limit: Maximum number of trades to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of trades
        """
        session = session or get_db_session()
        return (
            session.query(Trade)
            .filter(Trade.market_id == market_id)
            .order_by(desc(Trade.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_by_strategy(
        self, 
        strategy: str, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Trade]:
        """
        Get trades by strategy.
        
        Args:
            strategy: Strategy type
            limit: Maximum number of trades to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of trades
        """
        session = session or get_db_session()
        return (
            session.query(Trade)
            .filter(Trade.strategy == strategy)
            .order_by(desc(Trade.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_by_job(
        self, 
        job_id: str, 
        session: Optional[Session] = None
    ) -> List[Trade]:
        """
        Get trades by job ID.
        
        Args:
            job_id: Job ID
            session: Database session (optional)
            
        Returns:
            List of trades
        """
        session = session or get_db_session()
        return (
            session.query(Trade)
            .filter(Trade.job_id == job_id)
            .order_by(desc(Trade.created_at))
            .all()
        )
    
    def get_recent(
        self, 
        limit: int = 10,
        session: Optional[Session] = None
    ) -> List[Trade]:
        """
        Get recent trades.
        
        Args:
            limit: Maximum number of trades to return
            session: Database session (optional)
            
        Returns:
            List of recent trades
        """
        session = session or get_db_session()
        return (
            session.query(Trade)
            .order_by(desc(Trade.created_at))
            .limit(limit)
            .all()
        )
    
    def create_trade(self, trade_data: Dict[str, Any], session: Optional[Session] = None) -> Trade:
        """
        Create a new trade with UUID generation.
        
        Args:
            trade_data: Trade data
            session: Database session (optional)
            
        Returns:
            Created trade
        """
        session = session or get_db_session()
        
        # Generate trade_id if not provided
        if "trade_id" not in trade_data:
            trade_data["trade_id"] = str(uuid.uuid4())
        
        return self.create(trade_data, session)
    
    def update_status(
        self, 
        trade_id: str, 
        status: str, 
        session: Optional[Session] = None
    ) -> Optional[Trade]:
        """
        Update trade status.
        
        Args:
            trade_id: Trade ID
            status: New status
            session: Database session (optional)
            
        Returns:
            Updated trade if found, None otherwise
        """
        session = session or get_db_session()
        trade = self.get_by_trade_id(trade_id, session)
        if not trade:
            return None
        
        trade.status = status
        trade.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(trade)
        return trade


class PositionRepository(BaseRepository[Position]):
    """
    Repository for Position operations.
    
    Provides position-specific database operations.
    """
    
    def __init__(self):
        super().__init__(Position)
    
    def get_by_position_id(self, position_id: str, session: Optional[Session] = None) -> Optional[Position]:
        """
        Get position by position ID.
        
        Args:
            position_id: Position ID
            session: Database session (optional)
            
        Returns:
            Position if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(Position).filter(Position.position_id == position_id).first()
    
    def get_active_positions(
        self, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Position]:
        """
        Get active positions.
        
        Args:
            limit: Maximum number of positions to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of active positions
        """
        session = session or get_db_session()
        return (
            session.query(Position)
            .filter(Position.is_active == True)  # noqa: E712
            .order_by(desc(Position.opened_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_by_market(
        self, 
        market_id: str, 
        active_only: bool = False,
        session: Optional[Session] = None
    ) -> List[Position]:
        """
        Get positions by market ID.
        
        Args:
            market_id: Market ID
            active_only: Only return active positions
            session: Database session (optional)
            
        Returns:
            List of positions
        """
        session = session or get_db_session()
        query = session.query(Position).filter(Position.market_id == market_id)
        
        if active_only:
            query = query.filter(Position.is_active == True)  # noqa: E712
        
        return query.order_by(desc(Position.opened_at)).all()
    
    def get_by_strategy(
        self, 
        strategy: str, 
        active_only: bool = False,
        session: Optional[Session] = None
    ) -> List[Position]:
        """
        Get positions by strategy.
        
        Args:
            strategy: Strategy type
            active_only: Only return active positions
            session: Database session (optional)
            
        Returns:
            List of positions
        """
        session = session or get_db_session()
        query = session.query(Position).filter(Position.strategy == strategy)
        
        if active_only:
            query = query.filter(Position.is_active == True)  # noqa: E712
        
        return query.order_by(desc(Position.opened_at)).all()
    
    def close_position(
        self, 
        position_id: str, 
        realized_pnl: float, 
        realized_pnl_percentage: float,
        session: Optional[Session] = None
    ) -> Optional[Position]:
        """
        Close a position.
        
        Args:
            position_id: Position ID
            realized_pnl: Realized profit/loss
            realized_pnl_percentage: Realized profit/loss percentage
            session: Database session (optional)
            
        Returns:
            Updated position if found, None otherwise
        """
        session = session or get_db_session()
        position = self.get_by_position_id(position_id, session)
        if not position:
            return None
        
        position.is_active = False
        position.closed_at = datetime.utcnow()
        position.realized_pnl = realized_pnl
        position.realized_pnl_percentage = realized_pnl_percentage
        session.commit()
        session.refresh(position)
        return position


class AnalysisCacheRepository(BaseRepository[AnalysisCache]):
    """
    Repository for AnalysisCache operations.
    
    Provides analysis cache-specific database operations.
    """
    
    def __init__(self):
        super().__init__(AnalysisCache)
    
    def get_by_market_and_type(
        self, 
        market_id: str, 
        analysis_type: str,
        session: Optional[Session] = None
    ) -> Optional[AnalysisCache]:
        """
        Get analysis cache by market ID and type.
        
        Args:
            market_id: Market ID
            analysis_type: Analysis type
            session: Database session (optional)
            
        Returns:
            Analysis cache if found, None otherwise
        """
        session = session or get_db_session()
        return (
            session.query(AnalysisCache)
            .filter(
                AnalysisCache.market_id == market_id,
                AnalysisCache.analysis_type == analysis_type
            )
            .first()
        )
    
    def get_valid_cache(
        self, 
        market_id: str, 
        analysis_type: str,
        session: Optional[Session] = None
    ) -> Optional[AnalysisCache]:
        """
        Get valid (non-expired) analysis cache.
        
        Args:
            market_id: Market ID
            analysis_type: Analysis type
            session: Database session (optional)
            
        Returns:
            Valid analysis cache if found, None otherwise
        """
        session = session or get_db_session()
        now = datetime.utcnow()
        
        return (
            session.query(AnalysisCache)
            .filter(
                AnalysisCache.market_id == market_id,
                AnalysisCache.analysis_type == analysis_type,
                AnalysisCache.expiration > now
            )
            .first()
        )
    
    def update_or_create(
        self, 
        market_id: str, 
        analysis_type: str, 
        data: Dict[str, Any],
        expiration: datetime,
        parameters: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> AnalysisCache:
        """
        Update or create analysis cache.
        
        Args:
            market_id: Market ID
            analysis_type: Analysis type
            data: Analysis data
            expiration: Expiration timestamp
            parameters: Analysis parameters (optional)
            session: Database session (optional)
            
        Returns:
            Updated or created analysis cache
        """
        session = session or get_db_session()
        cache = self.get_by_market_and_type(market_id, analysis_type, session)
        
        if cache:
            cache.data = data
            cache.expiration = expiration
            cache.timestamp = datetime.utcnow()
            if parameters is not None:
                cache.parameters = parameters
            session.commit()
            session.refresh(cache)
            return cache
        else:
            return self.create({
                "market_id": market_id,
                "analysis_type": analysis_type,
                "data": data,
                "expiration": expiration,
                "parameters": parameters or {}
            }, session)
    
    def purge_expired(self, session: Optional[Session] = None) -> int:
        """
        Purge expired cache entries.
        
        Args:
            session: Database session (optional)
            
        Returns:
            Number of entries purged
        """
        session = session or get_db_session()
        now = datetime.utcnow()
        
        expired = (
            session.query(AnalysisCache)
            .filter(AnalysisCache.expiration <= now)
            .all()
        )
        
        for entry in expired:
            session.delete(entry)
        
        session.commit()
        return len(expired)


class EventRepository(BaseRepository[Event]):
    """
    Repository for Event operations.
    
    Provides event-specific database operations.
    """
    
    def __init__(self):
        super().__init__(Event)
    
    def get_by_event_id(self, event_id: str, session: Optional[Session] = None) -> Optional[Event]:
        """
        Get event by event ID.
        
        Args:
            event_id: Event ID
            session: Database session (optional)
            
        Returns:
            Event if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(Event).filter(Event.event_id == event_id).first()
    
    def get_by_category(
        self, 
        category: str, 
        limit: int = 100, 
        offset: int = 0,
        session: Optional[Session] = None
    ) -> List[Event]:
        """
        Get events by category.
        
        Args:
            category: Event category
            limit: Maximum number of events to return
            offset: Pagination offset
            session: Database session (optional)
            
        Returns:
            List of events
        """
        session = session or get_db_session()
        return (
            session.query(Event)
            .filter(Event.category == category)
            .order_by(desc(Event.timestamp))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_recent(
        self, 
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[Event]:
        """
        Get recent events.
        
        Args:
            limit: Maximum number of events to return
            session: Database session (optional)
            
        Returns:
            List of recent events
        """
        session = session or get_db_session()
        return (
            session.query(Event)
            .order_by(desc(Event.timestamp))
            .limit(limit)
            .all()
        )
    
    def get_unprocessed(
        self, 
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[Event]:
        """
        Get unprocessed events.
        
        Args:
            limit: Maximum number of events to return
            session: Database session (optional)
            
        Returns:
            List of unprocessed events
        """
        session = session or get_db_session()
        return (
            session.query(Event)
            .filter(Event.processed == False)  # noqa: E712
            .order_by(desc(Event.timestamp))
            .limit(limit)
            .all()
        )
    
    def mark_processed(
        self, 
        event_id: str,
        session: Optional[Session] = None
    ) -> Optional[Event]:
        """
        Mark event as processed.
        
        Args:
            event_id: Event ID
            session: Database session (optional)
            
        Returns:
            Updated event if found, None otherwise
        """
        session = session or get_db_session()
        event = self.get_by_event_id(event_id, session)
        if not event:
            return None
        
        event.processed = True
        event.processed_timestamp = datetime.utcnow()
        session.commit()
        session.refresh(event)
        return event


class TriggerRepository(BaseRepository[EventTrigger]):
    """
    Repository for EventTrigger operations.
    
    Provides trigger-specific database operations.
    """
    
    def __init__(self):
        super().__init__(EventTrigger)
    
    def get_by_trigger_id(self, trigger_id: str, session: Optional[Session] = None) -> Optional[EventTrigger]:
        """
        Get trigger by trigger ID.
        
        Args:
            trigger_id: Trigger ID
            session: Database session (optional)
            
        Returns:
            Trigger if found, None otherwise
        """
        session = session or get_db_session()
        return session.query(EventTrigger).filter(EventTrigger.trigger_id == trigger_id).first()
    
    def get_enabled(
        self, 
        session: Optional[Session] = None
    ) -> List[EventTrigger]:
        """
        Get all enabled triggers.
        
        Args:
            session: Database session (optional)
            
        Returns:
            List of enabled triggers
        """
        session = session or get_db_session()
        return (
            session.query(EventTrigger)
            .filter(EventTrigger.enabled == True)  # noqa: E712
            .all()
        )
    
    def get_by_categories(
        self, 
        categories: List[str],
        session: Optional[Session] = None
    ) -> List[EventTrigger]:
        """
        Get triggers by categories.
        
        This is a simplified implementation that checks if any of the
        provided categories match any of the categories in the trigger.
        
        Args:
            categories: List of categories
            session: Database session (optional)
            
        Returns:
            List of matching triggers
        """
        session = session or get_db_session()
        
        # Since categories are stored as JSON, we need to check each trigger
        all_triggers = session.query(EventTrigger).filter(
            EventTrigger.enabled == True  # noqa: E712
        ).all()
        
        matching_triggers = []
        for trigger in all_triggers:
            trigger_categories = trigger.categories
            for category in categories:
                if category in trigger_categories:
                    matching_triggers.append(trigger)
                    break
        
        return matching_triggers
    
    def update_last_triggered(
        self, 
        trigger_id: str,
        session: Optional[Session] = None
    ) -> Optional[EventTrigger]:
        """
        Update last triggered timestamp.
        
        Args:
            trigger_id: Trigger ID
            session: Database session (optional)
            
        Returns:
            Updated trigger if found, None otherwise
        """
        session = session or get_db_session()
        trigger = self.get_by_trigger_id(trigger_id, session)
        if not trigger:
            return None
        
        trigger.last_triggered = datetime.utcnow()
        session.commit()
        session.refresh(trigger)
        return trigger


# Create repository instances
job_repository = JobRepository()
trade_repository = TradeRepository()
position_repository = PositionRepository()
analysis_cache_repository = AnalysisCacheRepository()
event_repository = EventRepository()
trigger_repository = TriggerRepository()


# Helper function to get all repositories
def get_repositories():
    """
    Get all repository instances.
    
    Returns:
        Dict of repository instances
    """
    return {
        "job_repository": job_repository,
        "trade_repository": trade_repository,
        "position_repository": position_repository,
        "analysis_cache_repository": analysis_cache_repository,
        "event_repository": event_repository,
        "trigger_repository": trigger_repository
    }
