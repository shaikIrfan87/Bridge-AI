"""
Quiz Generation Service
Handles the creation of adaptive, industry-quality quizzes based on full candidate profile.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import QUIZ_GENERATION_PROMPT, QUIZ_EVALUATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.quiz import Quiz, QuizEvaluation, QuizSubmission

logger = logging.getLogger(__name__)


class QuizGenerator:
    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        """Surgically extract and repair JSON from AI responses."""
        if not response_text: return "{}"
        
        # 1. Strip Markdown blocks
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()
        
        # 2. Find balanced JSON bounds
        first_obj = cleaned.find("{")
        first_arr = cleaned.find("[")
        
        # Use whichever comes first
        start_idx = -1
        if first_obj != -1 and (first_arr == -1 or first_obj < first_arr):
            start_idx = first_obj
            end_char = "}"
        elif first_arr != -1:
            start_idx = first_arr
            end_char = "]"
            
        if start_idx != -1:
            end_idx = cleaned.rfind(end_char)
            if end_idx > start_idx:
                return cleaned[start_idx:end_idx+1].strip()
        
        return cleaned

    @staticmethod
    def _format_work_experience(profile: CandidateProfile) -> str:
        """Format work experience into a concise string for the prompt."""
        if not profile.work_experience:
            return "Not specified"
        parts = []
        for job in profile.work_experience[:4]:
            line = f"  - {job.job_title or 'Unknown Role'} at {job.company or 'Unknown Company'}"
            if job.duration:
                line += f" ({job.duration})"
            if job.responsibilities:
                line += f": {'; '.join(job.responsibilities[:3])}"
            parts.append(line)
        return "\n".join(parts)

    @staticmethod
    def _format_projects(profile: CandidateProfile) -> str:
        """Format projects into a concise string for the prompt."""
        if not profile.projects:
            return "Not specified"
        parts = []
        for proj in profile.projects[:3]:
            line = f"  - {proj.name or 'Unknown Project'}"
            if proj.description:
                line += f": {proj.description}"
            if proj.technologies:
                line += f" (Tech: {', '.join(proj.technologies)})"
            parts.append(line)
        return "\n".join(parts)

    @staticmethod
    async def generate_quiz(profile: CandidateProfile, count: int = 15) -> Optional[Quiz]:
        """
        Generate a highly personalized quiz based on the candidate's full profile.
        Uses work experience and projects to create industry-relevant questions.
        """
        tech_skills_str = ", ".join(profile.technical_skills[:12]) or "Not specified"
        soft_skills_str = ", ".join(profile.soft_skills[:6]) or "Not specified"
        work_exp_str = QuizGenerator._format_work_experience(profile)
        projects_str = QuizGenerator._format_projects(profile)

        # Estimated time: ~2.5 minutes per question
        estimated_minutes = max(20, count * 3)

        prompt = QUIZ_GENERATION_PROMPT.format(
            full_name=profile.full_name or "Candidate",
            summary=profile.summary or "Not provided",
            experience_level=profile.experience_level,
            years_of_experience=profile.years_of_experience or "Not specified",
            technical_skills=tech_skills_str,
            soft_skills=soft_skills_str,
            work_experience=work_exp_str,
            projects=projects_str,
            education=profile.education or "Not specified",
            certifications=", ".join(profile.certifications) if profile.certifications else "None",
            count=15,
            estimated_minutes=25
        )

        try:
            response_text = await asyncio.wait_for(
                GeminiClient.generate_content(prompt, model_name="gemini-2.0-flash", timeout_seconds=60),
                timeout=75  # Outer timeout gives 15s grace over inner
            )

            if not response_text:
                raise ValueError("Empty response from AI")

            if response_text.startswith("AI Error:") or response_text.startswith("Error:"):
                raise ValueError(response_text)

            json_str = QuizGenerator._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure total_questions is accurate
            questions = data.get("questions", [])
            data["total_questions"] = len(questions)

            if not questions:
                raise ValueError("AI returned no questions")

            quiz = Quiz(**data)
            return quiz

        except asyncio.TimeoutError:
            logger.warning(f"Quiz generation timed out after 50 seconds")
            # Generate a mock quiz with fallback questions
            return await QuizGenerator._generate_mock_quiz(profile, count=15)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Quiz JSON: {e}")
            # Return mock quiz on parse error
            return await QuizGenerator._generate_mock_quiz(profile, count=15)
        except Exception as e:
            logger.error(f"Quiz generation error: {type(e).__name__}: {e}", exc_info=True)
            # Generate mock quiz as fallback
            return await QuizGenerator._generate_mock_quiz(profile, count=15)

    @staticmethod
    async def _generate_mock_quiz(profile: CandidateProfile, count: int = 15) -> Quiz:
        """Generate intelligent resume-based fallback questions when AI is unavailable."""
        from app.models.quiz import Question
        
        mock_questions = []
        
        # Question 1: Work Experience Based
        if profile.work_experience and len(profile.work_experience) > 0:
            job = profile.work_experience[0]
            company = job.company or "your previous company"
            role = job.job_title or "your role"
            text = f"Tell me about your experience as {role} at {company}. What was your main responsibility and what technical challenge did you face?"
            mock_questions.append(Question(
                id=1, text=text, question_type="Behavioral",
                topic="Work Experience", difficulty="Medium",
                keywords=["Responsibility", "Challenge", "Solution", "Impact"],
                correct_answer_guide="Should describe specific role responsibilities, technical problem encountered, how it was solved, and business/technical impact."
            ))
        else:
            mock_questions.append(Question(
                id=1, text="Tell me about your professional background and main technical expertise.",
                question_type="Behavioral", topic="Background", difficulty="Easy",
                keywords=["Experience", "Skills", "Projects"],
                correct_answer_guide="Should provide overview of career, key skills developed, and notable contributions."
            ))
        
        # Question 2: Technical Skills Based
        if profile.technical_skills and len(profile.technical_skills) > 0:
            skill = profile.technical_skills[0]
            text = f"You mentioned {skill} as a key skill. Tell me about the most complex problem you solved using {skill}. What was the problem, your approach, and the outcome?"
            mock_questions.append(Question(
                id=2, text=text, question_type="Technical-Specific",
                topic="Technical Expertise", difficulty="Medium",
                keywords=["Complex Problem", "Approach", "Solution", "Trade-offs"],
                correct_answer_guide="Should describe specific problem, why {0} was the right choice, trade-offs considered, technical implementation details, and measurable outcome.".format(skill)
            ))
        else:
            mock_questions.append(Question(
                id=2, text="Describe a complex technical project you worked on. What technical challenges did you face and how did you overcome them?",
                question_type="Technical-Specific", topic="Problem-Solving", difficulty="Medium",
                keywords=["Challenge", "Solution", "Debugging", "Optimization"],
                correct_answer_guide="Should explain technical complexity, debugging/solving approach, technologies used, and learning from experience."
            ))
        
        # Question 3: Projects Based
        if profile.projects and len(profile.projects) > 0:
            project = profile.projects[0]
            proj_name = project.name or "your project"
            text = f"Walk me through the project '{proj_name}'. What was your role, what technical decisions did you make, and what would you do differently now?"
            mock_questions.append(Question(
                id=3, text=text, question_type="Decision-Based",
                topic="Project Architecture", difficulty="Hard",
                keywords=["Role", "Decision-Making", "Trade-offs", "Lessons Learned"],
                correct_answer_guide="Should explain project goals, personal role/ownership, key architectural decisions with rationale, and how experience would change future approaches."
            ))
        else:
            mock_questions.append(Question(
                id=3, text="Describe a significant project you designed or architected. What were the key design decisions and why did you make them?",
                question_type="Decision-Based", topic="Design", difficulty="Hard",
                keywords=["Architecture", "Design", "Scalability", "Maintenance"],
                correct_answer_guide="Should explain system design, trade-offs between different approaches, scalability considerations, and long-term maintainability."
            ))
        
        # Question 4: Experience Level Based
        if profile.experience_level in ["Senior", "Expert"]:
            text = "Tell me about a time you led a technical initiative or mentored junior developers. How did you approach it and what was the impact?"
            mock_questions.append(Question(
                id=4, text=text, question_type="Behavioral",
                topic="Leadership", difficulty="Hard",
                keywords=["Leadership", "Mentoring", "Initiative", "Impact"],
                correct_answer_guide="Should demonstrate leadership qualities, mentoring ability, initiative ownership, and measurable positive outcomes."
            ))
        else:
            text = "What's an area of technical expertise you want to develop further? How do you approach learning new technologies?"
            mock_questions.append(Question(
                id=4, text=text, question_type="Growth-Oriented",
                topic="Learning", difficulty="Easy",
                keywords=["Growth", "Learning", "Initiative", "Self-improvement"],
                correct_answer_guide="Should show growth mindset, specific learning strategies (online courses, projects, documentation), and commitment to skill development."
            ))
        
        # Question 5: Soft Skills
        mock_questions.append(Question(
            id=5, text="Describe a time you had to work with difficult stakeholders or resolve a technical disagreement in your team.",
            question_type="Behavioral", topic="Collaboration", difficulty="Medium",
            keywords=["Communication", "Conflict Resolution", "Teamwork", "Compromise"],
            correct_answer_guide="Should demonstrate communication skills, ability to understand different perspectives, collaborative problem-solving, and maintaining professional relationships."
        ))
        
        # Questions 6-15: Skill-specific intelligent questions
        skill_questions = [
            ("Performance", "How do you approach performance optimization? Tell me about a performance issue you debugged and optimized.", "Technical-Specific", ["Profiling", "Optimization", "Measurement", "Trade-offs"]),
            ("Testing", "What's your approach to testing and code quality? Describe your experience with unit/integration testing.", "Technical-Specific", ["Testing Strategy", "Code Quality", "Coverage", "Debugging"]),
            ("Database", "Tell me about your database design experience. How do you handle scaling and optimization?", "Technical-Specific", ["Data Modeling", "Indexing", "Scalability", "Query Optimization"]),
            ("API Design", "Describe your experience designing or building APIs. What principles do you follow?", "Technical-Specific", ["RESTful", "Versioning", "Documentation", "Error Handling"]),
            ("DevOps", "Tell me about your experience with deployment, CI/CD, and infrastructure. What tools have you used?", "Technical-Specific", ["Automation", "Deployment", "Monitoring", "Infrastructure"]),
            ("Security", "How do you approach security in your projects? Describe a security issue you've encountered.", "Technical-Specific", ["Security Best Practices", "Vulnerability", "Prevention", "Compliance"]),
            ("Agile", "What's your experience with Agile/Scrum? How do you handle sprint planning and code reviews?", "Behavioral", ["Agile", "Communication", "Collaboration", "Process"]),
            ("System Design", "If you had to design a system for [specific problem from resume], how would you approach it?", "Decision-Based", ["Architecture", "Scalability", "Trade-offs", "Components"]),
            ("Code Review", "Tell me about your approach to code reviews. How do you provide feedback and improve code quality?", "Behavioral", ["Code Quality", "Feedback", "Mentoring", "Standards"]),
        ]
        
        # Add unique skill-based questions
        for i, (skill_name, question_text, q_type, keywords) in enumerate(skill_questions[:count - 5], start=6):
            mock_questions.append(Question(
                id=i,
                text=question_text,
                question_type=q_type,
                topic=skill_name,
                difficulty="Medium" if i < 10 else "Hard",
                keywords=keywords,
                correct_answer_guide=f"Should demonstrate practical experience with {skill_name}, problem-solving ability, and understanding of best practices."
            ))
        
        return Quiz(
            title=f"Technical Interview - {profile.full_name or 'Candidate'}",
            total_questions=len(mock_questions),
            estimated_time_minutes=25,
            questions=mock_questions[:count]
        )

    @staticmethod
    async def evaluate_quiz_answers(
        quiz: Quiz,
        answers: dict,  # { question_id_str -> answer_text }
        experience_level: str = "Mid-Level"
    ) -> QuizEvaluation:
        """
        Use AI to score the candidate's open-ended quiz answers.
        Returns a detailed evaluation with per-question scores and feedback.
        ALWAYS returns a valid QuizEvaluation (never None).
        """
        from app.models.quiz import QuizAnswerScore
        
        qa_pairs = []
        for q in quiz.questions:
            qid = str(q.id)
            answer = answers.get(qid, "").strip() or "(No answer provided)"
            qa_pairs.append({
                "question_id": q.id,
                "question": q.text,
                "question_type": q.question_type,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "keywords": q.keywords,
                "correct_answer_guide": q.correct_answer_guide,
                "candidate_answer": answer
            })

        prompt = QUIZ_EVALUATION_PROMPT.format(
            qa_pairs=json.dumps(qa_pairs, indent=2),
            experience_level=experience_level
        )

        try:
            response_text = await asyncio.wait_for(
                GeminiClient.generate_content(prompt, model_name="gemini-2.0-flash", timeout_seconds=60),
                timeout=75  # Outer timeout gives 15s grace over inner
            )

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError("AI evaluation failed")

            json_str = QuizGenerator._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure all answer objects have required fields
            if 'answers' in data and isinstance(data['answers'], list):
                for ans in data['answers']:
                    ans.setdefault('matched_keywords', [])
                    ans.setdefault('missing_keywords', [])
                    ans.setdefault('feedback', 'Good answer.')
                    ans.setdefault('score', 50)
            
            data.setdefault('answers', [])
            data.setdefault('total_score', 50)
            data.setdefault('strengths', [])
            data.setdefault('weaknesses', [])
            data.setdefault('overall_feedback', 'Your answers have been recorded.')
            
            evaluation = QuizEvaluation(**data)
            return evaluation

        except asyncio.TimeoutError:
            logger.error("Quiz evaluation timed out")
            # Return fallback evaluation with basic feedback
            fallback_answers = []
            total_score = 0
            for q in quiz.questions:
                qid = str(q.id)
                user_answer = answers.get(qid, "(No answer provided)")
                score = 50 if user_answer and user_answer.strip() else 20
                fallback_answers.append(QuizAnswerScore(
                    question_id=q.id,
                    score=score,
                    matched_keywords=q.keywords[:2] if q.keywords else [],
                    missing_keywords=q.keywords[2:] if len(q.keywords) > 2 else [],
                    feedback="Your answer was recorded. Full evaluation is pending due to system load."
                ))
                total_score += score
            
            return QuizEvaluation(
                total_score=total_score // len(quiz.questions) if quiz.questions else 50,
                answers=fallback_answers,
                strengths=["Completed all questions"],
                weaknesses=["Detailed feedback pending"],
                overall_feedback="Evaluation could not be completed due to system load. Please review your answers above."
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Quiz Evaluation JSON: {e}")
            # Return basic evaluation
            fallback_answers = []
            total_score = 0
            for q in quiz.questions:
                qid = str(q.id)
                user_answer = answers.get(qid, "(No answer provided)")
                score = 50 if user_answer and user_answer.strip() else 20
                fallback_answers.append(QuizAnswerScore(
                    question_id=q.id,
                    score=score,
                    matched_keywords=[],
                    missing_keywords=q.keywords or [],
                    feedback="Your answer was recorded."
                ))
                total_score += score
            
            return QuizEvaluation(
                total_score=total_score // len(quiz.questions) if quiz.questions else 50,
                answers=fallback_answers,
                strengths=["Submitted answers"],
                weaknesses=[],
                overall_feedback="Your answers have been recorded for evaluation."
            )
        except Exception as e:
            logger.error(f"Quiz evaluation failed: {e}")
            # Return basic evaluation
            fallback_answers = []
            total_score = 0
            for q in quiz.questions:
                qid = str(q.id)
                user_answer = answers.get(qid, "(No answer provided)")
                score = 50 if user_answer and user_answer.strip() else 20
                fallback_answers.append(QuizAnswerScore(
                    question_id=q.id,
                    score=score,
                    matched_keywords=[],
                    missing_keywords=q.keywords or [],
                    feedback=f"Your answer was recorded. ({str(e)[:50]})"
                ))
                total_score += score
            
            return QuizEvaluation(
                total_score=total_score // len(quiz.questions) if quiz.questions else 50,
                answers=fallback_answers,
                strengths=["Completed quiz"],
                weaknesses=[],
                overall_feedback="Your answers have been recorded. Full evaluation is being processed."
            )

    @staticmethod
    async def generate_for_session(file_path: str, force_regenerate: bool = False) -> Optional[Quiz]:
        """
        Orchestrate quiz generation for a file session.
        Default question count set to 15 for focused assessment.
        """
        quiz_path = f"{file_path}.quiz.json"
        
        # Check cache
        if not force_regenerate and os.path.exists(quiz_path):
            try:
                with open(quiz_path, "r", encoding="utf-8") as f:
                    quiz_data = json.load(f)
                    return Quiz(**quiz_data)
            except Exception:
                pass

        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                profile = CandidateProfile(**profile_data)
        except Exception:
            return None

        # Request 15 questions for focused assessment
        quiz = await QuizGenerator.generate_quiz(profile, count=15)

        if quiz:
            # Save to cache
            try:
                with open(quiz_path, "w", encoding="utf-8") as f:
                    f.write(quiz.model_dump_json(indent=2))
                logger.info(f"Quiz saved to {quiz_path}")
            except Exception as e:
                logger.error(f"Failed to save quiz: {e}")

        return quiz
