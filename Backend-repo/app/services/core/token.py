"""
Redis token storage service for managing refresh tokens and token blacklisting.
Handles token storage, retrieval, revocation, and cleanup operations.
"""

import redis
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ...settings.base import get_settings
from ...core.auth import extract_user_id_from_token, get_token_expiry


class TokenInfo(BaseModel):
    """Token information structure."""
    user_id: int
    token_hash: str
    expires_at: datetime
    created_at: datetime
    is_revoked: bool = False


class TokenStorageService:
    """Redis-based token storage service."""
    
    def __init__(self):
        """Initialize Redis connection."""
        settings = get_settings()
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )
        
        # Key prefixes for different token types
        self.REFRESH_TOKEN_PREFIX = "refresh_token:"
        self.BLACKLIST_PREFIX = "blacklist:"
        self.USER_TOKENS_PREFIX = "user_tokens:"
        
    def _hash_token(self, token: str) -> str:
        """
        Create a hash of the token for storage.
        
        Args:
            token: JWT token to hash
            
        Returns:
            str: SHA256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _get_refresh_token_key(self, token_hash: str) -> str:
        """Get Redis key for refresh token."""
        return f"{self.REFRESH_TOKEN_PREFIX}{token_hash}"
    
    def _get_blacklist_key(self, token_hash: str) -> str:
        """Get Redis key for blacklisted token."""
        return f"{self.BLACKLIST_PREFIX}{token_hash}"
    
    def _get_user_tokens_key(self, user_id: int) -> str:
        """Get Redis key for user's tokens."""
        return f"{self.USER_TOKENS_PREFIX}{user_id}"
    
    def store_refresh_token(
        self,
        token: str,
        user_id: int,
        expires_at: datetime
    ) -> bool:
        """
        Store a refresh token in Redis.
        
        Args:
            token: Refresh token to store
            user_id: User ID associated with the token
            expires_at: Token expiration time
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            token_hash = self._hash_token(token)
            token_key = self._get_refresh_token_key(token_hash)
            user_tokens_key = self._get_user_tokens_key(user_id)
            
            # Calculate TTL in seconds
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl <= 0:
                return False
            
            # Store token info
            token_info = {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "is_revoked": False
            }
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Store refresh token with TTL
            pipe.setex(token_key, ttl, json.dumps(token_info))
            
            # Add token hash to user's token set with TTL
            pipe.sadd(user_tokens_key, token_hash)
            pipe.expire(user_tokens_key, ttl)
            
            pipe.execute()
            return True
            
        except Exception as e:
            print(f"Error storing refresh token: {e}")
            return False
    
    def get_refresh_token(self, token: str) -> Optional[TokenInfo]:
        """
        Retrieve refresh token information.
        
        Args:
            token: Refresh token to retrieve
            
        Returns:
            TokenInfo: Token information or None if not found
        """
        try:
            token_hash = self._hash_token(token)
            token_key = self._get_refresh_token_key(token_hash)
            
            token_data = self.redis_client.get(token_key)
            if not token_data:
                return None
            
            token_info = json.loads(token_data)
            return TokenInfo(
                user_id=token_info["user_id"],
                token_hash=token_info["token_hash"],
                expires_at=datetime.fromisoformat(token_info["expires_at"]),
                created_at=datetime.fromisoformat(token_info["created_at"]),
                is_revoked=token_info.get("is_revoked", False)
            )
            
        except Exception as e:
            print(f"Error retrieving refresh token: {e}")
            return None
    
    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            token: Refresh token to revoke
            
        Returns:
            bool: True if revoked successfully, False otherwise
        """
        try:
            token_hash = self._hash_token(token)
            token_key = self._get_refresh_token_key(token_hash)
            
            # Get current token info
            token_data = self.redis_client.get(token_key)
            if not token_data:
                return False
            
            token_info = json.loads(token_data)
            token_info["is_revoked"] = True
            
            # Update token info
            ttl = self.redis_client.ttl(token_key)
            if ttl > 0:
                self.redis_client.setex(token_key, ttl, json.dumps(token_info))
                return True
            
            return False
            
        except Exception as e:
            print(f"Error revoking refresh token: {e}")
            return False
    
    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: User ID whose tokens to revoke
            
        Returns:
            bool: True if revoked successfully, False otherwise
        """
        try:
            user_tokens_key = self._get_user_tokens_key(user_id)
            token_hashes = self.redis_client.smembers(user_tokens_key)
            
            if not token_hashes:
                return True
            
            pipe = self.redis_client.pipeline()
            
            for token_hash in token_hashes:
                token_key = self._get_refresh_token_key(token_hash)
                
                # Get current token info
                token_data = self.redis_client.get(token_key)
                if token_data:
                    token_info = json.loads(token_data)
                    token_info["is_revoked"] = True
                    
                    # Update token info
                    ttl = self.redis_client.ttl(token_key)
                    if ttl > 0:
                        pipe.setex(token_key, ttl, json.dumps(token_info))
            
            # Clear user's token set
            pipe.delete(user_tokens_key)
            pipe.execute()
            
            return True
            
        except Exception as e:
            print(f"Error revoking user tokens: {e}")
            return False
    
    def blacklist_token(self, token: str, ttl_seconds: Optional[int] = None) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: Token to blacklist
            ttl_seconds: TTL for blacklist entry (optional)
            
        Returns:
            bool: True if blacklisted successfully, False otherwise
        """
        try:
            token_hash = self._hash_token(token)
            blacklist_key = self._get_blacklist_key(token_hash)
            
            # If no TTL provided, calculate from token expiry
            if ttl_seconds is None:
                token_expiry = get_token_expiry(token)
                if token_expiry:
                    ttl_seconds = int((token_expiry - datetime.utcnow()).total_seconds())
                else:
                    ttl_seconds = 3600  # Default 1 hour
            
            if ttl_seconds <= 0:
                ttl_seconds = 60  # Minimum 1 minute
            
            # Store blacklist entry with TTL
            blacklist_info = {
                "token_hash": token_hash,
                "blacklisted_at": datetime.utcnow().isoformat(),
                "user_id": extract_user_id_from_token(token)
            }
            
            self.redis_client.setex(
                blacklist_key,
                ttl_seconds,
                json.dumps(blacklist_info)
            )
            
            return True
            
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: Token to check
            
        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        try:
            token_hash = self._hash_token(token)
            blacklist_key = self._get_blacklist_key(token_hash)
            
            return self.redis_client.exists(blacklist_key) > 0
            
        except Exception as e:
            print(f"Error checking token blacklist: {e}")
            return False
    
    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Clean up expired tokens from Redis.
        This is handled automatically by Redis TTL, but this method
        provides statistics about cleanup operations.
        
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        try:
            stats = {
                "refresh_tokens_cleaned": 0,
                "blacklist_entries_cleaned": 0,
                "user_token_sets_cleaned": 0
            }
            
            # Get all keys with our prefixes
            refresh_keys = self.redis_client.keys(f"{self.REFRESH_TOKEN_PREFIX}*")
            blacklist_keys = self.redis_client.keys(f"{self.BLACKLIST_PREFIX}*")
            user_token_keys = self.redis_client.keys(f"{self.USER_TOKENS_PREFIX}*")
            
            # Check TTL and count expired keys (Redis handles cleanup automatically)
            for key in refresh_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    stats["refresh_tokens_cleaned"] += 1
            
            for key in blacklist_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    stats["blacklist_entries_cleaned"] += 1
            
            for key in user_token_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    stats["user_token_sets_cleaned"] += 1
            
            return stats
            
        except Exception as e:
            print(f"Error during token cleanup: {e}")
            return {"error": str(e)}
    
    def get_user_active_tokens_count(self, user_id: int) -> int:
        """
        Get count of active refresh tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Number of active tokens
        """
        try:
            user_tokens_key = self._get_user_tokens_key(user_id)
            return self.redis_client.scard(user_tokens_key)
            
        except Exception as e:
            print(f"Error getting user token count: {e}")
            return 0
    
    def get_token_info_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all token information for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Dict]: List of token information
        """
        try:
            user_tokens_key = self._get_user_tokens_key(user_id)
            token_hashes = self.redis_client.smembers(user_tokens_key)
            
            tokens_info = []
            for token_hash in token_hashes:
                token_key = self._get_refresh_token_key(token_hash)
                token_data = self.redis_client.get(token_key)
                
                if token_data:
                    token_info = json.loads(token_data)
                    tokens_info.append(token_info)
            
            return tokens_info
            
        except Exception as e:
            print(f"Error getting user token info: {e}")
            return []


# Global token service instance
_token_service: Optional[TokenStorageService] = None


def get_token_service() -> TokenStorageService:
    """Get the global token service instance."""
    global _token_service
    if _token_service is None:
        _token_service = TokenStorageService()
    return _token_service