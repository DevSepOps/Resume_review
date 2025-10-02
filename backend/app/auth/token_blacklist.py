from sqlalchemy import Column, String, DateTime, Integer, func
from core.database import Base

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    blacklisted_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)  # Token expiration time
    
    def __repr__(self):
        return f"<BlacklistedToken {self.token[:10]}...>"
