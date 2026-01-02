import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    logger.warning("MONGO_URI not set, using in-memory storage")

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.crypto_collection = None
        self.connected = False
        
        if MONGO_URI:
            try:
                self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client['trading_bot']
                self.users_collection = self.db['users']
                self.crypto_collection = self.db['crypto_addresses']
                self.connected = True
                logger.info("Successfully connected to MongoDB")
                self._initialize_crypto_addresses()
            except ConnectionFailure as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                self.connected = False
        
        # Fallback to in-memory storage
        if not self.connected:
            self.memory_users = {}
            self.memory_crypto = {
                'Bitcoin': 'bc1qvy8t9tn96c55vq0mk2tzgkcaews23a0jldqlzr',
                'Ethereum': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'USDT(ERC20)': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'XRP': 'rUfe1havVukiCcvvUupD5kCBkgMABjP1xk',
                'XLM': 'GANOQPCXRJO6DOGT6BFPKMKG2EFP33EATNRSJUH3ZWDCZVISSXAMIF4F',
                'BNB': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'Solana': 'FivNN2VAtrsaNAoj6gYbKmZnebYy54R3uQmTM7mh72xF'
            }
    
    def _initialize_crypto_addresses(self):
        """Initialize crypto addresses if not present"""
        if self.crypto_collection.count_documents({}) == 0:
            default_addresses = {
                'Bitcoin': 'bc1qvy8t9tn96c55vq0mk2tzgkcaews23a0jldqlzr',
                'Ethereum': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'USDT(ERC20)': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'XRP': 'rUfe1havVukiCcvvUupD5kCBkgMABjP1xk',
                'XLM': 'GANOQPCXRJO6DOGT6BFPKMKG2EFP33EATNRSJUH3ZWDCZVISSXAMIF4F',
                'BNB': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
                'Solana': 'FivNN2VAtrsaNAoj6gYbKmZnebYy54R3uQmTM7mh72xF'
            }
            for crypto, address in default_addresses.items():
                self.crypto_collection.update_one(
                    {'name': crypto},
                    {'$set': {'address': address}},
                    upsert=True
                )
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data"""
        if self.connected:
            user = self.users_collection.find_one({'user_id': user_id})
            if user:
                user.pop('_id', None)
            return user
        else:
            return self.memory_users.get(user_id)
    
    def save_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Save user data"""
        try:
            data['user_id'] = user_id
            if self.connected:
                self.users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': data},
                    upsert=True
                )
            else:
                self.memory_users[user_id] = data
            return True
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
            return False
    
    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        """Get all users"""
        if self.connected:
            users = {}
            for user in self.users_collection.find():
                user_id = user.pop('user_id')
                user.pop('_id', None)
                users[user_id] = user
            return users
        else:
            return self.memory_users
    
    def get_crypto_address(self, crypto_name: str) -> Optional[str]:
        """Get crypto address"""
        if self.connected:
            crypto = self.crypto_collection.find_one({'name': crypto_name})
            return crypto['address'] if crypto else None
        else:
            return self.memory_crypto.get(crypto_name)
    
    def get_all_crypto_addresses(self) -> Dict[str, str]:
        """Get all crypto addresses"""
        if self.connected:
            addresses = {}
            for crypto in self.crypto_collection.find():
                addresses[crypto['name']] = crypto['address']
            return addresses
        else:
            return self.memory_crypto
    
    def update_crypto_address(self, crypto_name: str, address: str) -> bool:
        """Update crypto address"""
        try:
            if self.connected:
                self.crypto_collection.update_one(
                    {'name': crypto_name},
                    {'$set': {'address': address}},
                    upsert=True
                )
            else:
                self.memory_crypto[crypto_name] = address
            return True
        except Exception as e:
            logger.error(f"Error updating crypto address {crypto_name}: {e}")
            return False

# Global database instance
db = Database()