"""
Database Models për Email Tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class EmailLog(Base):
    """Model për tracking të emailave të dërguar"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_type = Column(String(50), nullable=False)  # welcome, streak_warning, weekly_report
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="email_logs")


class UserLoginActivity(Base):
    """Model për tracking të login activity"""
    __tablename__ = "user_login_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="login_activities")


# Update User model në models.py për të shtuar relationships
# Duhet të shtohet këto në User class:
# email_logs = relationship("EmailLog", back_populates="user")
# login_activities = relationship("UserLoginActivity", back_populates="user")
