from prompts.keywords import IMAGE_RESPONSES, MESSAGE_METADATA, SEARCH_RESPONSES

def build_searchengine_response_prompt(responses: list[dict[str, str]]):
    res = f"{SEARCH_RESPONSES}:\n"
    for response in responses:
        res += f"- Query: {response['query']}\n"
        res += f"  Title: {response['title']}\n"
        res += f"  Body: {response['body']}\n"
        res += f"  URL: {response['href']}\n"
    return res

def build_msg_metadata_prompt(meta: dict[str, str]):
    res = f"\n{MESSAGE_METADATA}:\n"
    for key in meta:
        res += f"  {key}: {meta[key]}\n"
    return res

def build_image_responses(responses: list[str]):
    res = f"{IMAGE_RESPONSES}:\n"
    for response in responses:
        res += f"- {response}\n"
    return res