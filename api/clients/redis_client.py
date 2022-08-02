import os

import redis

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_client = redis.Redis(decode_responses=True, host=redis_host, port=redis_port)
