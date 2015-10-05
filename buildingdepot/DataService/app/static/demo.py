import redis

r = redis.Redis()
print r.get(1)