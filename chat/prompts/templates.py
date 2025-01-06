from common.constants.keywords import MESSAGE_METADATA, SEARCH_RESPONSES

def build_msg_metadata_prompt(meta: dict[str, str]):
    res = f"\n{MESSAGE_METADATA}:\n"
    for key in meta:
        res += f"  {key}: {meta[key]}\n"
    return res
