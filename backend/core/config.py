"""
VULNOT Backend Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "vulnot-super-secret-token"
    INFLUXDB_ORG: str = "vulnot"
    INFLUXDB_BUCKET: str = "process_data"
    
    # Modbus
    MODBUS_HOST: str = "localhost"
    MODBUS_PORT: int = 502
    
    # Application
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()