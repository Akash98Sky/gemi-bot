from typing import Literal
from pydantic import Field, BaseModel
from google.genai.types import FunctionCall, Schema, FunctionDeclaration


class DuckduckgoSearchParams(BaseModel):
    query: str = Field(default='')
    max_results: int = Field(default=1)

class DuckduckgoSearchResults(BaseModel):
    query: str
    results: list[dict[str, str]]
    answers: list[dict[str, str]]

class DuckduckgoSearchFunctionCall(FunctionCall):
    name: str = "search"
    args: DuckduckgoSearchParams = Field(default=DuckduckgoSearchParams())

class DuckduckgoSearchFunctionDeclaration(FunctionDeclaration):
    name: str = "search"
    description: str = "A function to search the internet"
    parameters: Schema = Schema(
        type="OBJECT",
        properties={
            "query": Schema(
                type="STRING",
                description="A search query",
            ),
            "max_results": Schema(
                type="INTEGER",
                description="Number of results to return",
            )
        },
        required=["query"],
    )


class TavilySearchParams(BaseModel):
    query: str = Field(default='')
    max_results: int = Field(default=1)
    topic: Literal['general', 'news'] = Field(default='general')

class TavilyResultItem(BaseModel):
    title: str
    url: str
    content: str
    score: float

class TavilySearchResults(BaseModel):
    query: str
    answer: str
    results: list[TavilyResultItem]

class TavilySearchFunctionCall(FunctionCall):
    name: str = "realtime_search"
    args: TavilySearchParams = Field(default=TavilySearchParams())

class TavilySearchFunctionDeclaration(FunctionDeclaration):
    name: str = "realtime_search"
    description: str = "A function to search APIs such as Google, Serp and Bing and retrieve search results based on search query"
    parameters: Schema = Schema(
        type="OBJECT",
        properties={
            "query": Schema(
                type="STRING",
                description="A search query",
            ),
            "max_results": Schema(
                type="INTEGER",
                description="Number of results to return, should be in between 1-10",
                minimum=1,
                maximum=10
            ),
            "topic": Schema(
                type="STRING",
                description="Topic of the search query, news for news search and general for any other search.",
                enum=["general", "news"]
            )
        },
        required=["query"],
    )