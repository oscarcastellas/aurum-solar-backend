"""
Database type compatibility utilities
Handles PostgreSQL vs SQLite differences
"""

import os
from sqlalchemy import String, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# Detect database type from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///test.db')
IS_POSTGRESQL = DATABASE_URL.startswith('postgresql')

# Define compatible types
if IS_POSTGRESQL:
    # PostgreSQL types
    UUIDType = UUID(as_uuid=True)
    ArrayStringType = ARRAY(String)
    ArrayUUIDType = ARRAY(UUID)
else:
    # SQLite compatible types
    UUIDType = String(36)
    ArrayStringType = JSON
    ArrayUUIDType = JSON

# Helper function for array defaults
def get_array_default():
    """Get appropriate default for array columns"""
    if IS_POSTGRESQL:
        return []
    else:
        return []

# Helper function for UUID defaults
def get_uuid_default():
    """Get appropriate default for UUID columns"""
    import uuid
    return uuid.uuid4
