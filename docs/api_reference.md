# ACP Polymarket Trading Agent: API Reference

This document provides detailed information about the API endpoints available in the ACP Polymarket Trading Agent.

## Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [API Endpoints](#api-endpoints)
  - [Health and Status](#health-and-status)
  - [Agent Management](#agent-management)
  - [Job Management](#job-management)
  - [Trading](#trading)
  - [Market Analysis](#market-analysis)
  - [Event Monitor](#event-monitor)
  - [Agent Network](#agent-network)
  - [Dashboard](#dashboard)
- [Data Models](#data-models)
- [Error Handling](#error-handling)

## Authentication

All API requests require authentication using an API key. The API key should be provided in the `Authorization` header as follows:

```
Authorization: Bearer YOUR_API_KEY
```

API keys can be generated and managed through the dashboard interface under "Settings" > "API Keys".

## Base URL

By default, the API is available at:

```
http://localhost:8000/api/v1
```

## API Endpoints

### Health and Status

#### GET `/health`

Returns the health status of the agent and its dependencies.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-09-08T12:34:56.789Z",
  "version": "0.1.0",
  "response_time_ms": 25.4,
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "timestamp": "2023-09-08T12:34:56.700Z"
    },
    {
      "name": "acp_registry",
      "status": "healthy",
      "message": "ACP registry service reachable",
      "timestamp": "2023-09-08T12:34:56.750Z"
    }
  ]
}
```

### Agent Management

#### GET `/agent/profile`

Returns information about the current agent's profile.

**Response**:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Polymarket Trading Agent",
  "description": "Advanced trading agent for Polymarket prediction markets",
  "capabilities": ["trading", "market-analysis", "event-monitoring"],
  "reputation_score": 4.8,
  "job_success_rate": 0.95,
  "created_at": "2023-08-01T00:00:00Z",
  "last_active": "2023-09-08T12:00:00Z"
}
```

#### PUT `/agent/profile`

Updates the agent profile information.

**Request Body**:
```json
{
  "name": "Updated Agent Name",
  "description": "New description for the agent",
  "capabilities": ["trading", "market-analysis", "event-monitoring", "new-capability"]
}
```

**Response**:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Agent Name",
  "description": "New description for the agent",
  "capabilities": ["trading", "market-analysis", "event-monitoring", "new-capability"],
  "updated_at": "2023-09-08T13:00:00Z"
}
```

### Job Management

#### GET `/jobs`

Returns a list of jobs with optional filtering.

**Query Parameters**:
- `status` (optional): Filter by job status (pending, accepted, in_progress, completed, rejected)
- `role` (optional): Filter by agent role (provider, requester)
- `limit` (optional): Maximum number of jobs to return (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "total": 45,
  "limit": 20,
  "offset": 0,
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440001",
      "requester_id": "550e8400-e29b-41d4-a716-446655440002",
      "requester_name": "Market Analysis Agent",
      "title": "Trade Execution for Market XYZ",
      "description": "Execute trades based on provided signals",
      "status": "completed",
      "created_at": "2023-09-07T14:30:00Z",
      "updated_at": "2023-09-07T15:45:00Z",
      "deadline": "2023-09-07T16:30:00Z",
      "payment_amount": 50.0,
      "payment_token": "VIRTUAL",
      "payment_status": "paid"
    },
    // More jobs...
  ]
}
```

#### POST `/jobs`

Creates a new job request.

**Request Body**:
```json
{
  "requester_id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Market Analysis for Upcoming Election",
  "description": "Detailed analysis of the prediction market for the upcoming election",
  "parameters": {
    "market_ids": ["market-123", "market-456"],
    "analysis_types": ["liquidity", "momentum", "sentiment"]
  },
  "deadline": "2023-09-10T12:00:00Z",
  "payment_offer": 75.0
}
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "pending",
  "created_at": "2023-09-08T13:15:00Z",
  "estimated_completion": "2023-09-09T13:15:00Z"
}
```

#### GET `/jobs/{job_id}`

Returns details for a specific job.

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "requester_id": "550e8400-e29b-41d4-a716-446655440002",
  "requester_name": "Market Analysis Agent",
  "title": "Market Analysis for Upcoming Election",
  "description": "Detailed analysis of the prediction market for the upcoming election",
  "status": "in_progress",
  "progress": 0.6,
  "created_at": "2023-09-08T13:15:00Z",
  "updated_at": "2023-09-08T14:30:00Z",
  "deadline": "2023-09-10T12:00:00Z",
  "estimated_completion": "2023-09-09T13:15:00Z",
  "parameters": {
    "market_ids": ["market-123", "market-456"],
    "analysis_types": ["liquidity", "momentum", "sentiment"]
  },
  "payment_amount": 75.0,
  "payment_token": "VIRTUAL",
  "payment_status": "pending"
}
```

#### PUT `/jobs/{job_id}/status`

Updates the status of a job.

**Request Body**:
```json
{
  "status": "accepted",
  "message": "Job accepted, starting analysis now",
  "estimated_completion": "2023-09-09T13:15:00Z"
}
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "accepted",
  "updated_at": "2023-09-08T13:20:00Z",
  "estimated_completion": "2023-09-09T13:15:00Z"
}
```

#### POST `/jobs/{job_id}/deliverables`

Submits deliverables for a job.

**Request Body**:
```json
{
  "summary": "Analysis of election markets completed",
  "details": "Detailed analysis report...",
  "data": {
    "market_123": {
      "liquidity_score": 0.85,
      "momentum_direction": "positive",
      "sentiment_score": 0.7
    },
    "market_456": {
      "liquidity_score": 0.65,
      "momentum_direction": "neutral",
      "sentiment_score": 0.5
    }
  },
  "attachments": []
}
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "completed",
  "updated_at": "2023-09-09T10:30:00Z",
  "payment_request_id": "payment-req-123"
}
```

### Trading

#### GET `/trading/positions`

Returns a list of current trading positions.

**Query Parameters**:
- `active_only` (optional): Only return active positions (default: true)
- `market_id` (optional): Filter by market ID
- `strategy` (optional): Filter by strategy type
- `limit` (optional): Maximum number of positions to return (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "total": 12,
  "limit": 20,
  "offset": 0,
  "positions": [
    {
      "position_id": "550e8400-e29b-41d4-a716-446655440010",
      "market_id": "market-123",
      "market_name": "Will candidate X win the election?",
      "outcome_id": "outcome-yes",
      "outcome_name": "Yes",
      "direction": "buy",
      "size": 100.0,
      "entry_price": 0.65,
      "current_price": 0.70,
      "unrealized_pnl": 5.0,
      "unrealized_pnl_percentage": 7.69,
      "strategy": "momentum",
      "opened_at": "2023-09-05T09:30:00Z",
      "is_active": true,
      "stop_loss": 0.55,
      "take_profit": 0.85
    },
    // More positions...
  ]
}
```

#### POST `/trading/orders`

Places a new trade order.

**Request Body**:
```json
{
  "market_id": "market-789",
  "outcome_id": "outcome-yes",
  "direction": "buy",
  "size": 50.0,
  "price": 0.65,
  "strategy": "event_driven",
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "signal_id": "signal-456",
  "execution_priority": "normal",
  "stop_loss": 0.60,
  "take_profit": 0.75
}
```

**Response**:
```json
{
  "trade_id": "550e8400-e29b-41d4-a716-446655440020",
  "status": "pending",
  "created_at": "2023-09-08T15:30:00Z",
  "estimated_execution_time": "2023-09-08T15:30:05Z"
}
```

#### GET `/trading/orders/{trade_id}`

Returns details for a specific trade order.

**Response**:
```json
{
  "trade_id": "550e8400-e29b-41d4-a716-446655440020",
  "market_id": "market-789",
  "market_name": "Will event Z occur before year end?",
  "outcome_id": "outcome-yes",
  "outcome_name": "Yes",
  "direction": "buy",
  "size": 50.0,
  "price": 0.65,
  "executed_price": 0.652,
  "status": "filled",
  "strategy": "event_driven",
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "signal_id": "signal-456",
  "execution_priority": "normal",
  "created_at": "2023-09-08T15:30:00Z",
  "executed_at": "2023-09-08T15:30:07Z",
  "position_id": "550e8400-e29b-41d4-a716-446655440021"
}
```

#### PUT `/trading/positions/{position_id}/close`

Closes a trading position.

**Request Body**:
```json
{
  "reason": "take_profit",
  "price": 0.75
}
```

**Response**:
```json
{
  "position_id": "550e8400-e29b-41d4-a716-446655440021",
  "status": "closing",
  "requested_at": "2023-09-09T10:15:00Z",
  "estimated_execution_time": "2023-09-09T10:15:05Z"
}
```

### Market Analysis

#### GET `/analysis/markets/{market_id}`

Returns analysis data for a specific market.

**Query Parameters**:
- `analysis_types` (optional): Comma-separated list of analysis types (liquidity, volume, momentum, etc.)
- `time_window` (optional): Time window for analysis (1h, 24h, 7d, etc.)

**Response**:
```json
{
  "market_id": "market-123",
  "market_name": "Will candidate X win the election?",
  "timestamp": "2023-09-08T16:00:00Z",
  "analyses": {
    "liquidity": {
      "score": 0.85,
      "depth": "high",
      "bid_ask_spread": 0.02,
      "updated_at": "2023-09-08T15:55:00Z"
    },
    "momentum": {
      "direction": "positive",
      "strength": 0.7,
      "time_window": "24h",
      "updated_at": "2023-09-08T15:55:00Z"
    },
    "volume": {
      "total_24h": 50000.0,
      "change_percentage": 15.4,
      "updated_at": "2023-09-08T15:55:00Z"
    }
  }
}
```

#### POST `/analysis/run`

Triggers a specific analysis for one or more markets.

**Request Body**:
```json
{
  "market_ids": ["market-123", "market-456"],
  "analysis_types": ["liquidity", "sentiment", "momentum"],
  "parameters": {
    "time_window": "12h",
    "depth": "full"
  },
  "force_refresh": true
}
```

**Response**:
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440030",
  "status": "processing",
  "started_at": "2023-09-08T16:15:00Z",
  "estimated_completion": "2023-09-08T16:16:00Z"
}
```

### Event Monitor

#### GET `/events/triggers`

Returns a list of configured event triggers.

**Query Parameters**:
- `active_only` (optional): Only return active triggers (default: true)
- `category` (optional): Filter by category (price, volume, social, news, on-chain)
- `limit` (optional): Maximum number of triggers to return (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "total": 8,
  "limit": 20,
  "offset": 0,
  "triggers": [
    {
      "trigger_id": "550e8400-e29b-41d4-a716-446655440040",
      "name": "Price Movement Alert",
      "description": "Detect significant price movements",
      "enabled": true,
      "categories": ["price"],
      "sources": ["polymarket"],
      "min_severity": "medium",
      "conditions": [
        {"field": "price_change_percentage", "operator": "gt", "value": 5.0}
      ],
      "condition_type": "all",
      "actions": [
        {"action_type": "notify", "params": {"title": "Price Alert", "channel": "dashboard"}}
      ],
      "cooldown_seconds": 300,
      "created_at": "2023-09-01T12:00:00Z",
      "updated_at": "2023-09-01T12:00:00Z",
      "market_ids": ["market-123", "market-456"],
      "tags": ["price", "alert"]
    },
    // More triggers...
  ]
}
```

#### POST `/events/triggers`

Creates a new event trigger.

**Request Body**:
```json
{
  "name": "Volume Spike Detector",
  "description": "Detects unusual volume spikes in markets",
  "enabled": true,
  "categories": ["volume"],
  "sources": ["polymarket"],
  "min_severity": "high",
  "conditions": [
    {"field": "volume_change_percentage", "operator": "gt", "value": 50.0},
    {"field": "time_window", "operator": "eq", "value": "1h"}
  ],
  "condition_type": "all",
  "actions": [
    {"action_type": "notify", "params": {"title": "Volume Spike", "channel": "dashboard"}},
    {"action_type": "trade", "params": {"strategy": "momentum", "direction": "follow", "size": "small"}}
  ],
  "cooldown_seconds": 1800,
  "market_ids": ["market-123", "market-789"],
  "tags": ["volume", "spike", "momentum"]
}
```

**Response**:
```json
{
  "trigger_id": "550e8400-e29b-41d4-a716-446655440050",
  "created_at": "2023-09-08T17:00:00Z",
  "status": "created"
}
```

#### GET `/events/history`

Returns a history of detected events.

**Query Parameters**:
- `start_date` (optional): Filter events starting from this date
- `end_date` (optional): Filter events up to this date
- `category` (optional): Filter by event category
- `severity` (optional): Filter by minimum severity
- `limit` (optional): Maximum number of events to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "total": 120,
  "limit": 50,
  "offset": 0,
  "events": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440060",
      "timestamp": "2023-09-08T14:30:45Z",
      "category": "price",
      "source": "polymarket",
      "severity": "high",
      "title": "Significant Price Movement",
      "description": "Price increased by 15% in the last hour",
      "market_id": "market-123",
      "outcome_id": "outcome-yes",
      "data": {
        "old_price": 0.60,
        "new_price": 0.69,
        "change_percentage": 15.0
      },
      "triggers_activated": [
        "550e8400-e29b-41d4-a716-446655440040"
      ],
      "actions_executed": [
        {
          "action_type": "notify",
          "executed_at": "2023-09-08T14:30:46Z",
          "status": "success"
        }
      ]
    },
    // More events...
  ]
}
```

### Agent Network

#### GET `/network/agents`

Returns a list of discovered or connected agents.

**Query Parameters**:
- `status` (optional): Filter by connection status (discovered, connected, trusted)
- `capability` (optional): Filter by agent capability
- `limit` (optional): Maximum number of agents to return (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "total": 25,
  "limit": 20,
  "offset": 0,
  "agents": [
    {
      "agent_id": "550e8400-e29b-41d4-a716-446655440070",
      "name": "Market Analysis Agent",
      "description": "Specialized in deep market analysis and forecasting",
      "capabilities": ["market-analysis", "forecasting"],
      "reputation_score": 4.9,
      "connection_status": "trusted",
      "last_interaction": "2023-09-07T18:15:00Z"
    },
    // More agents...
  ]
}
```

