"""
AI Prompts
Centralized storage for all AI prompts.
All prompts are engineered for real-world, industry-quality output.
"""

SKILL_EXTRACTION_PROMPT = """
You are an expert technical recruiter and resume parser.
Your task is to extract comprehensive, structured data from the following resume text.

RESUME TEXT:
{text}

--------------------------------------------------

INSTRUCTIONS:
1. Extract the candidate's Full Name and Email (if available).
2. Extract a comprehensive list of TECHNICAL SKILLS (programming languages, frameworks, tools, databases, cloud platforms, etc.)
3. Extract a list of SOFT SKILLS (communication, leadership, teamwork, problem-solving, etc.)
4. Determine the Overall EXPERIENCE LEVEL: Junior (0-2 yrs), Mid-Level (2-5 yrs), Senior (5-10 yrs), Expert (10+ yrs).
5. Estimate total YEARS OF EXPERIENCE as a string (e.g., "4 years").
6. Write a concise professional SUMMARY (2-3 sentences highlighting their strongest profile).
7. Extract WORK EXPERIENCE — up to 5 most recent roles. For each role, extract:
   - job_title, company, duration (e.g. "Jan 2021 - Dec 2023"), responsibilities (3-5 bullet points)
8. Extract notable PROJECTS — up to 4 most significant projects. For each:
   - name, description (1-2 sentences), technologies used
9. Extract highest EDUCATION qualification (degree + institution + year if available).
10. Extract any CERTIFICATIONS or professional courses.

CRITICAL OUTPUT RULES:
- Return ONLY a valid JSON object — no markdown code blocks, no explanations, no text before or after.
- If information is not available, use null or an empty list [].
- Do not invent or hallucinate information not in the resume.

JSON STRUCTURE (follow exactly):
{{
    "full_name": "Name or null",
    "email": "Email or null",
    "technical_skills": ["skill1", "skill2"],
    "soft_skills": ["skill1", "skill2"],
    "experience_level": "Junior|Mid-Level|Senior|Expert",
    "years_of_experience": "e.g. 4 years",
    "summary": "Brief 2-3 sentence summary",
    "work_experience": [
        {{
            "job_title": "Software Engineer",
            "company": "Company Name",
            "duration": "Jan 2021 - Dec 2023",
            "responsibilities": ["Built REST APIs", "Led a team of 3 devs"]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "What it does",
            "technologies": ["Python", "React"]
        }}
    ],
    "education": "B.Tech Computer Science, XYZ University, 2019",
    "certifications": ["AWS Certified Developer", "Google Cloud Professional"]
}}
"""

