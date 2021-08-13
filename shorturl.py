import json
import uuid

def shorten_url(url, redis_client):
    short_url_uuid = str(uuid.uuid4()).replace("-", "")
    
    try:
        redis_client.set(short_url_uuid, url, ex=3600)
    except:
        return None
    
    return short_url_uuid

def get_shorturl(short_url, redis_client):
    try:
        return redis_client.get(short_url)
    except:
        return None

    