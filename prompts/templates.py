def build_searchengine_response_prompt(responses: list[dict[str, str]]):
    res = "search_responses:\n"
    for response in responses:
        res += f"- Query: {response['query']}\n"
        res += f"  Title: {response['title']}\n"
        res += f"  Body: {response['body']}\n"
    return res

def build_msg_metadata_prompt(meta: dict[str, str]):
    res = "message_metadata:\n"
    for key in meta:
        res += f"  {key}: {meta[key]}\n"
    return res + "\n"