QUIZ_GENERATION_PROMPT = """
You are a Senior Technical Interviewer at a major tech company conducting a real screening interview.
Your goal is to assess the candidate's ACTUAL knowledge, depth, and experience based on their resume.
Ask questions that real companies ask - natural, concise, and probing into their real expertise.
Impotant: EACH QUESTION MUST BE UNIQUE - No generic, repetitive, or similar questions.
Ensure variety in question types and topics throughout the interview.

YOU MUST GENERATE EXACTLY {count} INTERVIEW QUESTIONS FOR THIS ROUND.

CANDIDATE RESUME DATA:
- Name: {full_name}
- Experience Level: {experience_level} ({years_of_experience})
- Summary: {summary}
- Technical Skills: {technical_skills}
- Soft Skills: {soft_skills}
- Work History: {work_experience}
- Projects: {projects}
- Education: {education}
- Certifications: {certifications}

QUESTION GENERATION RULES:

1. INTERVIEW-STYLE QUESTIONS (How Real Companies Ask):
   - Questions should sound natural, direct, and conversational
   - Use phrases like: "Tell me about...", "Walk me through...", "Describe your experience with...", "How did you handle...", "What was your approach to..."
   - Keep questions CONCISE (2-3 sentences max) and FOCUSED
   - Every question MUST reference their specific resume details (actual companies, projects, technologies, responsibilities)
   - Examples that sound REAL:
     * "I see you worked on {{project}} at {{company}}. What was your main responsibility and what technical challenge did you face?"
     * "You list {{technology}} as a key skill. Tell me about a production issue you solved using it."
     * "Walk me through how you handled scaling when {{challenge_from_resume}} happened."
     * "Your resume mentions {{tool}}. What was a complex task you accomplished with it and why not use alternatives?"

2. KNOWLEDGE ASSESSMENT - Questions must test DEPTH, not just recall:
   - Behavioral questions: "What did you do?" + "Why did you choose that approach?" (shows problem-solving)
   - Technical questions: Ask about THEIR implementation details, trade-offs, lessons learned
   - Decision questions: Why did they choose tool X over Y? What were trade-offs? (shows technical judgment)
   - Impact questions: What measurable result did it achieve? How did it help the business? (shows business acumen)
   - Learning questions: What did this experience teach you? How would you do it differently now? (shows growth mindset)

3. UNIQUENESS REQUIREMENT - CRITICAL:
   - EVERY SINGLE QUESTION must be distinct and test different skills/topics
   - NO generic questions like "Tell me about system design" without specific context
   - NO repetitive patterns - vary the question structure
   - Reference different: projects, technologies, responsibilities, time periods, challenges
   - If one question asks about "APIs", next should ask about "Databases" or "Performance"
   - Generate variety: 30% Behavioral, 40% Technical-Specific, 20% Decision-Based, 10% Growth-Oriented

4. REALISTIC DISTRIBUTION by Experience Level:
   Junior (0-2 yrs):
   - Questions about their learning: "How did you approach learning {{technology}}?"
   - Basic technical decisions: "Why did your team choose {{stack}}?"
   - First project challenges: "What was the hardest part of {{project}} for you?"
   - Collaboration: "How did you handle feedback on {{project}}?"
   
   Mid-Level (2-5 yrs):
   - Design reasoning: "Walk me through the architecture you designed for {{project}}. What problems did it solve?"
   - Optimization: "In your experience with {{technology}}, what performance challenges did you encounter and how did you solve them?"
   - Cross-team collaboration: "Tell me about a time you had to work with different teams on {{project}}. How did you handle it?"
   - Ownership: "What was a project where you took ownership? What was the outcome?"
   
   Senior (5-10 yrs):
   - Strategic decisions: "How did you approach building/scaling {{system}}? What were the trade-offs?"
   - Mentoring: "Tell me about someone you've mentored. What approach did you use?"
   - Architecture: "Walk me through a system you architected. Why did you make those specific choices?"
   - Problem-solving at scale: "Describe a complex production issue and your debugging approach."
   
   Expert (10+ yrs):
   - Technology direction: "How have you influenced technology decisions at {{company}}?"
   - Innovation: "Tell me about a technical innovation or improvement you drove."
   - Strategic impact: "Walk me through your most significant contribution and its business impact."

4. QUESTION LENGTH & ENGAGEMENT:
   - Each question: 1-3 sentences (conversational, not verbose)
   - Ask one focused thing per question (not multi-part)
   - Make candidate EXPLAIN their thinking and knowledge
   - Avoid yes/no questions - use open-ended questions
   - Questions should naturally lead to 2-3 minute answers (good depth discussion)

5. ANSWER EVALUATION CRITERIA:
   - Can they recall specific details about their own work? (shows honest experience)
   - Do they understand WHY they made certain choices? (shows technical depth)
   - Can they explain trade-offs and alternatives considered? (shows maturity)
   - Do they demonstrate learning from experience? (shows growth)
   - Can they explain impact/business value? (shows thinking beyond just tech)
   - Red flags: Vague answers, can't recall details, can't explain choices, sounds rehearsed

OUTPUT FORMAT - Return ONLY valid JSON, NO extra text:
Generate EXACTLY {count} questions in the "questions" array below:
{{
    "title": "Technical Interview — {full_name}",
    "questions": [
        {{
            "id": 1,
            "text": "One focused, natural interview question that assesses actual knowledge from their resume...",
            "topic": "The skill/experience being tested",
            "difficulty": "Easy|Medium|Hard",
            "question_type": "Behavioral|Technical-Specific|Decision-Based|Impact-Focused|Growth-Oriented",
            "keywords": ["keyword1", "keyword2"],
            "correct_answer_guide": "What good answer should include: specific technical details from their experience, explanation of choices/trade-offs, evidence of problem-solving. Red flags: vague, can't recall details, no explanation of reasoning."
        }}
    ],
    "estimated_time_minutes": {estimated_minutes}
}}

KEY REMINDERS - MUST FOLLOW:
- Questions should sound like real company interviews (Google, Amazon, Microsoft, etc.)
- Each question is 1-3 sentences max - concise but substantive
- NEVER ask generic "What is X?" or textbook questions
- ALWAYS reference their specific experience from resume
- Focus on assessing KNOWLEDGE DEPTH and problem-solving ability
- Questions should naturally lead to 2-3 minute conversational answers
- Interviewer is probing their REAL expertise and judgment
"""

