from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Union

@dataclass
class MonitorPayload:
    email: str
    chatId: str
    prompt: str
    response: str
    shouldScore: bool
    tokens: Optional[int]
    requestTime: Optional[int]
    errorMessage: Optional[str]
    task: Optional[str]
    subTask: Optional[str]
    
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
    sanitize_patterns: Optional[List[Any]] = None

@dataclass
class MonitorOptions:
    capture: Optional[Callable] = None
    sanitize: bool = False
    on_error: Optional[Callable] = None
    priority: str = "normal"
    email: Optional[Union[str, Callable]] = "anonymous@olakai.ai"
    chatId: Optional[Union[str, Callable]] = "123"
    shouldScore: bool = False
    task: Optional[str] = None
    subTask: Optional[str] = None

@dataclass 
class Middleware:
    name: str
    before_call: Optional[Callable] = None
    after_call: Optional[Callable] = None
    on_error: Optional[Callable] = None 