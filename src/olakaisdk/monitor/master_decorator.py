from typing import Callable, List, Optional
from .decorator import olakai_monitor
from ..shared.utils import generate_random_id
from .types import MonitorOptions
from dataclasses import fields


class OlakaiMasterDecorator:
    
    def __init__(self, func: Optional[Callable] = None, **kwargs):
        self.func: Optional[Callable] = func
        self.stack_track: List[str] = []
        self.chatId: str = kwargs.get("chatId", generate_random_id())
        self.monitor_options: MonitorOptions = MonitorOptions(chatId=self.chatId, **kwargs)
    
    def __call__(self, *args, **kwargs):
        self.chatId: str = kwargs.get("chatId", generate_random_id())
        self.monitor_options.chatId = self.chatId
        return olakai_monitor(self.func, **self.monitor_options)

    def sub_decorator(self, **kwargs):
        
        # Combiner les paramètres globaux avec les paramètres locaux
        # Les paramètres locaux ont la priorité (override)
        global_params = {field.name: getattr(self.monitor_options, field.name) for field in fields(MonitorOptions)}
        
        # Supprimer les paramètres None des paramètres globaux
        global_params = {k: v for k, v in global_params.items() if v is not None}
        
        # Fusionner avec les paramètres locaux (kwargs ont la priorité)
        combined_params = {**global_params, **kwargs}
        
        return olakai_monitor(**combined_params)
    