def build_searchengine_response_prompt(responses: list[dict[str, str]]):
    res = "search_responses:\n"
    for response in responses:
        res += f"- Query: {response['query']}\n"
        res += f"  Title: {response['title']}\n"
        res += f"  Body: {response['body']}\n"
    return res