import json
import dash

GLOBAL_STATE = {}

def _save_session_parameter(session, parameter, value):
    GLOBAL_STATE[parameter] = value
    #print("SAVING HERE", parameter, value, GLOBAL_STATE)
    return

def _get_current_session_state(session):
    try:
        if len(session) > 2:
            return GLOBAL_STATE
        return {}
    except:
        return {}
    return GLOBAL_STATE

def _determine_new_param_value(settings_state, parameter, current_value, url_value):
    merged_value = settings_state.get(parameter, url_value)
    if current_value == merged_value:
        merged_value = dash.no_update

    return merged_value