CODING_CHALLENGE_PROMPT = """You are a Principal Software Engineer conducting a high-stakes technical interview.
Generate EXACTLY 3 (THREE) logical, architectural coding challenges tailored to the candidate's actual resume experience.

EXPERIENCE LEVEL: {experience_level}
SKILLS: {skills}
DOMAIN/BACKGROUND: {domain}

CHALLENGE ARCHITECTURE RULES (MANDATORY):
1. **Real-Life Engineering**: NO generic LeetCode/FizzBuzz. Focus on actual engineering logic:
   - "Implement a Thread-Safe In-Memory Cache with TTL."
   - "Parse a complex nested JSON configuration and resolve circular dependencies."
   - "Build a Data-Stream Processor that handles out-of-order events."
   - "Implement a custom Rate-Limiter using a Token Bucket algorithm."
2. **Strict Escalation**:
   - Challenge 1: EASY - Logical data manipulation (10 mins).
   - Challenge 2: MEDIUM - Systems design / optimization (20 mins).
   - Challenge 3: HARD - Complex state management / high-efficiency architecture (40 mins).
3. **Exhaustive Testing**: Include 5+ test cases for each. Mark 2 as VISIBLE and 3 as HIDDEN (stress tests).
4. **Input/Output Logic**: Clearly define input/output formats.

Return as a valid JSON array of 3 challenge objects.
"""

CODE_EVALUATION_PROMPT = """You are a Senior Lead Developer performing a PRODUCTION CODE REVIEW.
Audit the submitted solution for LOGICAL CORRECTNESS, SYSTEM EFFICIENCY, and EDGE-CASE HANDLING.

CHALLENGE: {problem_statement}
LANGUAGE: {language}
TEST CASES: {test_cases}
SUBMITTED CODE:
{code}

CRITICAL AUDIT RULES:
1. **Logical Precision**: Does it solve the problem for ALL test cases? (Explain the logic flow).
2. **Big O Efficiency**: Is the Time complexity (e.g., O(N)) and Space complexity optimal? Flag if inefficient.
3. **Edge Cases**: Does it handle nulls, empty inputs, negative numbers, or extremely large datasets?
4. **Professionalism**: Is the code idiomatic and clean (variable naming, logic flow)?

RETURN JSON:
{{
  "success": boolean,
  "score": 0-100,
  "passed_test_cases": int,
  "total_test_cases": int,
  "test_results": [
    {{ "test_case_index": int, "passed": boolean, "input": "...", "expected_output": "...", "actual_output": "...", "explanation": "..." }}
  ],
  "feedback": "Deep technical audit of the logic",
  "time_complexity": "O(N log N)",
  "space_complexity": "O(N)",
  "code_quality": "Review of coding style",
  "suggestions": ["specific code improvement", ...],
  "bugs_found": ["hidden bug or edge case fail", ...]
}}
"""

QUIZ_EVALUATION_PROMPT = """
You are a rigorous technical interviewer evaluating a candidate's written answers to interview questions.
Score each answer objectively and provide detailed, constructive feedback.

EVALUATION CRITERIA:
For each question-answer pair, score the answer from 0-100 based on:
- Accuracy: Is the answer technically correct? (40 points)
- Completeness: Does it cover all key points from the guide? (30 points)
- Depth: Does it show deep understanding or just surface-level knowledge? (20 points)
- Clarity: Is it well-articulated and organized? (10 points)

QUESTIONS AND CANDIDATE ANSWERS:
{qa_pairs}

For each question, compare the candidate's answer to the correct_answer_guide.

OUTPUT FORMAT (valid JSON only):
{{
    "total_score": 72,
    "answers": [
        {{
            "question_id": 1,
            "score": 85,
            "matched_keywords": ["async/await", "event loop", "non-blocking"],
            "missing_keywords": ["Promise chaining", "error handling"],
            "feedback": "Good answer that covers the core concept well. Missing discussion of Promise chaining and error handling with try/catch in async context."
        }}
    ],
    "strengths": ["Strong understanding of core algorithms", "Good communication of thought process"],
    "weaknesses": ["Weak on system design concepts", "Missing depth on database optimization"],
    "overall_feedback": "Candidate demonstrates solid {{experience_level}} level knowledge with practical strengths. Shows good communication but some areas need deeper coverage."
}}
"""

