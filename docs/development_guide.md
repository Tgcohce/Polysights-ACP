# ACP Polymarket Trading Agent: Development Guide

This guide provides detailed information for developers who want to contribute to or extend the ACP Polymarket Trading Agent.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Environment Setup](#development-environment-setup)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
  - [Adding a New Trading Strategy](#adding-a-new-trading-strategy)
  - [Adding a New Event Monitor](#adding-a-new-event-monitor)
  - [Adding a New API Endpoint](#adding-a-new-api-endpoint)
- [Testing](#testing)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Architecture Overview

The ACP Polymarket Trading Agent follows a modular architecture with several key components:

![Architecture Diagram](assets/architecture_diagram.png)

### Core Components

1. **ACP Agent Core**: Handles agent registration, profile, and job lifecycle
2. **PolymarketClient**: Interfaces with Polymarket CLOB API
3. **PolysightsClient**: Interfaces with Polysights analytics API
4. **TradingStrategyEngine**: Implements various trading strategies
5. **EventMonitor**: Detects and responds to market events
6. **AgentNetworkManager**: Facilitates agent discovery and collaboration
7. **Dashboard**: Provides a UI for monitoring and configuration

### Data Flow

1. Event sources (Polymarket WebSocket, Polysights, on-chain events) generate events
2. EventMonitor processes events and evaluates triggers
3. Triggered actions may generate trading signals
4. TradingStrategyEngine evaluates signals and generates trade orders
5. PolymarketClient executes orders on Polymarket
6. Database stores all relevant data for persistence and analysis

## Development Environment Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js 16+ (for dashboard frontend)
- Git

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/acp-polymarket-agent.git
   cd acp-polymarket-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Copy and configure the environment variables:
   ```bash
   cp .env.example .env.dev
   # Edit .env.dev with your development configuration
   ```

6. Create a development database:
   ```bash
   # In PostgreSQL:
   CREATE DATABASE acp_agent_dev;
   ```

7. Initialize the database:
   ```bash
   python -m app.db.create_tables
   ```

8. Run tests to verify your setup:
   ```bash
   pytest
   ```

9. Run the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Code Structure

The codebase is organized as follows:

```
acp_polymarket_agent/
├── app/                        # Application code
│   ├── agent/                  # ACP agent implementation
│   │   ├── registration.py     # Agent registration
│   │   ├── profile.py          # Agent profile
│   │   └── job_lifecycle.py    # Job management
│   ├── api/                    # API endpoints
│   │   ├── routes/             # API route definitions
│   │   └── models.py           # API request/response models
│   ├── dashboard/              # Dashboard UI
│   ├── db/                     # Database models and repositories
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── repository.py       # Repository layer
│   │   └── session.py          # Database session management
│   ├── polymarket/             # Polymarket API integration
│   │   └── client.py           # Polymarket client
│   ├── polysights/             # Polysights API integration
│   │   └── client.py           # Polysights client
│   ├── trading/                # Trading logic
│   │   ├── strategy_engine.py  # Trading strategy engine
│   │   ├── event_models.py     # Event models
│   │   └── event_monitor.py    # Event monitoring
│   ├── utils/                  # Utilities
│   │   ├── config.py           # Configuration management
│   │   └── logging.py          # Logging setup
│   ├── wallet/                 # Wallet management
│   │   └── erc6551.py          # ERC-6551 wallet implementation
│   └── main.py                 # Application entry point
├── config/                     # Configuration files
├── tests/                      # Test suite
├── docs/                       # Documentation
├── requirements.txt            # Production dependencies
└── requirements.dev.txt        # Development dependencies
```

## Adding New Features

### Adding a New Trading Strategy

1. Create a new strategy class in `app/trading/strategies/`:

```python
from app.trading.strategies.base import BaseStrategy

class MyNewStrategy(BaseStrategy):
    """My new trading strategy implementation."""
    
    def __init__(self, params=None):
        """Initialize the strategy with parameters."""
        super().__init__(name="my_new_strategy", params=params)
    
    async def generate_signals(self, market_data):
        """Generate trading signals based on market data.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        # Implementation logic here
        return signals
    
    async def evaluate_position(self, position):
        """Evaluate an existing position and recommend actions.
        
        Args:
            position: Position object to evaluate
            
        Returns:
            PositionAction enum indicating what to do with the position
        """
        # Evaluation logic here
        return self.PositionAction.HOLD
```

2. Register the strategy in `app/trading/strategy_engine.py`:

```python
from app.trading.strategies.my_new_strategy import MyNewStrategy

# In the TradingStrategyEngine class:
def _initialize_strategies(self):
    self.strategies = {
        # Existing strategies
        "my_new_strategy": MyNewStrategy(self.strategy_params.get("my_new_strategy", {}))
    }
```

3. Add appropriate unit tests in `tests/trading/strategies/test_my_new_strategy.py`

4. Update documentation in `docs/trading_strategies.md`

### Adding a New Event Monitor

1. Create a new monitor class in `app/trading/monitors/`:

```python
from app.trading.monitors.base import BaseMonitor
from app.trading.event_models import Event, EventCategory, EventSource, EventSeverity

class MyNewMonitor(BaseMonitor):
    """Monitor for my new data source."""
    
    def __init__(self, event_monitor):
        """Initialize the monitor.
        
        Args:
            event_monitor: Parent EventMonitor instance
        """
        super().__init__(name="my_new_monitor", event_monitor=event_monitor)
    
    async def start(self):
        """Start monitoring."""
        await super().start()
        # Implementation: connect to data source, subscribe to events, etc.
    
    async def stop(self):
        """Stop monitoring."""
        # Implementation: disconnect from data source, etc.
        await super().stop()
    
    async def _generate_event(self, data):
        """Generate an event from received data.
        
        Args:
            data: Raw data from the source
            
        Returns:
            Event object or None if no event should be generated
        """
        # Process data and create an event
        event = Event(
            category=EventCategory.CUSTOM,
            source=EventSource.CUSTOM,
            severity=EventSeverity.MEDIUM,
            title="My New Event",
            description="Something interesting happened",
            data=data
        )
        return event
```

2. Register the monitor in `app/trading/event_monitor.py`:

```python
from app.trading.monitors.my_new_monitor import MyNewMonitor

# In the EventMonitor._initialize_monitors method:
def _initialize_monitors(self):
    self.monitors = {
        # Existing monitors
        "my_new_monitor": MyNewMonitor(self)
    }
```

3. Add appropriate unit tests in `tests/trading/monitors/test_my_new_monitor.py`

### Adding a New API Endpoint

1. Create a new route file in `app/api/routes/` or add to an existing one:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.models import MyNewRequestModel, MyNewResponseModel
from app.utils.deps import get_db_session, get_my_service

router = APIRouter()

@router.post("/my-new-endpoint", response_model=MyNewResponseModel)
async def my_new_endpoint(
    request: MyNewRequestModel,
    db_session: Session = Depends(get_db_session),
    my_service = Depends(get_my_service)
):
    """Handle my new endpoint."""
    try:
        # Implementation logic here
        result = await my_service.do_something(request.param)
        return MyNewResponseModel(
            success=True,
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. Register the router in `app/api/__init__.py`:

```python
from app.api.routes import my_new_router

# In the init_routers function:
def init_routers(app):
    # Existing routers
    app.include_router(my_new_router.router, prefix="/api/v1/my-new-feature", tags=["My New Feature"])
```

3. Add API models in `app/api/models.py`:

```python
from pydantic import BaseModel, Field

class MyNewRequestModel(BaseModel):
    """Request model for my new endpoint."""
    param: str = Field(..., description="Parameter description")
    optional_param: int = Field(None, description="Optional parameter")

class MyNewResponseModel(BaseModel):
    """Response model for my new endpoint."""
    success: bool
    result: dict
    message: str = None
```

4. Add appropriate unit tests in `tests/api/test_my_new_endpoint.py`

5. Update the API reference documentation

## Testing

### Running Tests

Run the entire test suite:

```bash
pytest
```

Run specific test files:

```bash
pytest tests/trading/test_strategy_engine.py
```

Run with coverage:

```bash
pytest --cov=app tests/
```

### Writing Tests

Tests are organized to mirror the application structure:

```
tests/
├── agent/                  # Tests for ACP agent components
├── api/                    # Tests for API endpoints
├── db/                     # Tests for database components
├── polymarket/             # Tests for Polymarket client
├── polysights/             # Tests for Polysights client
├── trading/                # Tests for trading components
│   ├── strategies/         # Tests for trading strategies
│   └── monitors/           # Tests for event monitors
└── conftest.py             # Test fixtures and configuration
```

Example test:

```python
import pytest
from app.trading.strategies.my_strategy import MyStrategy
from app.trading.models import TradingSignal

@pytest.fixture
def strategy():
    """Create a strategy instance for testing."""
    params = {"param1": "value1"}
    return MyStrategy(params)

def test_generate_signals(strategy):
    """Test signal generation."""
    # Setup test data
    market_data = {"price": 0.65, "volume": 1000}
    
    # Run the function being tested
    signals = strategy.generate_signals(market_data)
    
    # Assertions
    assert len(signals) > 0
    assert isinstance(signals[0], TradingSignal)
    assert signals[0].direction == "buy"
```

## Coding Standards

The project follows these coding standards:

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints
- Write docstrings in Google style
- Line length: 100 characters
- Use f-strings for string formatting
- Use named tuples or data classes for data structures

### API Design

- Follow RESTful principles
- Use consistent naming conventions
- Provide meaningful error responses
- Document all endpoints with OpenAPI annotations

### Git

- Use descriptive commit messages
- Follow conventional commits format: `type(scope): message`
  - Example: `feat(trading): add momentum strategy`
  - Types: feat, fix, docs, style, refactor, test, chore

## Pull Request Process

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Implement your changes with appropriate tests and documentation

3. Ensure all tests pass:
   ```bash
   pytest
   ```

4. Ensure code quality:
   ```bash
   flake8 app tests
   mypy app
   ```

5. Submit a pull request with:
   - Clear description of the changes
   - Link to any related issues
   - Screenshots or examples if applicable
   - List of breaking changes if any

## Documentation

### Code Documentation

- All modules, classes, and functions should have docstrings
- Use Google style docstrings:

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with docstring.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    Raises:
        ValueError: If param1 is negative.
    """
```

### Project Documentation

- Update README.md with new features
- Update API documentation for new endpoints
- Create or update architecture diagrams when appropriate
- Add usage examples for new features
