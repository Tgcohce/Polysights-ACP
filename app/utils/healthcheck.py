"""
Health check utility for ACP Polymarket Trading Agent.

This module provides health check endpoints and functions to verify
the application's dependencies and services are operational.
"""
from datetime import datetime
import logging
from typing import Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session, close_db_session
from app.utils.config import config


logger = logging.getLogger(__name__)


async def check_database_connection() -> Dict[str, Any]:
    """Check if the database connection is working."""
    result = {
        "name": "database",
        "status": "healthy",
        "message": "Database connection successful",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    session = None
    try:
        session = get_db_session()
        # Execute a simple query to verify connection
        session.execute("SELECT 1")
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        result.update({
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        })
    finally:
        if session:
            close_db_session(session)
            
    return result


async def check_acp_service_registry() -> Dict[str, Any]:
    """Check if the ACP service registry is accessible."""
    # This is a placeholder. In a real implementation, you would
    # make an actual API call to the ACP service registry.
    
    result = {
        "name": "acp_registry",
        "status": "healthy",
        "message": "ACP registry service reachable",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Mock implementation - would need actual API call logic
    registry_url = config.get("ACP_SERVICE_REGISTRY")
    if not registry_url:
        result.update({
            "status": "unhealthy",
            "message": "ACP_SERVICE_REGISTRY environment variable not configured"
        })
    
    return result


async def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health by checking all critical dependencies.
    
    Returns:
        Dict containing health check results for each component
        and overall system status.
    """
    start_time = datetime.utcnow()
    
    # Check all dependencies
    db_health = await check_database_connection()
    registry_health = await check_acp_service_registry()
    
    # Collect all checks
    checks = [db_health, registry_health]
    
    # Determine overall status - unhealthy if any component is unhealthy
    overall_status = "healthy"
    for check in checks:
        if check["status"] == "unhealthy":
            overall_status = "unhealthy"
            break
    
    # Calculate response time
    response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Construct the full health response
    health_response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": config.get("APP_VERSION", "0.1.0"),
        "response_time_ms": round(response_time_ms, 2),
        "checks": checks
    }
    
    return health_response