#### POST `/network/connect`

Requests a connection to another agent.

**Request Body**:
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440080",
  "message": "Requesting collaboration on market analysis",
  "capabilities_required": ["social-sentiment", "news-analysis"]
}
```

**Response**:
```json
{
  "connection_id": "550e8400-e29b-41d4-a716-446655440090",
  "status": "pending",
  "requested_at": "2023-09-08T17:30:00Z"
}
```

### Dashboard

#### GET `/dashboard/summary`

Returns a summary of agent activity for the dashboard.

**Response**:
```json
{
  "timestamp": "2023-09-08T18:00:00Z",
  "active_positions": 12,
  "total_pnl": 240.5,
  "pnl_change_24h": 35.2,
  "wallet_balance": 1500.0,
  "pending_jobs": 3,
  "active_jobs": 2,
  "completed_jobs_24h": 8,
  "events_24h": 15,
  "top_markets": [
    {
      "market_id": "market-123",
      "market_name": "Will candidate X win the election?",
      "position_size": 100.0,
      "current_price": 0.70,
      "pnl": 5.0
    },
    // More markets...
  ],
  "recent_events": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440060",
      "timestamp": "2023-09-08T14:30:45Z",
      "category": "price",
      "severity": "high",
      "title": "Significant Price Movement",
      "market_id": "market-123"
    },
    // More events...
  ]
}
```

## Data Models

### Job

```json
{
  "id": 123,
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "requester_id": "550e8400-e29b-41d4-a716-446655440002",
  "requester_name": "Market Analysis Agent",
  "provider_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Trade Execution for Market XYZ",
  "description": "Execute trades based on provided signals",
  "status": "completed",
  "created_at": "2023-09-07T14:30:00Z",
  "updated_at": "2023-09-07T15:45:00Z",
  "deadline": "2023-09-07T16:30:00Z",
  "payment_amount": 50.0,
  "payment_token": "VIRTUAL",
  "payment_status": "paid",
  "metadata": {},
  "parameters": {},
  "results": {}
}
```

### Trade

```json
{
  "id": 456,
  "trade_id": "550e8400-e29b-41d4-a716-446655440020",
  "market_id": "market-789",
  "market_name": "Will event Z occur before year end?",
  "outcome_id": "outcome-yes",
  "outcome_name": "Yes",
  "direction": "buy",
  "size": 50.0,
  "price": 0.65,
  "executed_price": 0.652,
  "status": "filled",
  "strategy": "event_driven",
  "job_id": "550e8400-e29b-41d4-a716-446655440003",
  "signal_id": "signal-456",
  "execution_priority": "normal",
  "created_at": "2023-09-08T15:30:00Z",
  "executed_at": "2023-09-08T15:30:07Z",
  "position_id": "550e8400-e29b-41d4-a716-446655440021",
  "metadata": {}
}
```

### Position

```json
{
  "id": 789,
  "position_id": "550e8400-e29b-41d4-a716-446655440021",
  "market_id": "market-789",
  "market_name": "Will event Z occur before year end?",
  "outcome_id": "outcome-yes",
  "outcome_name": "Yes",
  "direction": "buy",
  "size": 50.0,
  "entry_price": 0.652,
  "current_price": 0.70,
  "unrealized_pnl": 2.4,
  "unrealized_pnl_percentage": 7.36,
  "realized_pnl": 0.0,
  "strategy": "event_driven",
  "trade_id": "550e8400-e29b-41d4-a716-446655440020",
  "opened_at": "2023-09-08T15:30:07Z",
  "closed_at": null,
  "is_active": true,
  "stop_loss": 0.60,
  "take_profit": 0.75,
  "metadata": {}
}
```

### Event

```json
{
  "id": 101,
  "event_id": "550e8400-e29b-41d4-a716-446655440060",
  "timestamp": "2023-09-08T14:30:45Z",
  "category": "price",
  "source": "polymarket",
  "severity": "high",
  "title": "Significant Price Movement",
  "description": "Price increased by 15% in the last hour",
  "market_id": "market-123",
  "outcome_id": "outcome-yes",
  "data": {
    "old_price": 0.60,
    "new_price": 0.69,
    "change_percentage": 15.0
  },
  "processed": true,
  "metadata": {}
}
```

### EventTrigger

```json
{
  "id": 202,
  "trigger_id": "550e8400-e29b-41d4-a716-446655440040",
  "name": "Price Movement Alert",
  "description": "Detect significant price movements",
  "enabled": true,
  "categories": ["price"],
  "sources": ["polymarket"],
  "min_severity": "medium",
  "conditions": [
    {"field": "price_change_percentage", "operator": "gt", "value": 5.0}
  ],
  "condition_type": "all",
  "actions": [
    {"action_type": "notify", "params": {"title": "Price Alert", "channel": "dashboard"}}
  ],
  "cooldown_seconds": 300,
  "created_at": "2023-09-01T12:00:00Z",
  "updated_at": "2023-09-01T12:00:00Z",
  "market_ids": ["market-123", "market-456"],
  "tags": ["price", "alert"]
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK`: Request was successful
- `201 Created`: Resource was successfully created
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Authenticated but unauthorized for the requested resource
- `404 Not Found`: Resource not found
- `409 Conflict`: Request conflicts with current state
- `500 Internal Server Error`: Server error

Error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "The request contains invalid parameters",
    "details": [
      {
        "field": "price",
        "message": "Price must be between 0 and 1"
      }
    ]
  }
}
```
