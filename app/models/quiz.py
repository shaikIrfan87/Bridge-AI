"""
Quiz Models
Pydantic models for the Quiz engine.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class Question(BaseModel):
    id: int
    text: str
    correct_answer_guide: str = Field(
        description="A detailed guide with key points that an ideal answer should contain"
    )
    topic: str = Field(description="The specific skill/topic this question tests")
    difficulty: str = Field(description="Easy, Medium, Hard")
    question_type: str = Field(
        default="Technical",
        description="Technical, Behavioral, Scenario, System Design"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Important keywords/concepts the answer should cover"
    )


class QuizAnswerScore(BaseModel):
    question_id: int
    score: int = Field(description="Score 0-100 for this answer")
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    feedback: str = Field(description="Specific feedback on this answer")


class DetailedQuizAnswer(BaseModel):
    question_id: int
    question_text: str = Field(description="The question asked")
    user_answer: str = Field(description="What the candidate answered")
    score: int = Field(description="Score 0-100 for this answer")
    correct_answer_guide: str = Field(description="How the question should be answered")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords found in user's answer")
    missing_keywords: List[str] = Field(default_factory=list, description="Keywords missing from user's answer")
    feedback: str = Field(description="Detailed feedback and suggestions for improvement")
    topic: str = Field(description="The skill/topic being tested")
    difficulty: str = Field(description="Easy, Medium, Hard")


class QuizEvaluation(BaseModel):
    total_score: int = Field(description="Overall quiz score 0-100")
    answers: List[QuizAnswerScore] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    overall_feedback: str = Field(description="Summary feedback on the quiz performance")


class Quiz(BaseModel):
    title: str = "Skill Assessment"
    questions: List[Question]
    total_questions: int
    estimated_time_minutes: int

    @field_validator("total_questions", mode="before")
    @classmethod
    def sync_total_questions(cls, v, info):
        # If questions are available, use their count
        if hasattr(info, "data") and "questions" in info.data:
            return len(info.data["questions"])
        return v


class QuizSubmission(BaseModel):
    quiz_id: str
    answers: dict  # { question_id (str) -> answer_text }


class QuizResponse(BaseModel):
    success: bool
    quiz_id: str
    quiz: Quiz
    message: str


class QuizEvaluationResponse(BaseModel):
    success: bool
    evaluation: Optional[QuizEvaluation] = None
    message: str
