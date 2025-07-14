from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Union

@dataclass
class MonitorPayload:
    userId: str
    chatId: str
    prompt: str
    response: str
    tokens: Optional[int]
    requestTime: Optional[int]
    errorMessage: Optional[str]
    
@dataclass
class BatchRequest:
    id: str
    payload: MonitorPayload
    timestamp: int
    retries: int = 0
    priority: str = "normal"  # 'low', 'normal', 'high'

@dataclass
class APIResponse:
    success: bool
    # Add more fields as needed, e.g., message, data, etc.
    data: Optional[Any] = None
    message: Optional[str] = None

@dataclass
class SDKConfig:
    apiKey: str = ""
    apiUrl: Optional[str] = None
    batchSize: int = 10
    batchTimeout: int = 5000  # milliseconds
    retries: int = 3
    timeout: int = 20000  # milliseconds
    enableLocalStorage: bool = True
    localStorageKey: str = "olakai-sdk-queue"
    maxLocalStorageSize: int = 1000000  # 1MB
    debug: bool = False
    verbose: bool = False
    onError: Optional[Callable[[Exception], None]] = None 