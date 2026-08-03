"""
Coding Engine
Handles generation and AI-powered evaluation of coding challenges.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import CODING_CHALLENGE_PROMPT, CODE_EVALUATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.coding import CodingChallenge, EvaluationResult

logger = logging.getLogger(__name__)


class CodingEngine:

    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        """Robustly clean AI response to extract valid JSON."""
        if not response_text:
            return "{}"
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        if cleaned.startswith("{") or cleaned.startswith("["):
            return cleaned

        # Try to find top-level JSON object by locating balanced braces
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
    def _get_domain(profile: CandidateProfile) -> str:
        """Infer the candidate's primary technical domain from their profile."""
        skills_lower = [s.lower() for s in profile.technical_skills]
        projects_tech = []
        for p in profile.projects:
            projects_tech.extend([t.lower() for t in p.technologies])

        all_tech = skills_lower + projects_tech

        # Heuristic domain detection
        if any(t in all_tech for t in ["machine learning", "ml", "deep learning", "tensorflow", "pytorch", "sklearn"]):
            return "Machine Learning / Data Science"
        if any(t in all_tech for t in ["react", "vue", "angular", "frontend", "css", "html", "ui"]):
            return "Web Frontend Development"
        if any(t in all_tech for t in ["fastapi", "django", "flask", "express", "spring", "node", "rest api", "graphql"]):
            return "Backend / API Development"
        if any(t in all_tech for t in ["android", "ios", "react native", "flutter", "kotlin", "swift"]):
            return "Mobile Development"
        if any(t in all_tech for t in ["docker", "kubernetes", "aws", "gcp", "azure", "terraform", "devops", "ci/cd"]):
            return "DevOps / Cloud Infrastructure"
        if any(t in all_tech for t in ["postgresql", "mysql", "mongodb", "redis", "sql", "database"]):
            return "Backend / Database Engineering"
        if any(t in all_tech for t in ["blockchain", "solidity", "web3"]):
            return "Blockchain / Web3"

        return "General Software Engineering"

    @staticmethod
    def _generate_mock_challenges(profile: CandidateProfile) -> list:
        """Generate mock coding challenges when AI is unavailable."""
        mock_challenges = [
            CodingChallenge(
                title="Two Sum Problem",
                problem_statement="Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to the target.\n\nYou may assume each input has exactly one solution, and you cannot use the same element twice.",
                difficulty="Easy",
                function_signature="def find_two_sum(nums: list, target: int) -> list:",
                input_format="First line: n (length of array), followed by n integers\nSecond line: target integer",
                output_format="List of two indices [i, j] where nums[i] + nums[j] == target",
                constraints=["2 <= n <= 10^5", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9"],
                starter_code_by_language={
                    "python": "def find_two_sum(nums: list, target: int) -> list:\n    # Your solution here\n    pass",
                    "javascript": "function findTwoSum(nums, target) {\n    // Your solution here\n}",
                    "java": "class Solution {\n    public int[] findTwoSum(int[] nums, int target) {\n        // Your solution here\n        return null;\n    }\n}",
                    "cpp": "class Solution {\npublic:\n    vector<int> findTwoSum(vector<int>& nums, int target) {\n        // Your solution here\n    }\n};"
                },
                test_cases=[
                    {"input": "[2, 7, 11, 15], 9", "expected_output": "[0, 1]"},
                    {"input": "[3, 2, 4], 6", "expected_output": "[1, 2]"},
                ],
                tags=["array", "hash_map", "two_pointer"]
            ),
            CodingChallenge(
                title="Reverse Linked List",
                problem_statement="Given the head of a singly linked list, reverse the list and return the new head.\n\nReverse the list in-place.",
                difficulty="Medium",
                function_signature="def reverse_linked_list(head: ListNode) -> ListNode:",
                input_format="A linked list represented as [1,2,3,4,5]",
                output_format="The reversed linked list [5,4,3,2,1]",
                constraints=["0 <= number of nodes <= 5000", "-5000 <= node.val <= 5000"],
                starter_code_by_language={
                    "python": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverse_linked_list(head: ListNode) -> ListNode:\n    # Your solution here\n    pass",
                    "javascript": "class ListNode {\n    constructor(val = 0, next = null) {\n        this.val = val;\n        this.next = next;\n    }\n}\n\nfunction reverseLinkedList(head) {\n    // Your solution here\n}",
                    "java": "class ListNode {\n    int val;\n    ListNode next;\n    ListNode(int val) { this.val = val; }\n}\nclass Solution {\n    public ListNode reverseLinkedList(ListNode head) {\n        // Your solution here\n        return null;\n    }\n}",
                    "cpp": "struct ListNode {\n    int val;\n    ListNode* next;\n    ListNode(int x) : val(x), next(nullptr) {}\n};\nclass Solution {\npublic:\n    ListNode* reverseLinkedList(ListNode* head) {\n        // Your solution here\n    }\n};"
                },
                test_cases=[
                    {"input": "[1, 2, 3, 4, 5]", "expected_output": "[5, 4, 3, 2, 1]"},
                ],
                tags=["linked_list", "pointers"]
            ),
            CodingChallenge(
                title="Merge K Sorted Lists",
                problem_statement="You are given an array of k linked-lists `lists`, each linked-list is sorted in ascending order.\n\nMerge all the linked-lists into one sorted linked-list and return it.",
                difficulty="Hard",
                function_signature="def merge_k_lists(lists: list) -> ListNode:",
                input_format="Array of k linked lists, each sorted in ascending order",
                output_format="Single merged linked list sorted in ascending order",
                constraints=["k == lists.length", "0 <= k <= 10^4", "0 <= lists[i].length <= 500", "-10^4 <= lists[i][j] <= 10^4"],
                starter_code_by_language={
                    "python": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef merge_k_lists(lists: list) -> ListNode:\n    # Your solution here\n    pass",
                    "javascript": "class ListNode {\n    constructor(val = 0, next = null) {\n        this.val = val;\n        this.next = next;\n    }\n}\n\nfunction mergeKLists(lists) {\n    // Your solution here\n}",
                    "java": "class ListNode {\n    int val;\n    ListNode next;\n    ListNode(int val) { this.val = val; }\n}\nclass Solution {\n    public ListNode mergeKLists(ListNode[] lists) {\n        // Your solution here\n        return null;\n    }\n}",
                    "cpp": "struct ListNode {\n    int val;\n    ListNode* next;\n    ListNode(int x) : val(x), next(nullptr) {}\n};\nclass Solution {\npublic:\n    ListNode* mergeKLists(vector<ListNode*>& lists) {\n        // Your solution here\n    }\n};"
                },
                test_cases=[
                    {"input": "[[1, 4, 5], [1, 3, 4], [2, 6]]", "expected_output": "[1, 1, 2, 3, 4, 4, 5, 6]"},
                ],
                tags=["linked_list", "merge", "heap", "divide_and_conquer"]
            ),
        ]
        return mock_challenges

    @staticmethod
    async def generate_challenge(profile: CandidateProfile, force_regenerate: bool = False) -> Optional[list]:
        """
        Generate 3 coding challenges (Easy, Medium, Hard) based on the candidate's profile.
        Returns a list of CodingChallenge objects.
        """
        top_skills = profile.technical_skills[:6]
        skills_str = ", ".join(top_skills) if top_skills else "General programming"
        domain = CodingEngine._get_domain(profile)

        prompt = CODING_CHALLENGE_PROMPT.format(
            experience_level=profile.experience_level,
            skills=skills_str,
            domain=domain
        )

        try:
            response_text = await asyncio.wait_for(
                GeminiClient.generate_content(prompt, model_name="gemini-2.0-flash", timeout_seconds=60),
                timeout=75  # Outer timeout gives 15s grace over inner
            )

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError(f"AI failed: {response_text}")

            json_str = CodingEngine._clean_json_response(response_text)
            
            # Parse as array of challenges
            data_array = json.loads(json_str)
            if not isinstance(data_array, list):
                raise ValueError("Expected array of challenges from AI")
            
            challenges = []
            for data in data_array:
                # Ensure function_signature is set
                if not data.get("function_signature") and data.get("starter_code_by_language", {}).get("python"):
                    data["function_signature"] = data["starter_code_by_language"]["python"]

                # Ensure starter_code_by_language has all languages
                if not data.get("starter_code_by_language"):
                    data["starter_code_by_language"] = {
                        "python": data.get("function_signature", "def solve():\n    pass"),
                        "javascript": "function solve() {\n    // Write your solution here\n}",
                        "java": "class Solution {\n    public Object solve() {\n        // Write your solution here\n        return null;\n    }\n}",
                        "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    auto solve() {\n        // Write your solution here\n    }\n};"
                    }

                challenge = CodingChallenge(**data)
                challenges.append(challenge)
            
            return challenges if challenges else None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse coding challenges JSON: {e}")
            logger.debug(f"Raw (first 500): {response_text[:500] if response_text else 'None'}")
            logger.info("Using mock challenges as fallback")
            return CodingEngine._generate_mock_challenges(profile)
        except asyncio.TimeoutError:
            logger.warning("Coding challenge generation timed out")
            logger.info("Using mock challenges as fallback")
            return CodingEngine._generate_mock_challenges(profile)
        except Exception as e:
            logger.error(f"Challenge generation failed: {e}")
            logger.info("Using mock challenges as fallback")
            return CodingEngine._generate_mock_challenges(profile)

    @staticmethod
    def _run_code_locally(code: str, test_cases: list) -> list:
        """
        Execute Python code locally against test cases for real-world verification.
        """
        import subprocess
        import sys
        import tempfile
        import time
        
        results = []
        for i, tc in enumerate(test_cases):
            # Create a wrapper script to run the function with input
            # This assumes the function name is 'solve' which we enforce in the prompt
            wrapper = f"""
{code}
import json
try:
    # Handle inputs (string representation)
    inp = {tc.get('input', 'None')}
    result = solve(inp)
    print(json.dumps(result))
except Exception as e:
    print(f"ERROR: {{str(e)}}")
"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(wrapper)
                temp_path = f.name
            
            try:
                start = time.time()
                proc = subprocess.run(
                    [sys.executable, temp_path],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                duration = time.time() - start
                
                output = proc.stdout.strip()
                if output.startswith("ERROR:"):
                    results.append({"index": i, "passed": False, "actual": output, "error": True})
                else:
                    # Compare output to expected
                    try:
                        actual_val = json.loads(output)
                        expected_val = json.loads(tc.get('expected_output', 'null'))
                        passed = (actual_val == expected_val)
                        results.append({"index": i, "passed": passed, "actual": str(actual_val), "error": False})
                    except:
                        results.append({"index": i, "passed": False, "actual": output, "error": False})
            except subprocess.TimeoutExpired:
                results.append({"index": i, "passed": False, "actual": "TIMEOUT (Infinite loop?)", "error": True})
            except Exception as e:
                results.append({"index": i, "passed": False, "actual": str(e), "error": True})
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        return results

    @staticmethod
    async def evaluate_code(challenge: CodingChallenge, code: str, language: str = "python", skipped: bool = False) -> EvaluationResult:
        """
        Evaluate code submission using a Hybrid Logic Engine (Real Run + AI Audit).
        Scoring:
        - skipped=True: score=0
        - skipped=False, attempted but failed: score=5
        - skipped=False, all tests passed: score=100
        NOTE: Always returns a valid EvaluationResult (never None)
        """
        from app.models.coding import TestCaseResult
        
        # Check if skipped
        if skipped or not code or not code.strip():
            return EvaluationResult(
                success=False,
                score=0,
                attempted=not skipped,  # False if skipped, True if just empty
                passed_test_cases=0,
                total_test_cases=len(challenge.test_cases),
                feedback="Challenge was skipped." if skipped else "Empty submission.",
                time_complexity="N/A",
                suggestions=["Try to solve the challenge." if skipped else "Write code."],
                test_results=[]
            )

        # 1. ACTUAL EXECUTION (For Python)
        local_results = []
        if language.lower() == "python":
            local_results = CodingEngine._run_code_locally(code, [t.model_dump() for t in challenge.test_cases])

        # 2. DEEP AI AUDIT (Informing the AI with local run results)
        try:
            local_context = "LOCAL EXECUTION RESULTS:\n" + json.dumps(local_results, indent=2) if local_results else "Local execution skipped (non-python)."
            prompt = CODE_EVALUATION_PROMPT.format(
                problem_statement=challenge.problem_statement,
                test_cases=json.dumps([t.model_dump() for t in challenge.test_cases], indent=2),
                code=code,
                language=language.capitalize()
            )
            # Append local findings to the prompt
            prompt += f"\n\n{local_context}\n\nEVALUATE BASED ON THE ABOVE TRUTH."

            response_text = await asyncio.wait_for(
                GeminiClient.generate_content(prompt, model_name="gemini-2.0-flash", timeout_seconds=60),
                timeout=75  # Outer timeout gives 15s grace over inner
            )
            json_str = CodingEngine._clean_json_response(response_text)
            data = json.loads(json_str)
            
            # Convert test_results to proper TestCaseResult objects if present
            if 'test_results' in data and isinstance(data['test_results'], list):
                test_results_list = []
                for i, tr in enumerate(data['test_results']):
                    try:
                        test_results_list.append(TestCaseResult(
                            test_case_index=i,
                            passed=tr.get('passed', False),
                            input=tr.get('input', ''),
                            expected_output=tr.get('expected_output', ''),
                            actual_output=tr.get('actual_output', ''),
                            explanation=tr.get('explanation', '')
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to parse test result {i}: {e}")
                data['test_results'] = test_results_list
            
            # If local results say it failed, and AI says it passed, LOCAL RESULTS WIN
            if local_results:
                passed_count = sum(1 for r in local_results if r['passed'])
                data['passed_test_cases'] = passed_count
                all_passed = passed_count == len(challenge.test_cases)
                data['success'] = all_passed
                
                # Apply skip penalty scoring:
                # - All tests passed: score = 100
                # - Some tests failed: score = 5 (for attempting)
                if all_passed:
                    data['score'] = 100
                else:
                    data['score'] = 5  # Penalty for attempt but failed
                
                # Convert local_results to TestCaseResult objects
                test_results_list = []
                for i, lr in enumerate(local_results):
                    test_results_list.append(TestCaseResult(
                        test_case_index=i,
                        passed=lr.get('passed', False),
                        input=challenge.test_cases[i].input if i < len(challenge.test_cases) else '',
                        expected_output=challenge.test_cases[i].expected_output if i < len(challenge.test_cases) else '',
                        actual_output=lr.get('actual', ''),
                        explanation=f"{'PASS' if lr.get('passed') else 'FAIL'}: {lr.get('actual', '')}"
                    ))
                data['test_results'] = test_results_list
            
            # Mark as attempted
            data['attempted'] = True
            data['total_test_cases'] = len(challenge.test_cases)
            
            return EvaluationResult(**data)
        except asyncio.TimeoutError:
            logger.error("Code evaluation timed out")
            # Return partial evaluation based on local results
            if local_results:
                passed_count = sum(1 for r in local_results if r['passed'])
                all_passed = passed_count == len(challenge.test_cases)
                score = 100 if all_passed else 5
                
                # Convert local results to TestCaseResult objects
                test_results_list = []
                for i, lr in enumerate(local_results):
                    test_results_list.append(TestCaseResult(
                        test_case_index=i,
                        passed=lr.get('passed', False),
                        input=challenge.test_cases[i].input if i < len(challenge.test_cases) else '',
                        expected_output=challenge.test_cases[i].expected_output if i < len(challenge.test_cases) else '',
                        actual_output=lr.get('actual', ''),
                        explanation=f"{'PASS' if lr.get('passed') else 'FAIL'}: {lr.get('actual', '')}"
                    ))
                
                return EvaluationResult(
                    success=all_passed,
                    score=score,
                    attempted=True,
                    passed_test_cases=passed_count,
                    total_test_cases=len(challenge.test_cases),
                    feedback="Evaluation timed out but local tests were run.",
                    time_complexity="Unable to determine",
                    suggestions=["Evaluation incomplete due to timeout"],
                    test_results=test_results_list
                )
            # Fallback when no local results
            return EvaluationResult(
                success=False,
                score=0,
                attempted=True,
                passed_test_cases=0,
                total_test_cases=len(challenge.test_cases),
                feedback="Code evaluation timed out. Please try again.",
                time_complexity="Unable to determine",
                suggestions=["The evaluation took too long. Your code may have an infinite loop."],
                test_results=[]
            )
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Return error result instead of None
            if local_results:
                passed_count = sum(1 for r in local_results if r['passed'])
                all_passed = passed_count == len(challenge.test_cases)
                score = 100 if all_passed else 5
                
                # Convert local results to TestCaseResult objects
                test_results_list = []
                for i, lr in enumerate(local_results):
                    test_results_list.append(TestCaseResult(
                        test_case_index=i,
                        passed=lr.get('passed', False),
                        input=challenge.test_cases[i].input if i < len(challenge.test_cases) else '',
                        expected_output=challenge.test_cases[i].expected_output if i < len(challenge.test_cases) else '',
                        actual_output=lr.get('actual', ''),
                        explanation=f"{'PASS' if lr.get('passed') else 'FAIL'}: {lr.get('actual', '')}"
                    ))
                
                return EvaluationResult(
                    success=all_passed,
                    score=score,
                    attempted=True,
                    passed_test_cases=passed_count,
                    total_test_cases=len(challenge.test_cases),
                    feedback=f"Evaluation error: {str(e)} (Local tests: {passed_count}/{len(challenge.test_cases)} passed)",
                    time_complexity="Unable to determine",
                    suggestions=["Try fixing the identified test failures"],
                    test_results=test_results_list
                )
            return EvaluationResult(
                success=False,
                score=0,
                attempted=True,
                passed_test_cases=0,
                total_test_cases=len(challenge.test_cases),
                feedback=f"Code evaluation failed: {str(e)[:100]}",
                time_complexity="Unable to determine",
                suggestions=["Check your code for syntax errors or runtime issues"],
                test_results=[]
            )

    @staticmethod
    async def generate_for_session(file_path: str, force_regenerate: bool = False) -> Optional[list]:
        """
        Orchestrate challenge generation from file session.
        Uses cache unless force_regenerate=True.
        Returns list of 3 challenges.
        """
        challenge_path = f"{file_path}.coding.json"

        # Check cache
        if not force_regenerate and os.path.exists(challenge_path):
            try:
                with open(challenge_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [CodingChallenge(**ch) for ch in data]
                    else:
                        # Handle old single challenge format
                        return [CodingChallenge(**data)]
            except Exception:
                pass

        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            logger.error(f"Profile not found for {file_path}")
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                profile = CandidateProfile(**profile_data)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

        challenges = await CodingEngine.generate_challenge(profile, force_regenerate=force_regenerate)

        if challenges:
            try:
                with open(challenge_path, "w", encoding="utf-8") as f:
                    # Save as array of challenges
                    challenge_dicts = [ch.model_dump() for ch in challenges]
                    f.write(json.dumps(challenge_dicts, indent=2))
                logger.info(f"Challenges ({len(challenges)} total) saved to {challenge_path}")
            except Exception as e:
                logger.error(f"Failed to save challenges: {e}")

        return challenges
