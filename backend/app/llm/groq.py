import requests
import logging
import re
from typing import List, Dict, Tuple, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass


def parse_confidence_score(text: str) -> Tuple[str, Optional[float]]:
    """
    Extract confidence score from LLM response and return clean text.
    
    Looks for patterns like [CONFIDENCE: 0.85] at the end of the response.
    
    Args:
        text: Raw LLM response text
    
    Returns:
        Tuple of (cleaned_text, confidence_score)
        confidence_score is None if no valid score found
    """
    pattern = r'\[CONFIDENCE:\s*([0-9]*\.?[0-9]+)\]\s*$'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        try:
            score = float(match.group(1))
            if 0.0 <= score <= 1.0:
                cleaned_text = text[:match.start()].rstrip()
                return cleaned_text, score
            else:
                logger.warning(f"Confidence score {score} out of range [0.0, 1.0]")
        except ValueError:
            logger.warning(f"Failed to parse confidence score: {match.group(1)}")
    
    return text, None


def generate_answer(messages: List[Dict[str, str]], context: str) -> Tuple[str, Optional[float]]:
    """
    Generate answer using Groq API with conversation history.
    
    Args:
        messages: List of conversation messages [{"role": "user/assistant", "content": "..."}]
                  Should be the last N messages (windowed history)
        context: RAG-retrieved context from vector store
    
    Returns:
        Tuple of (answer_text, confidence_score)
        confidence_score is None if LLM doesn't provide one
        
    Raises:
        LLMError: If there's an error communicating with the LLM
    """
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_message = {
        "role": "system",
        "content": f"""You are a friendly AI assistant helping a user explore a document they have uploaded to the system.

IMPORTANT: The user has ALREADY LOADED A DOCUMENT into this conversation. You have access to relevant excerpts from that document below.

CONVERSATIONAL BEHAVIOR:
- Respond naturally to greetings (Hi, Hello, Hey, etc.)
  → Example: "Hello! I'm here to help you with your document. What would you like to know about it?"
- Acknowledge thank yous politely
  → Example: "You're welcome! Let me know if you have any other questions about the document."
- Be warm and conversational, not robotic
- For greetings, don't say "no document provided" - the document EXISTS and is loaded

ANSWERING QUESTIONS:
- When the user asks actual questions, use the relevant excerpts provided below
- Give detailed, comprehensive answers when information is available
- If the specific answer isn't in the excerpts, state: "That specific information isn't in this section of the document."
- Cite specific details when answering questions

SUMMARY REQUESTS:
- If asked for a summary/overview, synthesize the excerpts into a coherent summary
- Highlight main topics, key points, and important information from the excerpts
- Structure the summary logically (introduction, main points, conclusion)
- Don't say "no information available" if excerpts are provided - summarize what's there!

CONFIDENCE SCORING:
End every response with: [CONFIDENCE: X.XX] where X.XX is 0.0-1.0

Confidence Guidelines:
- Simple greetings/pleasantries: [CONFIDENCE: 1.00]
- Summary with good excerpts: [CONFIDENCE: 0.85-0.95]
- Question answered with clear context: [CONFIDENCE: 0.90-0.95]
- Partial information available: [CONFIDENCE: 0.60-0.75]
- Information not in excerpts: [CONFIDENCE: 0.10-0.20]

===== RELEVANT DOCUMENT EXCERPTS =====
{context}
===== END OF EXCERPTS ====="""
    }
    
    recent_messages = messages[-10:] if len(messages) > 10 else messages
    
    full_messages = [system_message] + recent_messages

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": full_messages,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                raw_answer = result["choices"][0]["message"]["content"].strip()
                clean_answer, confidence = parse_confidence_score(raw_answer)
                return clean_answer, confidence
            
            raise LLMError("No response generated from API")
        
        elif response.status_code == 401:
            raise LLMError("Invalid Groq API key")
        
        elif response.status_code == 429:
            raise LLMError("Rate limit exceeded")
        
        else:
            logger.error(f"Groq API Error: {response.status_code} - {response.text}")
            raise LLMError(f"API Error: {response.status_code}")
        
    except requests.exceptions.Timeout:
        raise LLMError("Request timed out")
    except LLMError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_answer: {str(e)}")
        raise LLMError(f"Unexpected error: {type(e).__name__}")


def generate_document_summary(context: str) -> str:
    """
    Generate a comprehensive summary/outline of a document based on initial excerpts.
    
    Args:
        context: Text excerpts from the document
    
    Returns:
        A formatted summary of the document
    """
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_message = {
        "role": "system",
        "content": """You are an AI assistant specializing in document analysis. Your task is to provide a clear, comprehensive overview of documents.

Given excerpts from a document, create a well-structured summary that includes:

**📄 Document Overview**
Brief description of what this document contains and its purpose.

**🔑 Key Topics**
- Main subjects and themes covered
- Important sections or categories

**⚡ Important Highlights**
- Critical policies, guidelines, or requirements
- Key dates, numbers, or specifications
- Notable rules or procedures

**📋 Document Structure**
How the content is organized and what sections are included.

Be concise but comprehensive. Use markdown formatting with emojis for visual appeal."""
    }
    
    user_message = {
        "role": "user",
        "content": f"""Please analyze these excerpts from a document and provide a comprehensive overview:

===== DOCUMENT EXCERPTS =====
{context}
===== END OF EXCERPTS =====

Provide a clear, structured summary of this document."""
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [system_message, user_message],
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                summary = result["choices"][0]["message"]["content"].strip()
                return summary
            raise LLMError("No summary generated from API")
        else:
            logger.error(f"Groq API Error: {response.status_code}")
            raise LLMError(f"API Error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        raise LLMError("Request timed out")
    except LLMError:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise LLMError(f"Unexpected error: {type(e).__name__}")


def generate_suggested_questions(context: str, document_name: str) -> List[str]:
    """
    Generate 4-5 relevant questions a user might want to ask about the document.
    
    Args:
        context: Text excerpts from the document
        document_name: Name of the document
    
    Returns:
        List of suggested questions
    """
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    
    system_message = {
        "role": "system",
        "content": """You are an AI assistant that generates relevant questions about documents.

Given excerpts from a document, generate 4-5 specific, insightful questions that users would likely want to ask.

Requirements:
- Questions should be specific to the document content
- Use natural, conversational language
- Mix different types: specific details, policies, procedures, implications
- Make questions actionable and relevant
- Return ONLY the questions, one per line, without numbering or bullets"""
    }
    
    user_message = {
        "role": "user",
        "content": f"""Based on these excerpts from "{document_name}", generate 4-5 relevant questions users might ask:

===== DOCUMENT EXCERPTS =====
{context}
===== END OF EXCERPTS =====

Generate the questions:"""
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [system_message, user_message],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                questions_text = result["choices"][0]["message"]["content"].strip()
                # Split by newlines and clean up
                questions = [
                    q.strip().lstrip('0123456789.-) ').strip()
                    for q in questions_text.split('\n')
                    if q.strip() and len(q.strip()) > 10
                ]
                return questions[:5]  # Return max 5 questions
            raise LLMError("No questions generated from API")
        else:
            logger.error(f"Groq API Error: {response.status_code}")
            return []  # Return empty list on error
            
    except requests.exceptions.Timeout:
        logger.warning("Timeout generating questions")
        return []
    except LLMError:
        return []
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        return []  # Return empty list on error
