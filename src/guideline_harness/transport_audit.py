"""Conservative read-only audit of partial CLI streams before timeout recovery."""
import json

def audit_timeout_stream(text):
    try:
        events=[json.loads(line) for line in text.splitlines() if line.strip()]
    except ValueError:
        return {'resumable':False,'reason':'invalid_json'}
    allowed={'thread.started','turn.started','item.started','item.updated','item.completed'}
    for event in events:
        if not isinstance(event,dict) or event.get('type') not in allowed:
            return {'resumable':False,'reason':'unknown_or_terminal_event'}
        item=event.get('item',{})
        if not isinstance(item,dict) or item.get('type') not in (None,'agent_message','reasoning','error'):
            return {'resumable':False,'reason':'native_or_unknown_item'}
        if item.get('type')=='agent_message':
            try:
                action=json.loads(item.get('text',''))
                arguments=json.loads(action['arguments_json'])
                if action['action'] not in {'list_materials','read_material','search_materials','read_example','read_examples','search_examples','write_asset','run_program'} or not isinstance(arguments,dict):
                    return {'resumable':False,'reason':'final_or_unknown_message'}
            except (ValueError,KeyError,TypeError):
                return {'resumable':False,'reason':'unclassified_agent_message'}
        if item.get('type')=='error' and not item.get('message','').startswith('Code Mode is unavailable because code-mode host is disabled.'):
            return {'resumable':False,'reason':'unclassified_error'}
    if not any(e.get('type')=='turn.started' for e in events):
        return {'resumable':False,'reason':'no_started_turn'}
    return {'resumable':True,'reason':'incomplete_turn_without_native_tools_or_terminal_event','events':len(events)}
