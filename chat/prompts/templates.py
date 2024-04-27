from common.constants.keywords import MESSAGE_METADATA, SEARCH_RESPONSES

def build_searchengine_response_prompt(responses: list[dict[str, str]]):
    res = f"{SEARCH_RESPONSES}:\n"
    for response in responses:
        res += f"- query: {response['query']}\n"
        res += f"  title: {response['title']}\n"
        res += f"  body: {response['body']}\n"
        res += f"  url: {response['href']}\n"
    return res

def build_msg_metadata_prompt(meta: dict[str, str]):
    res = f"\n{MESSAGE_METADATA}:\n"
    for key in meta:
        res += f"  {key}: {meta[key]}\n"
    return res