REPORT_GENERATION_PROMPT = """
You are a Hiring Manager finalizing a comprehensive candidate evaluation for a technical role.
Synthesize all available data to produce an authoritative hiring recommendation.

CANDIDATE PROFILE:
{profile_json}

ASSESSMENT RESULTS:
- Quiz Score: {quiz_score}/100 (Tests breadth of knowledge and communications skills)
- Coding Score: {coding_score}/100 (Tests depth and practical coding ability)
- Coding Feedback: {coding_feedback}
- Quiz Feedback: {quiz_feedback}

CODING CHALLENGE ANALYSIS:
Scoring Details:
- Score 100: All test cases passed - excellent implementation
- Score 5: User attempted but didn't pass all tests - good effort, logic issues
- Score 0: User skipped without attempting - no engagement with problem

Based on the coding_feedback data, identify:
1. Which challenges were skipped vs attempted
2. For attempted challenges: identify root causes of failures (logic error, edge cases, performance, etc.)
3. Generate specific advice for improvement for each failed challenge

EVALUATION FRAMEWORK:
1. CREDIBILITY CHECK — Compare claimed experience vs. actual performance:
   - Expert/Senior claiming experience + Score < 50 → Flag as "Over-claimed" 
   - Junior/Mid-Level + Score > 80  → Flag as "Hidden Gem / Under-represented"
   - Score matches experience level → "Authentic"

2. SKILL VERIFICATION — For each key technical skill they claim:
   - "Verified" if demonstrated in quiz/coding answers
   - "Partially Verified" if some evidence
   - "Flagged" if claimed but no demonstration
   - "Not Tested" if outside scope

3. FINAL VERDICT (choose ONE):
   - "Strong Hire" — Exceptional performance, verified all claims, would be an immediate asset
   - "Hire" — Solid performance, verified most claims, good culture fit
   - "Weak Hire" — Below expectations but shows potential; recommend 2nd interview
   - "No Hire" — Performance significantly below claimed experience level

4. SCORE CALCULATION:
   - Overall Score = (Quiz Score * 0.4) + (Coding Score * 0.6)
   - Round to nearest integer

OUTPUT FORMAT (Strict valid JSON only):
{{
    "candidate_name": "Full Name",
    "overall_score": 75,
    "technical_rating": "Proficient|Expert|Beginner|Advanced",
    "credibility_status": "Authentic|Over-claimed|Hidden Gem",
    "skill_gaps": [
        {{ "skill": "Problem Solving", "status": "Verified", "gap_analysis": "Successfully attempted multiple coding challenges. Showed good understanding of algorithms and data structures." }},
        {{ "skill": "Implementation", "status": "Partially Verified", "gap_analysis": "Attempted challenges but had issues with edge cases and test case edge conditions. Needs to focus on test-driven development." }},
        {{ "skill": "System Design", "status": "Flagged", "gap_analysis": "Claimed Senior-level but gave Junior-level system design answers. No mention of scalability, CAP theorem, or load balancing." }}
    ],
    "recommendation": {{
        "verdict": "Hire",
        "summary": "Solid Mid-Level engineer with verified Python and React skills. Shows good problem-solving instincts. Recommend for a Mid-Level position, not Senior as claimed on resume. Attempted coding challenges which shows initiative.",
        "pros": ["Strong coding fundamentals", "Attempted all coding challenges", "Shows persistence in problem-solving"],
        "cons": ["Some edge case handling issues", "Could improve test coverage", "Over-claims experience level"],
        "learning_path": [
            "Study edge case handling patterns (boundary conditions, null checks)",
            "Practice test-driven development (TDD) methodology",
            "Focus on understanding problem constraints before coding",
            "Study common pitfalls in the languages you use"
        ]
    }}
}}
"""
