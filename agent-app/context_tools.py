import difflib

def fuzzy_match(word, candidates):
    matches = difflib.get_close_matches(word, candidates, n=1, cutoff=0.8)
    return matches[0] if matches else None

def update_user_context(prompt, supported_species, supported_value_types, session_state):
    lower_prompt = prompt.lower()

    # 检测 species
    for s in supported_species:
        if s in lower_prompt:
            session_state["user_settings"]["species"] = s
            break

    # 检测 value_type
    for v in supported_value_types:
        if v in lower_prompt:
            session_state["user_settings"]["value_type"] = v
            break