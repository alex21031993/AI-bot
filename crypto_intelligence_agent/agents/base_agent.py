"""
Base Agent class for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class AgentResponse:
    """Standard response from agent"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = logger
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize agent resources"""
        self.logger.info(f"Initializing {self.name} agent")
        self.setup()
    
    @abstractmethod
    def setup(self) -> None:
        """Setup agent-specific resources"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> AgentResponse:
        """Execute agent task"""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters"""
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input and return response"""
        try:
            if not self.validate_input(**input_data):
                return AgentResponse(
                    success=False,
                    error="Invalid input parameters"
                )
            
            return await self.execute(**input_data)
            
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "config": self.config
        }
