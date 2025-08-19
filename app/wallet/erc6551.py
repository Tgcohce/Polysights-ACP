"""
ERC-6551 Smart Wallet implementation for ACP agent.

This module provides functionality for interacting with ERC-6551 token-bound accounts,
handling transactions, and managing $VIRTUAL tokens.
"""
import os
from typing import Dict, Any, Optional, List, Union

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from loguru import logger
from web3 import Web3

from app.utils.config import config


class SmartWallet:
    """
    ERC-6551 Smart Wallet implementation for autonomous agent operations.
    
    Handles wallet creation, transaction signing, and token management.
    """
    
    def __init__(self):
        """Initialize the Smart Wallet with configuration settings."""
        self.private_key = config.acp.whitelisted_wallet_private_key
        
        # Configure web3 provider
        self.base_rpc_url = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        self.w3 = Web3(Web3.HTTPProvider(self.base_rpc_url))
        
        # ERC-6551 registry contract
        self.registry_address = os.getenv(
            "ERC6551_REGISTRY_ADDRESS", 
            "0x000000006551c19487814612e58FE06813775758"  # Standard ERC-6551 registry
        )
        self.registry_abi = self._load_registry_abi()
        self.registry_contract = self.w3.eth.contract(
            address=self.registry_address,
            abi=self.registry_abi
        )
        
        # Virtual token contract
        self.virtual_token_address = os.getenv(
            "VIRTUAL_TOKEN_ADDRESS",
            "0x0000000000000000000000000000000000000000"  # Replace with actual token address
        )
        # Convert to checksum address for web3.py compatibility
        self.virtual_token_address = self.w3.to_checksum_address(self.virtual_token_address)
        
        self.virtual_token_abi = self._load_virtual_token_abi()
        self.virtual_token_contract = self.w3.eth.contract(
            address=self.virtual_token_address,
            abi=self.virtual_token_abi
        )
        
        # Initialize account
        self._initialize_account()
        
    def _initialize_account(self) -> None:
        """Initialize the wallet account using the private key."""
        try:
            if self.private_key:
                self.account: LocalAccount = Account.from_key(self.private_key)
                self.address = self.account.address
                logger.info(f"Wallet initialized with address: {self.address}")
            else:
                # Create a new account if no private key provided
                self.account = Account.create()
                self.private_key = self.account.key.hex()
                self.address = self.account.address
                logger.warning(
                    f"Created new wallet with address {self.address}. "
                    "IMPORTANT: Save the private key securely!"
                )
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {e}")
            # Create a temporary account for development purposes
            self.account = Account.create()
            self.private_key = self.account.key.hex()
            self.address = self.account.address
            logger.warning(
                f"Using temporary wallet with address {self.address} due to initialization error"
            )
    
    def _load_registry_abi(self) -> List[Dict[str, Any]]:
        """
        Load the ERC-6551 registry ABI.
        
        Returns:
            List[Dict[str, Any]]: Registry ABI
        """
        # Simplified ABI for ERC-6551 Registry
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "implementation", "type": "address"},
                    {"internalType": "bytes32", "name": "salt", "type": "bytes32"},
                    {"internalType": "uint256", "name": "chainId", "type": "uint256"},
                    {"internalType": "address", "name": "tokenContract", "type": "address"},
                    {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
                ],
                "name": "account",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "implementation", "type": "address"},
                    {"internalType": "bytes32", "name": "salt", "type": "bytes32"},
                    {"internalType": "uint256", "name": "chainId", "type": "uint256"},
                    {"internalType": "address", "name": "tokenContract", "type": "address"},
                    {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
                    {"internalType": "bytes", "name": "initData", "type": "bytes"}
                ],
                "name": "createAccount",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def _load_virtual_token_abi(self) -> List[Dict[str, Any]]:
        """
        Load the $VIRTUAL token ABI.
        
        Returns:
            List[Dict[str, Any]]: $VIRTUAL token ABI
        """
        # Standard ERC-20 functions needed for token interactions
        return [
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "symbol",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def create_tba(
        self,
        implementation_address: str,
        token_contract: str,
        token_id: int,
        init_data: bytes = b""
    ) -> str:
        """
        Create a Token Bound Account (TBA) using ERC-6551 registry.
        
        Args:
            implementation_address: Address of the ERC-6551 implementation contract
            token_contract: NFT contract address
            token_id: NFT token ID
            init_data: Initialization data for the TBA
            
        Returns:
            str: Address of the created TBA
        """
        try:
            logger.info(f"Creating TBA for token {token_contract}:{token_id}")
            
            # Generate salt (could be deterministic based on some agent parameters)
            salt = self.w3.keccak(text=f"{config.acp.agent_name}:{token_id}")
            
            # Get chain ID from the connected network
            chain_id = self.w3.eth.chain_id
            
            # Check if account already exists
            tba_address = self.registry_contract.functions.account(
                implementation_address,
                salt,
                chain_id,
                token_contract,
                token_id
            ).call()
            
            if self.w3.eth.get_code(tba_address):
                logger.info(f"TBA already exists at {tba_address}")
                return tba_address
            
            # Create new account
            tx = self.registry_contract.functions.createAccount(
                implementation_address,
                salt,
                chain_id,
                token_contract,
                token_id,
                init_data
            ).build_transaction({
                "from": self.address,
                "nonce": self.w3.eth.get_transaction_count(self.address),
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get the created account address
            created_address = self.registry_contract.functions.account(
                implementation_address,
                salt,
                chain_id,
                token_contract,
                token_id
            ).call()
            
            logger.info(f"Successfully created TBA at address {created_address}")
            return created_address
            
        except Exception as e:
            logger.error(f"Failed to create TBA: {e}")
            raise
    
    async def sign_message(self, message: str) -> str:
        """
        Sign a message using the wallet's private key.
        
        Args:
            message: Message to sign
            
        Returns:
            str: Signature hex string
        """
        try:
            message_hash = encode_defunct(text=message)
            signed_message = self.w3.eth.account.sign_message(
                message_hash,
                private_key=self.private_key
            )
            return signed_message.signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            raise
    
    async def get_token_balance(self, token_symbol: str = "VIRTUAL") -> float:
        """
        Get token balance for the specified token.
        
        Args:
            token_symbol: Token symbol (default: VIRTUAL)
            
        Returns:
            float: Token balance as a float
        """
        try:
            if token_symbol != "VIRTUAL":
                logger.warning(f"Only VIRTUAL token is supported, got: {token_symbol}")
            
            # Query token balance
            balance_wei = self.virtual_token_contract.functions.balanceOf(
                self.address
            ).call()
            
            # Get token decimals
            decimals = self.virtual_token_contract.functions.decimals().call()
            
            # Convert to float
            balance = balance_wei / (10 ** decimals)
            
            logger.info(f"Current {token_symbol} balance: {balance}")
            return balance
            
        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            # Return mock balance for development
            return 100.0
    
    async def transfer_tokens(
        self, 
        to_address: str, 
        amount: float, 
        token_symbol: str = "VIRTUAL"
    ) -> Dict[str, Any]:
        """
        Transfer tokens to another address.
        
        Args:
            to_address: Recipient address
            amount: Amount to transfer (in token units, not wei)
            token_symbol: Token symbol (default: VIRTUAL)
            
        Returns:
            Dict[str, Any]: Transaction receipt
        """
        try:
            if token_symbol != "VIRTUAL":
                logger.warning(f"Only VIRTUAL token is supported, got: {token_symbol}")
            
            # Get token decimals
            decimals = self.virtual_token_contract.functions.decimals().call()
            
            # Convert to wei
            amount_wei = int(amount * (10 ** decimals))
            
            # Build transaction
            tx = self.virtual_token_contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                "from": self.address,
                "nonce": self.w3.eth.get_transaction_count(self.address),
                "gas": 100000,
                "gasPrice": self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Successfully transferred {amount} {token_symbol} to {to_address}")
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "from": self.address,
                "to": to_address,
                "amount": amount,
                "token": token_symbol
            }
            
        except Exception as e:
            logger.error(f"Failed to transfer tokens: {e}")
            return {
                "success": False,
                "error": str(e),
                "from": self.address,
                "to": to_address,
                "amount": amount,
                "token": token_symbol
            }
    
    async def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get wallet information.
        
        Returns:
            Dict[str, Any]: Wallet information
        """
        try:
            # Get ETH balance
            eth_balance = self.w3.eth.get_balance(self.address)
            eth_balance_ether = self.w3.from_wei(eth_balance, "ether")
            
            # Get $VIRTUAL balance
            virtual_balance = await self.get_token_balance("VIRTUAL")
            
            return {
                "address": self.address,
                "chain_id": self.w3.eth.chain_id,
                "network": "Base Mainnet" if self.w3.eth.chain_id == 8453 else "Unknown",
                "eth_balance": eth_balance_ether,
                "virtual_balance": virtual_balance,
                "is_contract": len(self.w3.eth.get_code(self.address)) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get wallet info: {e}")
            return {
                "address": self.address,
                "error": str(e)
            }
