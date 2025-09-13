"""
Authentication and user management models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.db_types import UUIDType, ArrayStringType, ArrayUUIDType, get_uuid_default
from app.core.database import Base
import uuid


class User(Base):
    """
    User model for authentication and access control
    """
    __tablename__ = "users"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), index=True)
    last_name = Column(String(100), index=True)
    
    # Contact information
    phone = Column(String(20), index=True)
    address = Column(Text)
    city = Column(String(100), index=True)
    state = Column(String(50), index=True)
    zip_code = Column(String(10), index=True)
    country = Column(String(2), default="US", index=True)
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    is_superuser = Column(Boolean, default=False, index=True)
    email_verified = Column(Boolean, default=False, index=True)
    phone_verified = Column(Boolean, default=False, index=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32))
    
    # Preferences
    timezone = Column(String(50), default="America/New_York")
    language = Column(String(5), default="en")
    notification_preferences = Column(JSON)
    dashboard_preferences = Column(JSON)
    
    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), index=True)
    last_activity_at = Column(DateTime(timezone=True), index=True)
    login_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_last_login', 'last_login_at', 'is_active'),
        Index('idx_user_created_active', 'created_at', 'is_active'),
        UniqueConstraint('email', name='uq_user_email'),
    )


class UserRole(Base):
    """
    User roles and permissions system
    """
    __tablename__ = "user_roles"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False, index=True)
    role_name = Column(String(100), nullable=False, index=True)
    
    # Role details
    role_description = Column(Text)
    is_primary_role = Column(Boolean, default=False, index=True)
    
    # Permissions
    permissions = Column(ArrayStringType, default=[])
    
    # Role status
    is_active = Column(Boolean, default=True, index=True)
    assigned_by = Column(UUIDType)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="roles")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_role_active', 'user_id', 'is_active'),
        Index('idx_role_name_active', 'role_name', 'is_active'),
        Index('idx_role_assigned_expires', 'assigned_at', 'expires_at'),
        UniqueConstraint('user_id', 'role_name', name='uq_user_role'),
    )


class UserPermission(Base):
    """
    Granular permissions system
    """
    __tablename__ = "user_permissions"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Permission identification
    permission_name = Column(String(100), unique=True, nullable=False, index=True)
    permission_category = Column(String(50), nullable=False, index=True)
    permission_description = Column(Text)
    
    # Permission details
    resource = Column(String(100), nullable=False, index=True)  # leads, analytics, exports, etc.
    action = Column(String(50), nullable=False, index=True)  # create, read, update, delete, export
    conditions = Column(JSON)  # Additional conditions for the permission
    
    # Permission status
    is_active = Column(Boolean, default=True, index=True)
    is_system_permission = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_category_resource', 'permission_category', 'resource'),
        Index('idx_permission_resource_action', 'resource', 'action'),
        Index('idx_permission_active_system', 'is_active', 'is_system_permission'),
        UniqueConstraint('permission_name', name='uq_permission_name'),
    )