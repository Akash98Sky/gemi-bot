from typing import Literal
from google.genai.types import Tool, FunctionDeclaration, Schema, FunctionCall
from pydantic import BaseModel, Field


class GenerateImageParams(BaseModel):
    prompt: str = Field(default="")
    image_name: str = Field(default="")
    quality: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM")

class GenerateImageFunctionCall(FunctionCall):
    name: str = "generate_image"
    args: GenerateImageParams = Field(default=GenerateImageParams())

class GenerateImageFunctionDeclaration(FunctionDeclaration):
    name: str = "generate_image"
    description: str = "Generate image from the given prompt parameter"
    parameters: Schema = Schema(
        type="OBJECT",
        properties={
            "prompt": Schema(
                type="STRING",
                description="A detailed prompt to generate the image",
            ),
            "image_name": Schema(
                type="STRING",
                description="A short file name for the image",
            ),
            "quality": Schema(
                type="STRING",
                description="Image quality",
                enum=["LOW", "MEDIUM", "HIGH"],
            )
        },
        required=["prompt", "image_name"],
    )

class GenerateVoiceParams(BaseModel):
    text: str = Field(default="")
    quality: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM")

class GenerateVoiceFunctionCall(FunctionCall):
    name: str = "generate_voice"
    args: GenerateVoiceParams = Field(default=GenerateVoiceParams())

class GenerateVoiceFunctionDeclaration(FunctionDeclaration):
    name: str = "generate_voice"
    description: str = "Generates audio format of the given text parameter"
    parameters: Schema = Schema(
        type="OBJECT",
        properties={
            "text": Schema(
                type="STRING",
                description="The entire text to be convert to audio format",
            ),
            "quality": Schema(
                type="STRING",
                description="Audio quality",
                enum=["LOW", "MEDIUM", "HIGH"],
            )
        },
        required=["text"],
    )
