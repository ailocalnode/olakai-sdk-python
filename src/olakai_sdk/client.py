import json
import os
import threading
import time
from dataclasses import asdict
from typing import Optional, List, Union
import requests

from .types import SDKConfig, MonitorPayload, BatchRequest, APIResponse

# Default config
subdomain = "staging.app"  # TODO: make this dynamic
isBatchingEnabled = False

config = SDKConfig(
    apiKey="",
    apiUrl=f"https://{subdomain}.olakai.ai/api/monitoring/prompt",
)

batchQueue: List[BatchRequest] = []
batchTimer: Optional[threading.Timer] = None
isOnline = True  # No browser events; assume online

QUEUE_FILE = "olakai_sdk_queue.json"

def init_client(key_or_config: Union[str, SDKConfig]):
    global config
    if isinstance(key_or_config, str):
        config.apiKey = key_or_config
    else:
        # Merge with defaults
        for field_name, value in key_or_config.__dict__.items():
            setattr(config, field_name, value)
    if config.verbose:
        print("[Olakai SDK] Config:", config)
    # Load persisted queue
    if config.enableLocalStorage:
        try:
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r") as f:
                    parsed_queue = json.load(f)
                    for item in parsed_queue:
                        batchQueue.append(BatchRequest(**item))
                if config.debug:
                    print(f"[Olakai SDK] Loaded {len(parsed_queue)} items from file")
        except Exception as err:
            if config.debug:
                print("[Olakai SDK] Failed to load from file:", err)
    if batchQueue and isOnline:
        if config.verbose:
            print("[Olakai SDK] Starting batch processing")
        process_batch_queue()

def get_config() -> SDKConfig:
    return config

def persist_queue():
    if not config.enableLocalStorage:
        return
    try:
        serialized = json.dumps([b.__dict__ for b in batchQueue])
        if len(serialized) > config.maxLocalStorageSize:
            target_size = int(config.maxLocalStorageSize * 0.8)
            while len(json.dumps([b.__dict__ for b in batchQueue])) > target_size and batchQueue:
                batchQueue.pop(0)
        with open(QUEUE_FILE, "w") as f:
            json.dump([b.__dict__ for b in batchQueue], f)
        if config.verbose:
            print("[Olakai SDK] Persisted queue to file")
    except Exception as err:
        if config.debug:
            print("[Olakai SDK] Failed to persist queue:", err)

def sleep(ms: int):
    if config.verbose:
        print(f"[Olakai SDK] Sleeping for {ms} ms")
    time.sleep(ms / 1000)

def make_api_call(payload: Union[MonitorPayload, List[MonitorPayload]]) -> APIResponse:
    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    if not config.apiUrl:
        raise Exception("[Olakai SDK] API URL is not set")
    headers = {"x-api-key": config.apiKey}
    data = {"batch": payload} if isinstance(payload, list) else payload
    data_dict = asdict(data) if isinstance(data, MonitorPayload) else data
    try:
        response = requests.post(
            config.apiUrl,
            headers=headers,
            json=json.dumps(data_dict),
            timeout=config.timeout / 1000,
        )
        if config.verbose:
            print("[Olakai SDK] API response:", response)
        response.raise_for_status()
        result = response.json()
        return APIResponse(success=True, data=result)
    except Exception as err:
        raise err

def send_with_retry(payload: Union[MonitorPayload, List[MonitorPayload]]) -> bool:
    if config.retries <= 0:
        return make_api_call(payload).success
    else:
        max_retries = config.retries
    last_error = None
    for attempt in range(config.retries + 1):
        try:
            make_api_call(payload)
            return True
        except Exception as err:
            last_error = err
            if config.debug:
                print(f"[Olakai SDK] Attempt {attempt+1}/{max_retries+1} failed:", err)
            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                sleep(delay)
    if config.onError and last_error:
        config.onError(last_error)
    if config.debug:
        print("[Olakai SDK] All retry attempts failed:", last_error)
    return False

def schedule_batch_processing():
    global batchTimer
    if batchTimer:
        return
    batchTimer = threading.Timer(config.batchTimeout / 1000, process_batch_queue)
    batchTimer.start()

def process_batch_queue():
    global batchTimer
    if batchTimer:
        batchTimer.cancel()
        batchTimer = None
    if not batchQueue or not isOnline:
        return
    # Sort by priority
    priority_order = {"high": 0, "normal": 1, "low": 2}
    batchQueue.sort(key=lambda x: priority_order.get(x.priority, 1))
    # Group into batches
    batches = [batchQueue[i:i+config.batchSize] for i in range(0, len(batchQueue), config.batchSize)]
    successful_batches = set()
    for batch_index, batch in enumerate(batches):
        payloads = [item.payload for item in batch]
        try:
            success = send_with_retry(payloads)
            if success:
                successful_batches.add(batch_index)
                if config.verbose:
                    print(f"[Olakai SDK] Successfully sent batch of {len(batch)} items")
        except Exception as err:
            if config.debug:
                print(f"[Olakai SDK] Batch {batch_index} failed:", err)
    # Remove successfully sent items
    remove_count = 0
    for i in range(len(batches)):
        if i in successful_batches:
            remove_count += len(batches[i])
        else:
            break
    if remove_count > 0:
        del batchQueue[:remove_count]
        persist_queue()
    if batchQueue:
        schedule_batch_processing()

def send_to_api(payload: MonitorPayload, options: dict = {}):
    if not config.apiKey:
        if config.debug:
            print("[Olakai SDK] API key is not set.")
        return
    if isBatchingEnabled:
        batch_item = BatchRequest(
            id=f"{int(time.time() * 1000)}",
            payload=payload,
            timestamp=int(time.time() * 1000),
            retries=0,
            priority=options.get("priority", "normal"),
        )
        batchQueue.append(batch_item)
        persist_queue()
        if len(batchQueue) >= config.batchSize or options.get("priority") == "high":
            process_batch_queue()
        else:
            schedule_batch_processing()
    else:
        make_api_call(payload)

def get_queue_size() -> int:
    return len(batchQueue)

def clear_queue():
    global batchQueue
    batchQueue = []
    if config.enableLocalStorage and os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)
        if config.verbose:
            print("[Olakai SDK] Cleared queue from file")

def flush_queue():
    if config.verbose:
        print("[Olakai SDK] Flushing queue")
    process_batch_queue() 