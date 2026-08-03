"""
Coding Challenge Models
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Any
import json


class TestCase(BaseModel):
    input: str
    expected_output: str
    description: Optional[str] = None
    is_hidden: bool = Field(default=False, description="Hidden test cases not shown to candidate")

    @field_validator("input", "expected_output", mode="before")
    @classmethod
    def _stringify_fields(cls, value: Any) -> str:
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value)
        except Exception:
            return str(value)


class SupportedLanguage(BaseModel):
    name: str  # "Python 3", "JavaScript", "Java", "C++"
    slug: str  # "python", "javascript", "java", "cpp"
    starter_code: str  # Language-specific function signature


class CodingChallenge(BaseModel):
    title: str = Field(description="Title of the challenge")
    difficulty: str = Field(description="Easy, Medium, Hard")
    problem_statement: str = Field(description="Markdown description of the problem")
    function_signature: str = Field(description="Python starting code template (default language)")
    input_format: str
    output_format: str
    constraints: List[str]
    test_cases: List[TestCase]
    starter_code_by_language: dict = Field(
        default_factory=dict,
        description="Starter code keyed by language slug: python, javascript, java, cpp"
    )
    solution_code_by_language: dict = Field(
        default_factory=dict,
        description="Solution code for each language: python, javascript, java, cpp"
    )
    hints: List[str] = Field(
        default_factory=list,
        description="Optional hints revealed progressively"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Topic tags e.g. arrays, dp, graphs"
    )


class CodingChallenges(BaseModel):
    """Container for multiple coding challenges (typically 3: Easy, Medium, Hard)"""
    challenges: List[CodingChallenge] = Field(
        description="Array of 3 coding challenges (Easy, Medium, Hard)"
    )


class CodeSubmission(BaseModel):
    code: str
    language: str = "python"
    challenge_id: Optional[str] = None
    challenge_index: int = 0
    skipped: bool = False  # True if user skipped without attempting


class TestCaseResult(BaseModel):
    test_case_index: int
    passed: bool
    input: str = ""
    expected_output: str = ""
    actual_output: str = ""
    explanation: str = ""


class EvaluationResult(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=None,
        # Use serialization_alias for sending test_results as test_cases in response
    )
    
    success: bool
    score: int = Field(default=0, description="0-100 score")
    attempted: bool = Field(default=True, description="True if user attempted, False if skipped")
    passed_test_cases: int = 0
    total_test_cases: int = 0
    test_results: List[TestCaseResult] = Field(
        default_factory=list,
        description="Per-test-case breakdown",
        serialization_alias="test_cases"  # Send as test_cases in JSON response
    )
    feedback: str = Field(default="", description="Detailed feedback on logic and style")
    time_complexity: str = Field(default="O(n)", description="Estimated complexity (e.g., O(n))")
    space_complexity: str = Field(default="O(n)", description="Estimated space complexity")
    code_quality: str = Field(default="Good", description="Assessment of code quality")
    suggestions: List[str] = Field(default_factory=list, description="Tips for improvement")
    bugs_found: List[str] = Field(
        default_factory=list,
        description="Specific bugs or issues found in the code"
    )


class CodingResponse(BaseModel):
    success: bool
    challenge_id: str
    challenges: List[CodingChallenge] = Field(description="Array of 3 coding challenges")
    message: str
