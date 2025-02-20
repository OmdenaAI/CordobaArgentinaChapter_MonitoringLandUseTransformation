from limiting_algorithms import FixedCounterWindow, TokenBucket, SlidingWindow

""""
get_instance method accepts an algorithm as input and 
provides the corresponding object associated with it as its output. 
This allows us to select from different rate-limiting algorithms 
We can dynamically generate an instance of the object using this Factory Class.
"""
class RateLimitFactory:
   @staticmethod
   def get_instance(algorithm:str = None):
    if algorithm== "TokenBucket":
        return TokenBucket()
    
    elif algorithm== "FixedCounterWindow":
        return FixedCounterWindow()

    else:
        return SlidingWindow()