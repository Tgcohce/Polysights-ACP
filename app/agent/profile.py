"""
ACP Agent profile configuration and registration functionality.
"""
from typing import Dict, Any, List

# ACP Agent profile configuration as specified in the requirements
AGENT_CONFIG: Dict[str, Any] = {
    "name": "PolysightsTrader",
    "role": "hybrid",  # Both provider and requestor
    "description": "Advanced prediction market trading agent powered by Polysights analytics. Provides market analysis, executes trades, and offers portfolio management services.",
    "services": [
        {
            "name": "Market Analysis",
            "price": 0.50,  # USD (converted to $VIRTUAL)
            "sla": 300,  # 5 minutes
            "description": "Comprehensive market analysis using Polysights data"
        },
        {
            "name": "Trade Execution",
            "price": 2.00,
            "sla": 600,  # 10 minutes
            "description": "Execute trades based on analysis and user parameters"
        },
        {
            "name": "Portfolio Management",
            "price": 5.00,
            "sla": 1800,  # 30 minutes
            "description": "Full portfolio optimization and risk management"
        },
        {
            "name": "Arbitrage Detection",
            "price": 1.00,
            "sla": 180,  # 3 minutes
            "description": "Real-time arbitrage opportunity identification"
        }
    ]
}


def get_agent_metadata() -> Dict[str, Any]:
    """
    Get enhanced agent metadata for registration.
    
    Returns:
        Dict[str, Any]: Dictionary containing agent metadata for registration
    """
    return {
        **AGENT_CONFIG,
        "capabilities": [
            "prediction-markets-trading",
            "market-analysis",
            "arbitrage-detection",
            "portfolio-optimization",
            "risk-management"
        ],
        "supported_markets": [
            "polymarket"
        ],
        "api_version": "1.0.0",
        "provider_status": "active",
        "requestor_status": "active",
    }


def get_service_details(service_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific service.
    
    Args:
        service_name: Name of the service to retrieve details for
        
    Returns:
        Dict[str, Any]: Service details or empty dict if not found
    """
    for service in AGENT_CONFIG["services"]:
        if service["name"].lower() == service_name.lower():
            return service
    return {}
