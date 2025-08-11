# ACP Polymarket Trading Agent: User Guide

This guide provides detailed instructions on how to use and configure the ACP Polymarket Trading Agent.

## Table of Contents

- [Introduction](#introduction)
- [Dashboard Overview](#dashboard-overview)
- [Configuration](#configuration)
- [Job Management](#job-management)
- [Trading Strategies](#trading-strategies)
- [Event Monitoring](#event-monitoring)
- [Agent Network](#agent-network)
- [Wallet Management](#wallet-management)
- [Troubleshooting](#troubleshooting)

## Introduction

The ACP Polymarket Trading Agent is designed to automate trading on Polymarket based on various signals and strategies. It can be used as:

1. **A provider of trading services** to other agents in the ACP ecosystem
2. **A requester of analysis or data** from other agents to enhance its trading decisions
3. **A standalone trading agent** for your own trading strategies

The agent integrates with Polymarket's CLOB API for trade execution and Polysights for market analytics, providing a comprehensive solution for automated trading on prediction markets.

## Dashboard Overview

The agent's dashboard is accessible at `http://localhost:8000/dashboard` after deployment. The dashboard provides:

- **Portfolio Overview**: View current positions, PnL, and trading history
- **Job Management**: Track incoming and outgoing job requests
- **Market Analysis**: View market analytics and predictions
- **Event Monitor**: Configure alerts and triggers for market events
- **Agent Network**: Manage connections to other agents
- **Configuration**: Adjust agent settings and parameters

![Dashboard Overview](assets/dashboard_overview.png)

## Configuration

The agent is configured through environment variables, which can be set in the `.env` file. Key configuration parameters include:

### ACP Configuration

- `ACP_AGENT_ID`: Unique identifier for your agent in the ACP ecosystem
- `ACP_AGENT_NAME`: Human-readable name for your agent
- `ACP_SERVICE_REGISTRY`: URL of the ACP service registry

### Polymarket Configuration

- `POLYMARKET_API_URL`: URL of the Polymarket API
- `POLYMARKET_API_KEY`: Your Polymarket API key
- `POLYMARKET_WEBSOCKET_URL`: WebSocket URL for real-time market updates

### Wallet Configuration

- `WALLET_PRIVATE_KEY`: Private key for your ERC-6551 wallet
- `VIRTUAL_TOKEN_ADDRESS`: Address of the $VIRTUAL token contract
- `CHAIN_ID`: Chain ID for the blockchain (1 for Ethereum Mainnet, 137 for Polygon)

### Strategy Configuration

- `DEFAULT_STRATEGY`: Default trading strategy (momentum, arbitrage, event-driven, etc.)
- `MAX_POSITION_SIZE`: Maximum position size as a percentage of available capital
- `RISK_TOLERANCE`: Risk tolerance level (low, medium, high)

## Job Management

The agent can both accept job requests from other agents and create job requests for other agents.

### Accepting Jobs

When the agent receives a job request, it:

1. Validates the request against its capabilities
2. Estimates the cost based on complexity
3. Accepts or rejects the job based on configured criteria
4. Executes the job if accepted
5. Delivers results and requests payment

Job types that can be accepted:
- Market analysis requests
- Trade execution requests
- Signal generation requests
- Custom analysis requests

### Creating Job Requests

The agent can create job requests for:
- Additional market analysis
- On-chain data analysis
- Social sentiment analysis
- News and event analysis

To create a job request through the dashboard:
1. Navigate to the "Job Management" tab
2. Click "Create Job Request"
3. Fill in the job details (type, parameters, budget)
4. Submit the request

## Trading Strategies

The agent supports multiple trading strategies that can be configured through the dashboard:

### Momentum Trading

Follows market trends based on price movements and trading volume.

Configuration parameters:
- Time window (short, medium, long)
- Momentum threshold
- Volume confirmation required (yes/no)

### Arbitrage Trading

Exploits price differences between related markets.

Configuration parameters:
- Related market pairs
- Minimum arbitrage opportunity (%)
- Maximum execution delay (ms)

### Event-Driven Trading

Makes trades based on real-world events that impact market outcomes.

Configuration parameters:
- Event sources (news feeds, social media, on-chain data)
- Event relevance threshold
- Response time window

### Mean Reversion

Assumes prices will revert to historical averages after deviations.

Configuration parameters:
- Reference window length
- Deviation threshold
- Mean calculation method (SMA, EMA, etc.)

### Smart Money Tracking

Follows positions of wallets identified as profitable traders.

Configuration parameters:
- Wallets to track
- Minimum wallet performance
- Follow delay

## Event Monitoring

The Event Monitoring system allows you to set up alerts and automated actions based on market conditions:

### Creating Triggers

1. Navigate to the "Event Monitor" tab in the dashboard
2. Click "Create New Trigger"
3. Select trigger type (price, volume, social, news, on-chain, composite)
4. Configure trigger conditions
5. Set up actions to take when triggered
6. Save and enable the trigger

Example triggers:
- Alert when price moves more than 10% in 1 hour
- Execute a trade when trading volume spikes above threshold
- Adjust strategy parameters when market liquidity changes
- Notify when significant social media mentions occur

### Managing Triggers

From the Event Monitor tab, you can:
- View all active and inactive triggers
- Edit trigger conditions and actions
- Enable/disable triggers
- View trigger history and performance

## Agent Network

The agent can connect to other agents in the ACP ecosystem for collaboration:

### Discovering Agents

1. Navigate to the "Agent Network" tab
2. Click "Discover Agents"
3. Filter agents by capabilities, reputation, or specialization
4. Request connection to selected agents

### Managing Connections

From the Agent Network tab, you can:
- View all connected agents
- Set trust levels and permissions
- Configure automatic job delegation rules
- Review collaboration history

## Wallet Management

The agent uses an ERC-6551 smart wallet for secure handling of $VIRTUAL tokens:

### Monitoring Balance

The wallet balance is displayed on the dashboard home screen, showing:
- Current $VIRTUAL token balance
- Pending payments
- Reserved funds for active jobs

### Managing Funds

From the "Wallet" tab, you can:
- Deposit additional funds
- Withdraw available funds
- Set maximum spending limits
- View transaction history

## Troubleshooting

### Common Issues

**Issue**: Agent fails to connect to Polymarket API
**Solution**: Verify API key and URL in .env file, check network connectivity

**Issue**: Job execution failures
**Solution**: Check job logs in the "Job Management" tab, verify required parameters were provided

**Issue**: Trading strategy not executing trades
**Solution**: Check market liquidity, verify position size limits, ensure wallet has sufficient funds

**Issue**: Database connection errors
**Solution**: Verify database credentials and connectivity, check database logs

### Logs

Logs can be accessed in several ways:
1. Through the dashboard "Logs" tab
2. In the container logs using `docker logs acp-polymarket-agent`
3. In the log files located at `/app/logs` inside the container

### Getting Support

If you encounter issues not covered in this guide:
1. Check the [GitHub repository issues](https://github.com/yourusername/acp-polymarket-agent/issues)
2. Join the ACP Discord community for community support
3. Contact the maintenance team at support@acp-agent.example.com
