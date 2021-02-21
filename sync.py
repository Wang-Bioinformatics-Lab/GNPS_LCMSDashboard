import json

def _sychronize_save_state(session_id, parameter_dict, redis_client, synchronization_token=None):
    session_dict = _sychronize_load_state(session_id, redis_client)

    db_token = session_dict.get("synchronization_token", None)

    if db_token is not None:
        if db_token != synchronization_token:
            return
        
        # tokens are equal, so lets make sure to keep saving it
        parameter_dict["synchronization_token"] = synchronization_token

    try:
        redis_client.set(session_id, json.dumps(parameter_dict))
    except:
        pass
    
def _sychronize_load_state(session_id, redis_client):
    session_state = {}

    try:
        session_state = json.loads(redis_client.get(session_id))
    except:
        pass

    return session_state