"""
Report Generation Service
Aggregates all assessment data to produce a final hiring recommendation.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import REPORT_GENERATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.report import FinalReport

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def _generate_mock_report(candidate_name: str, quiz_score: int, coding_score: Optional[int], detailed_quiz_answers: Optional[list] = None) -> FinalReport:
        """Generate a mock/fallback report when AI is unavailable."""
        from app.models.report import SkillGap, Recommendation
        
        overall_score = quiz_score
        if coding_score is not None:
            overall_score = (quiz_score + coding_score) // 2
        
        if overall_score >= 80:
            rating = "Advanced"
            verdict = "Recommend Immediate Interview"
            summary = f"{candidate_name} demonstrated strong technical skills with an overall score of {overall_score}/100."
        elif overall_score >= 60:
            rating = "Proficient"
            verdict = "Recommend For Interview"
            summary = f"{candidate_name} showed competent technical skills with an overall score of {overall_score}/100."
        elif overall_score >= 40:
            rating = "Competent"
            verdict = "Consider For Training"
            summary = f"{candidate_name} has foundational skills but needs development. Score: {overall_score}/100."
        else:
            rating = "Novice"
            verdict = "Not Recommended"
            summary = f"{candidate_name} did not meet minimum technical requirements. Score: {overall_score}/100."
        
        skill_gaps = [
            SkillGap(
                skill="Advanced Data Structures",
                status="Partially Verified",
                gap_analysis="Demonstrated basic understanding but needs improvement in complex scenarios."
            ),
            SkillGap(
                skill="Performance Optimization",
                status="Partially Verified",
                gap_analysis="Shows awareness but lacks depth in optimization techniques."
            ),
            SkillGap(
                skill="System Design",
                status="Not Tested",
                gap_analysis="Not covered in this assessment round. Recommend architectural interview."
            )
        ]
        
        return FinalReport(
            candidate_name=candidate_name,
            overall_score=overall_score,
            technical_rating=rating,
            credibility_status="Authentic",
            quiz_score=quiz_score,
            coding_score=coding_score,
            skill_gaps=skill_gaps,
            detailed_quiz_answers=detailed_quiz_answers or [],
            recommendation=Recommendation(
                verdict=verdict,
                summary=summary,
                pros=["Completed all assessments", "Demonstrated problem-solving ability"],
                cons=["Needs improvement in advanced concepts"] if overall_score < 70 else [],
                learning_path=["Master advanced data structures", "Learn algorithm optimization", "Practice system design"]
            )
        )

    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        if not response_text:
            return "{}"
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        if cleaned.startswith("{"):
            return cleaned

        # Find balanced JSON object
        first = cleaned.find("{")
        if first != -1:
            depth = 0
            for i, ch in enumerate(cleaned[first:], start=first):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return cleaned[first:i + 1].strip()
        return cleaned

    @staticmethod
    async def evaluate_and_generate_report(file_path: str, filename: str) -> Optional[FinalReport]:
        """
        Evaluate all rounds in bulk and generate the final report.
        """
        from app.services.quiz_generator import QuizGenerator
        from app.services.coding_engine import CodingEngine
        from app.models.quiz import Quiz
        from app.models.coding import CodingChallenge
        
        quiz_score = 0
        quiz_eval_json = None
        detailed_quiz_answers = []
        coding_score = 0
        coding_eval_json = None
        
        # 1. Evaluate Quiz if needed
        quiz_sub_path = f"{file_path}.quiz_submission.json"
        if os.path.exists(quiz_sub_path):
            quiz_path = f"{file_path}.quiz.json"
            if os.path.exists(quiz_path):
                with open(quiz_path, "r", encoding="utf-8") as f:
                    quiz = Quiz(**json.load(f))
                with open(quiz_sub_path, "r", encoding="utf-8") as f:
                    answers = json.load(f)
                eval_res = await QuizGenerator.evaluate_quiz_answers(quiz, answers)
                
                # evaluate_quiz_answers always returns a valid QuizEvaluation
                quiz_score = eval_res.total_score
                quiz_eval_json = eval_res.model_dump_json()
                
                # Build detailed quiz answers with questions and feedback
                for ans_eval in eval_res.answers:
                    q_id = ans_eval.question_id
                    question = next((q for q in quiz.questions if q.id == q_id), None)
                    if question:
                        user_answer = answers.get(str(q_id), "(No answer provided)")
                        detailed_quiz_answers.append({
                            "question_id": q_id,
                            "question_text": question.text,
                            "user_answer": user_answer,
                            "score": ans_eval.score,
                            "correct_answer_guide": question.correct_answer_guide,
                            "matched_keywords": ans_eval.matched_keywords,
                            "missing_keywords": ans_eval.missing_keywords,
                            "feedback": ans_eval.feedback,
                            "topic": question.topic,
                            "difficulty": question.difficulty
                        })

        # 2. Evaluate Coding if needed
        coding_sub_path = f"{file_path}.coding_submission.json"
        if os.path.exists(coding_sub_path):
            coding_path = f"{file_path}.coding.json"
            if os.path.exists(coding_path):
                with open(coding_path, "r", encoding="utf-8") as f:
                    challenges_data = json.load(f)
                    challenges = [CodingChallenge(**ch) for ch in challenges_data]
                with open(coding_sub_path, "r", encoding="utf-8") as f:
                    submissions = json.load(f)
                    
                all_evals = []
                total_score = 0
                count = 0
                
                for idx_str, sub in submissions.items():
                    idx = int(idx_str)
                    if idx < len(challenges):
                        # Use pre-calculated evaluation if available, otherwise evaluate
                        if 'evaluation' in sub and 'score' in sub['evaluation']:
                            # Score was already calculated and saved
                            score = sub['evaluation']['score']
                            feedback = sub['evaluation'].get('feedback', 'No feedback available')
                            all_evals.append({"index": idx, "score": score, "feedback": feedback, "skipped": sub.get('skipped', False)})
                            total_score += score
                            count += 1
                        else:
                            # Fall back to re-evaluating if scores not saved
                            skipped = sub.get('skipped', False)
                            res = await CodingEngine.evaluate_code(challenges[idx], sub['code'], sub['language'], skipped=skipped)
                            if res:
                                all_evals.append({"index": idx, "score": res.score, "feedback": res.feedback, "skipped": skipped})
                                total_score += res.score
                                count += 1
                
                if count > 0:
                    coding_score = total_score // count
                    coding_eval_json = json.dumps(all_evals)

        # 3. Handle Integrity Violation (Anti-Cheat)
        cheat_path = f"{file_path}.cheated"
        if os.path.exists(cheat_path):
            # Instant Rejection Report without AI Synthesis
            profile_path = f"{file_path}.json"
            name = "Candidate"
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f: name = json.load(f).get("full_name", "Candidate")
            
            return FinalReport(
                candidate_name=name,
                overall_score=0,
                technical_rating="Beginner",
                credibility_status="Flagged",
                skill_gaps=[],
                recommendation={
                    "verdict": "Rejected: Integrity Violation",
                    "summary": "This candidate attempted to cheat during the technical assessment by switching tabs or minimizing the browser window. The assessment was automatically terminated.",
                    "pros": [],
                    "cons": ["Attempted to use unauthorized external resources", "Failed proctoring checks"],
                    "learning_path": ["Practice ethical coding standards", "Focus on core competence building"]
                }
            )

        return await ReportGenerator.generate_final_report(
            file_path=file_path,
            quiz_score=quiz_score,
            coding_score=coding_score,
            coding_feedback=coding_eval_json,
            quiz_feedback=quiz_eval_json,
            detailed_quiz_answers=detailed_quiz_answers
        )

    @staticmethod
    async def generate_final_report(
        file_path: str,
        quiz_score: int,
        coding_score: Optional[int] = None,
        coding_feedback: Optional[str] = None,
        quiz_feedback: Optional[str] = None,
        detailed_quiz_answers: Optional[list] = None
    ) -> Optional[FinalReport]:
        # Quick path: try to load profile for candidate name
        candidate_name = "Candidate"
        profile_path = f"{file_path}.json"
        try:
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    candidate_name = json.load(f).get("full_name", "Candidate")
        except:
            pass

        # Try AI generation with timeout
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_json = json.dumps(json.load(f), indent=2)

            prompt = REPORT_GENERATION_PROMPT.format(
                profile_json=profile_json,
                quiz_score=quiz_score,
                coding_score=coding_score if coding_score else "Not Attempted",
                coding_feedback=coding_feedback or "N/A",
                quiz_feedback=quiz_feedback or "N/A"
            )

            response_text = await asyncio.wait_for(
                GeminiClient.generate_content(prompt, model_name="gemini-2.0-flash", timeout_seconds=60),
                timeout=75  # Outer gives 15s grace over inner
            )
            json_str = ReportGenerator._clean_json_response(response_text)
            data = json.loads(json_str)
            data.setdefault("credibility_status", "Authentic")
            data["quiz_score"] = quiz_score
            data["coding_score"] = coding_score
            if detailed_quiz_answers:
                data["detailed_quiz_answers"] = detailed_quiz_answers
            report = FinalReport(**data)
            
            with open(f"{file_path}.report.json", "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            return report
        except (asyncio.TimeoutError, TimeoutError) as e:
            logger.warning(f"Report generation timed out: {e}")
            report = ReportGenerator._generate_mock_report(candidate_name, quiz_score, coding_score, detailed_quiz_answers)
            try:
                with open(f"{file_path}.report.json", "w", encoding="utf-8") as f:
                    f.write(report.model_dump_json(indent=2))
            except:
                pass
            return report
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report = ReportGenerator._generate_mock_report(candidate_name, quiz_score, coding_score, detailed_quiz_answers)
            try:
                with open(f"{file_path}.report.json", "w", encoding="utf-8") as f:
                    f.write(report.model_dump_json(indent=2))
            except:
                pass
            return report
