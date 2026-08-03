"""
Skill Analysis Models
Pydantic models for structured skill extraction.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class WorkExperience(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    full_name: Optional[str] = "Candidate"
    email: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list, description="List of technical hard skills")
    soft_skills: List[str] = Field(default_factory=list, description="List of soft/interpersonal skills")
    experience_level: str = Field(description="Junior, Mid-Level, Senior, or Expert")
    years_of_experience: Optional[str] = Field(default=None, description="Estimated years of experience")
    summary: str = Field(description="Brief professional summary of the candidate")
    work_experience: List[WorkExperience] = Field(
        default_factory=list,
        description="List of work experiences extracted from resume"
    )
    projects: List[Project] = Field(
        default_factory=list,
        description="List of notable projects"
    )
    education: Optional[str] = Field(default=None, description="Highest education qualification")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")


class AnalysisResponse(BaseModel):
    success: bool
    profile: CandidateProfile
    session_id: str
    message: str
