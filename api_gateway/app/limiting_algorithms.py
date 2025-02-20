from datetime import datetime
import threading
from fastapi import HTTPException

class RateLimit:
    def __init__(self):
        self.interval = 60
        self.limit_per_interval = 60
        self.lock = threading.Lock()

class RateLimitExceeded(HTTPException):
    def __init__(self, detail="Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

# Implement the TokenBucket class, which inherits from the RateLimit class.
# The TokenBucket class is used to limit the number of requests that can be made to an API endpoint.
class TokenBucket(RateLimit):
    """
    The TokenBucket class is used to limit the number of requests that can be made to an API endpoint.
    The token_interval is set to 1 second, and the tokens_per_interval is set to 1.
    The total_capacity is set to 10, which means that the bucket can hold a maximum of 10 tokens.
    The tokens attribute is initialized to 10, which represents the number of tokens currently in the bucket.
    The last_updated attribute is used to capture the timestamp of the last API request made.
    The lock attribute is used to ensure that the operations we perform are consistent and atomic."""
    def __init__(self):
        super().__init__()
        self.total_capacity = 10
        self.token_interval = 1
        self.tokens_per_interval = 1
        # Initial value of self.tokens = 10. Each time an API call is made, this value is reduced.
        self.tokens = 10
        # Capture the timestamp of the last API request made. 
        self.last_updated = datetime.now()
        # We are using threading.Lock() to ensure that the operations we perform are consistent and atomic
        self.lock = threading.Lock()

    def allow_request(self, ip):
        with self.lock:
            # Calculate the time difference between the current time and the time when the last API call was executed.
            curr = datetime.now()
            gap = (curr - self.last_updated).total_seconds()
            tokens_to_add =  gap*self.tokens_per_interval
            self.tokens = min(self.total_capacity,tokens_to_add+self.tokens)
            self.last_updated = curr

            if self.tokens>=1:
                self.tokens-=1
                return True
            raise RateLimitExceeded()
        
# Implement the FixedCounterWindow class, which inherits from the RateLimit class.
# The FixedCounterWindow class is used to limit the number of requests that can be made to an API endpoint.
class FixedCounterWindow(RateLimit):
    """
    Employ a 60-second time window, which begins at the 0th second and 0th microsecond. 
    When an API call is initiated, we record the current time and commence incrementing the counter.
    """
    def __init__(self):
        super().__init__()
        self.counter = 0
        # Employ a 60-second time window, which begins at the 0th second and 0th microsecond. 
        # When an API call is initiated, we record the current time and commence incrementing the counter. 
        self.curr_time = datetime.now().time().replace(second=0,microsecond=0)
    
    def allow_request(self,ip):
        with self.lock:
            curr = datetime.now().time().replace(second=0,microsecond=0)
            if curr!=self.curr_time:
                self.curr_time = curr
                self.counter = 0
            
            if self.counter>=self.limit_per_interval:
                raise RateLimitExceeded()
            self.counter+=1
            return True

# Implement the SlidingWindow class, which inherits from the RateLimit class.
# The SlidingWindow class is used to limit the number of requests that can be made to an API endpoint.        
class SlidingWindow(RateLimit):
    """
    Maintain a log list that captures timestamps for all successful API calls
    When a new API call is made, the first step is to remove all log entries older than 60 seconds.
    Once this cleanup is completed, we check the length of the log list. 
    If it exceeds or equals our limit (e.g., 60 API calls per minute), we raise an exception; 
    otherwise, we add the current timestamp to the logs.
    """
    def __init__(self):
        super().__init__()
        # Maintain a log list that captures timestamps for all successful API calls
        self.logs = []
        self.limit_per_interval = 60
        self.interval = 60

    
    def allow_request(self,ip):
        while self.lock:
            curr = datetime.now()
            while len(self.logs)>0 and (curr-self.logs[0]).total_seconds()>self.interval:
                self.logs.pop(0)

            if len(self.logs)>=self.limit_per_interval:
                raise RateLimitExceeded()
                return
            
            self.logs.append(curr)
            return True