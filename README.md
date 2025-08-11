# ACP Polymarket Trading Agent

A hybrid/graduated agent for the ACP ecosystem that provides algorithmic trading services on Polymarket prediction markets using $VIRTUAL tokens, advanced market analysis, and the Polysights analytics pipeline.

## Overview

The ACP Polymarket Trading Agent is a sophisticated trading system that acts as both a provider and requester in the ACP ecosystem. It leverages multiple data sources including the Polymarket CLOB API, Polysights analytics, and on-chain signals to execute trades with various strategies.

### Key Features

- **Full ACP Integration**: Acts as a hybrid/graduated agent in the ACP ecosystem with agent-to-agent messaging
- **Advanced Trading Strategies**: Implements arbitrage, momentum, mean reversion, event-driven, and smart money tracking
- **Real-time Event Monitoring**: Detects and responds to market events, price movements, and trading signals
- **ERC-6551 Smart Wallet**: Secure management of $VIRTUAL tokens for ACP job payments
- **Dashboard UI**: FastAPI-based monitoring and control interface
- **Agent Network**: Collaborative trading and signal sharing with other agents
- **Database Persistence**: Complete storage of trades, jobs, analysis cache, and event history
- **Production-Ready**: Dockerized deployment with monitoring, alerting, and comprehensive documentation

## System Architecture

![System Architecture](docs/assets/system_architecture.png)

The system consists of the following core components:

1. **ACP Agent Core**: Handles agent registration, profile management, and job lifecycle
2. **Trading Engine**: Executes trading strategies and manages positions
3. **Market Analysis**: Processes market data and generates trading signals
4. **Event Monitor**: Detects and responds to market events and triggers
5. **Agent Network**: Facilitates collaboration with other agents
6. **Dashboard**: Provides monitoring and control interface

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (for containerized deployment)
- Polymarket API Key
- Polysights API Key
- Ethereum Wallet with $VIRTUAL tokens

### Installation

#### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/acp-polymarket-agent.git
   cd acp-polymarket-agent
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

3. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

#### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/acp-polymarket-agent.git
   cd acp-polymarket-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

5. Initialize the database:
   ```bash
   python -m app.db.create_tables
   ```

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Documentation

- [User Guide](docs/user_guide.md): How to use and configure the agent
- [API Reference](docs/api_reference.md): API endpoints and schema documentation
- [Deployment Guide](docs/deployment_guide.md): Detailed deployment instructions
- [Development Guide](docs/development_guide.md): Information for contributors
- [Trading Strategies](docs/trading_strategies.md): Details on implemented strategies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [ACP Protocol](https://acp-protocol.org)
- [Polymarket](https://polymarket.com)
- [Polysights](https://polysights.xyz)
