# ACP Polymarket Trading Agent: Deployment Guide

This guide provides detailed instructions for deploying the ACP Polymarket Trading Agent in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Options](#deployment-options)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [Cloud Deployment](#cloud-deployment)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Security Considerations](#security-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the ACP Polymarket Trading Agent, ensure you have:

- **Polymarket API Key**: Register at the [Polymarket Developer Portal](https://polymarket.com/developers)
- **Polysights API Key**: Obtain from [Polysights](https://polysights.xyz)
- **Ethereum Wallet**: An Ethereum wallet with private key and sufficient $VIRTUAL tokens
- **ACP Registration**: Register as an agent on the ACP Protocol to obtain your agent ID

### System Requirements

#### Minimum Requirements
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Ubuntu 20.04 LTS or newer / Windows Server 2019 or newer

#### Recommended Requirements
- 4 CPU cores
- 8GB RAM
- 50GB SSD storage
- Ubuntu 22.04 LTS / Windows Server 2022

## Environment Setup

### Required Software

- **Docker**: v20.10 or newer
- **Docker Compose**: v2.0 or newer
- **Python**: 3.10 or newer (if not using Docker)
- **PostgreSQL**: 14 or newer (if not using the containerized database)
- **Git**: 2.30 or newer

### Network Requirements

- Outbound access to:
  - Polymarket API (`clob.polymarket.com`)
  - Polysights API (`api.polysights.xyz`)
  - ACP Service Registry
  - Ethereum/Polygon RPC nodes

## Deployment Options

### Local Development

For development and testing purposes:

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

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy and configure the environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

5. Initialize the database:
   ```bash
   python -m app.db.create_tables
   ```

6. Run the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The application will be available at `http://localhost:8000`.

### Docker Deployment

#### Using the Deploy Script (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/acp-polymarket-agent.git
   cd acp-polymarket-agent
   ```

2. Copy and configure the environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```

4. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

The script will:
- Validate your environment configuration
- Build and start the Docker containers
- Initialize the database
- Verify that services are running correctly

#### Manual Docker Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/acp-polymarket-agent.git
   cd acp-polymarket-agent
   ```

2. Copy and configure the environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. Build the Docker images:
   ```bash
   docker-compose build
   ```

4. Start the services:
   ```bash
   docker-compose up -d
   ```

The services will be available at:
- Agent API and Dashboard: `http://localhost:8000`
- PgAdmin (database management): `http://localhost:5050`

### Cloud Deployment

#### AWS Deployment

1. **Prerequisites**:
   - AWS CLI installed and configured
   - Docker installed locally
   - ECR repository created
   - ECS cluster configured
   - RDS PostgreSQL instance created

2. **Configure AWS RDS**:
   - Create a PostgreSQL RDS instance
   - Configure security groups to allow access from your ECS cluster
   - Update the `.env` file with RDS connection details

3. **Build and push Docker image**:
   ```bash
   aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
   docker build -t your-account-id.dkr.ecr.your-region.amazonaws.com/acp-agent:latest .
   docker push your-account-id.dkr.ecr.your-region.amazonaws.com/acp-agent:latest
   ```

4. **Deploy to ECS**:
   - Create a task definition using the ECR image
   - Configure environment variables from your `.env` file
   - Create or update an ECS service
   - Configure an Application Load Balancer if needed

#### Azure Deployment

1. **Prerequisites**:
   - Azure CLI installed and configured
   - Docker installed locally
   - Azure Container Registry created
   - Azure Container Apps environment configured
   - Azure Database for PostgreSQL created

2. **Configure Azure PostgreSQL**:
   - Create a PostgreSQL server instance
   - Configure firewall rules to allow access from your Container Apps
   - Update the `.env` file with PostgreSQL connection details

3. **Build and push Docker image**:
   ```bash
   az acr login --name YourRegistryName
   docker build -t yourregistryname.azurecr.io/acp-agent:latest .
   docker push yourregistryname.azurecr.io/acp-agent:latest
   ```

4. **Deploy to Azure Container Apps**:
   ```bash
   az containerapp create \
     --name acp-agent \
     --resource-group YourResourceGroup \
     --environment YourContainerAppsEnvironment \
     --image yourregistryname.azurecr.io/acp-agent:latest \
     --registry-server yourregistryname.azurecr.io \
     --env-vars DATABASE_HOST=yourdb.postgres.database.azure.com DATABASE_USER=your_user DATABASE_PASSWORD=your_password
   ```

## Database Setup

### Using Containerized PostgreSQL

The Docker Compose setup includes a PostgreSQL container configured for immediate use with the agent. The database will be initialized when the container first starts.

Database data is persisted in a Docker volume named `postgres_data`.

### Using External PostgreSQL

To use an external PostgreSQL server:

1. Create a database:
   ```sql
   CREATE DATABASE acp_agent;
   CREATE USER acp_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE acp_agent TO acp_user;
   ```

2. Update your `.env` file with the database connection details:
   ```
   DATABASE_USER=acp_user
   DATABASE_PASSWORD=your_secure_password
   DATABASE_HOST=your_db_host
   DATABASE_PORT=5432
   DATABASE_NAME=acp_agent
   ```

3. Initialize the database schema:
   ```bash
   python -m app.db.create_tables
   ```

### Database Migrations

For database schema updates, the agent uses Alembic migrations:

1. Generate a new migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

## Configuration

### Environment Variables

The agent's behavior is configured through environment variables. Critical variables include:

#### Core Configuration
- `ACP_AGENT_ID`: Your agent's unique ID in the ACP ecosystem
- `ACP_AGENT_NAME`: Human-readable name for your agent
- `ACP_SERVICE_REGISTRY`: URL of the ACP service registry

#### Database Configuration
- `DATABASE_USER`: Database username
- `DATABASE_PASSWORD`: Database password
- `DATABASE_HOST`: Database host address
- `DATABASE_PORT`: Database port (default: 5432)
- `DATABASE_NAME`: Database name
- `DATABASE_ECHO`: Set to "true" to log SQL queries (default: "false")

#### Blockchain Configuration
- `WALLET_PRIVATE_KEY`: Private key for your ERC-6551 wallet
- `VIRTUAL_TOKEN_ADDRESS`: Address of the $VIRTUAL token contract
- `CHAIN_ID`: Chain ID (1 for Ethereum Mainnet, 137 for Polygon)

#### API Keys
- `POLYMARKET_API_KEY`: Your Polymarket API key
- `POLYSIGHTS_API_KEY`: Your Polysights API key

### Configuration Files

For configuration that doesn't fit in environment variables, the agent uses YAML files:

- `config/strategies.yaml`: Configuration for trading strategies
- `config/triggers.yaml`: Default event triggers
- `config/markets.yaml`: Market-specific settings

## Security Considerations

### API Key Management

Never commit API keys or private keys to your repository. Always use environment variables or secure secret management solutions.

For cloud deployments, use the platform's secrets management:
- AWS: AWS Secrets Manager
- Azure: Azure Key Vault
- GCP: Google Secret Manager

### Database Security

- Use strong, unique passwords for database access
- Limit database access to only the necessary IP addresses
- Enable SSL for database connections
- Regularly back up the database

### Wallet Security

- Use a dedicated wallet for the agent with only the necessary funds
- Consider using a hardware wallet for the root key
- Implement transaction signing on a separate, secured service

## Monitoring and Maintenance

### Logging

Logs are written to:
- Console output
- `/app/logs` directory inside the container
- Configurable external services (optional)

Configure log level using the `LOG_LEVEL` environment variable.

### Health Checks

The agent provides a health check endpoint at `/health` that returns the status of:
- API connectivity (Polymarket, Polysights)
- Database connection
- Wallet balance
- Overall system status

### Backups

#### Database Backups

For the containerized database:

```bash
docker exec acp-agent-db pg_dump -U postgres acp_agent > backup_$(date +%Y-%m-%d).sql
```

For cloud-managed databases, use the platform's backup features.

### Updating

To update the agent:

1. Pull the latest code:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart the containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Troubleshooting

### Common Issues

#### Connection Errors

**Issue**: The agent can't connect to Polymarket API.
**Solution**: 
- Verify your API key is correct
- Check your network configuration allows outbound connections
- Ensure the Polymarket API is not experiencing downtime

#### Database Errors

**Issue**: Database connection fails.
**Solution**:
- Check database credentials in `.env`
- Ensure the database server is running
- Verify network connectivity to the database
- Check if the database exists and user has proper permissions

#### Wallet Errors

**Issue**: Wallet transactions fail.
**Solution**:
- Ensure your wallet has sufficient funds
- Verify the private key is correct
- Check network configuration for blockchain RPC access
- Verify gas settings are appropriate for current network conditions

### Getting Help

If you encounter issues not covered in this guide:

1. Check the application logs:
   ```bash
   docker logs acp-polymarket-agent
   ```

2. Check the database logs:
   ```bash
   docker logs acp-agent-db
   ```

3. Consult the [GitHub repository issues](https://github.com/yourusername/acp-polymarket-agent/issues)

4. Join the ACP Discord community for community support
