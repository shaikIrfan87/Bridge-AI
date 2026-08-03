"""
Code Execution Service
Safely executes code using Piston API (external sandbox)
Replaces the non-functional Gemini-based code "execution"
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

# Piston API endpoint - free code execution service
PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"

class CodeTestCase(BaseModel):
    """Represents a test case for code execution"""
    input_data: str
    expected_output: str
    visible: bool = True  # Whether to show to candidate


class CodeExecutionRequest(BaseModel):
    """Request to execute code"""
    language: str  # "python", "javascript", "java", etc.
    code: str
    test_cases: List[CodeTestCase] = []


class CodeExecutionResult(BaseModel):
    """Result of code execution"""
    success: bool
    output: str
    error: Optional[str] = None
    test_passed: Optional[int] = None  # Number of tests passed
    test_results: List[Dict[str, Any]] = []


class PistonCodeExecutor:
    """
    Executes code safely using Piston API
    Provides sandboxed execution without local security risks
    """
    
    # Supported languages in Piston
    LANGUAGE_RUNTIMES = {
        "python": "python",
        "javascript": "node",
        "nodejs": "node",
        "java": "java",
        "go": "go",
        "rust": "rust",
        "cpp": "cpp",
        "c": "c",
    }
    
    @classmethod
    async def execute_code(
        cls,
        code: str,
        language: str,
        timeout: int = None
    ) -> CodeExecutionResult:
        """
        Execute code in sandboxed environment.
        
        Args:
            code: Source code to execute
            language: Programming language
            timeout: Execution timeout in seconds
        
        Returns:
            CodeExecutionResult with output or error
        """
        if timeout is None:
            timeout = settings.CODE_TIMEOUT_SECONDS
        
        language = language.lower()
        runtime = cls.LANGUAGE_RUNTIMES.get(language)
        
        if not runtime:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Unsupported language: {language}. Supported: {', '.join(cls.LANGUAGE_RUNTIMES.keys())}"
            )
        
        try:
            request_body = {
                "language": runtime,
                "version": "*",
                "files": [{"name": f"main.{cls._get_extension(language)}", "content": code}],
                "compile": {"args": []},
                "run": {"args": [], "stdin": ""}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    PISTON_API_URL,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Piston API error: {error_text}")
                        return CodeExecutionResult(
                            success=False,
                            output="",
                            error=f"Code execution service error (HTTP {response.status})"
                        )
                    
                    result = await response.json()
                    
                    # Parse Piston response
                    if result.get("compile") and result["compile"].get("signal"):
                        # Compilation error
                        stderr = result.get("compile", {}).get("stderr", "Compilation failed")
                        return CodeExecutionResult(
                            success=False,
                            output="",
                            error=stderr[:settings.MAX_CODE_OUTPUT_LENGTH]
                        )
                    
                    if result.get("run") and result["run"].get("signal"):
                        # Runtime error
                        stderr = result.get("run", {}).get("stderr", "Runtime error")
                        return CodeExecutionResult(
                            success=False,
                            output="",
                            error=stderr[:settings.MAX_CODE_OUTPUT_LENGTH]
                        )
                    
                    output = result.get("run", {}).get("stdout", "").strip()
                    return CodeExecutionResult(
                        success=True,
                        output=output[:settings.MAX_CODE_OUTPUT_LENGTH]
                    )
        
        except asyncio.TimeoutError:
            logger.warning(f"Code execution timeout after {timeout}s")
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Code execution timeout (max {timeout} seconds). Your code may be in an infinite loop or too slow."
            )
        except aiohttp.ClientConnectionError as e:
            logger.error(f"Connection error to Piston API: {str(e)}")
            return CodeExecutionResult(
                success=False,
                output="",
                error="Code execution service is currently unavailable (no internet connection or service down). Please check your connection and try again."
            )
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error from Piston API: {str(e)}")
            return CodeExecutionResult(
                success=False,
                output="",
                error="Code execution service temporarily unavailable. Please try again in a moment."
            )
        except Exception as e:
            logger.error(f"Unexpected error during code execution: {str(e)}")
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Unexpected error during code execution: {str(e)}"
            )
    
    @classmethod
    async def run_test_cases(
        cls,
        code: str,
        language: str,
        test_cases: List[CodeTestCase]
    ) -> CodeExecutionResult:
        """
        Execute code against test cases.
        Returns number of passing tests and detailed results.
        """
        result = await cls.execute_code(code, language)
        
        if not result.success:
            return result
        
        # For simple test cases, compare outputs
        passed = 0
        test_results = []
        
        for i, test_case in enumerate(test_cases):
            # This is a simplified test evaluation
            # For full implementation, create test harnesses for each language
            test_result = {
                "test_case_index": i,
                "input": test_case.input_data if test_case.visible else "(hidden)",
                "expected_output": test_case.expected_output if test_case.visible else "(hidden)",
                "passed": False,
                "explanation": "Test framework not yet implemented for this language"
            }
            test_results.append(test_result)
        
        result.test_passed = passed
        result.test_results = test_results
        return result
    
    @staticmethod
    def _get_extension(language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "nodejs": "js",
            "java": "java",
            "go": "go",
            "rust": "rs",
            "cpp": "cpp",
            "c": "c",
        }
        return extensions.get(language.lower(), "txt")
