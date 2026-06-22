import os
import fitz  # PyMuPDF
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Define the State
class CourseState(TypedDict):
    topic: str
    folder_path: str
    context: str
    objectives: str
    sections: str
    quizzes: str
    summary: str
    review_feedback: Optional[str]
    revision_count: int

# Initialize LLM
# Assuming GROQ_API_KEY is set in environment
def get_llm():
    # Reduced max_tokens to stay within the 6000 TPM limit of your organization tier
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0.2, max_tokens=2000)

# Nodes
def extract_context(state: CourseState) -> CourseState:
    folder_path = state["folder_path"]
    context_text = ""
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if filename.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(file_path)
                    for page in doc:
                        context_text += page.get_text() + "\n"
                except Exception as e:
                    print(f"Error reading PDF {filename}: {e}")
            elif filename.lower().endswith(".txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        context_text += f.read() + "\n"
                except Exception as e:
                    print(f"Error reading TXT {filename}: {e}")
    else:
        context_text = "No valid documents found or folder does not exist."
    
    # Cap context length based on the 6,000 token organization TPM limit
    # 12,000 characters is roughly ~2,800 tokens
    max_chars = 12000 
    if len(context_text) > max_chars:
        context_text = context_text[:max_chars] + "...[TRUNCATED]"

    return {"context": context_text}

def design_curriculum(state: CourseState) -> CourseState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Curriculum Designer. First, analyze the provided context and the requested topic. If the context is NOT related to the topic, respond exactly with 'ERROR: UNRELATED'. If it is related, create learning objectives for the given topic based ONLY on the provided context. Do NOT use any external knowledge. All objectives must be directly supported by the context. Format as a markdown list."),
        ("user", "Topic: {topic}\n\nContext:\n{context}")
    ])
    chain = prompt | llm
    res = chain.invoke({"topic": state["topic"], "context": state["context"]})
    return {"objectives": res.content}

def write_content(state: CourseState) -> CourseState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Content Writer. Write detailed educational content sections based on the learning objectives and the context. You MUST rely ONLY on the provided context. Do NOT use any external knowledge or make assumptions. If something is not in the context, do not write about it. Format using markdown headers."),
        ("user", "Topic: {topic}\n\nObjectives:\n{objectives}\n\nContext:\n{context}\n\nFeedback (if any): {feedback}")
    ])
    chain = prompt | llm
    feedback = state.get("review_feedback", "None")
    res = chain.invoke({
        "topic": state["topic"], 
        "objectives": state["objectives"], 
        "context": state["context"],
        "feedback": feedback
    })
    return {"sections": res.content}

def generate_quiz(state: CourseState) -> CourseState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Quiz Generator. Create 3 multiple choice questions to test the learner on the provided content sections. The questions and answers must be strictly grounded in the provided content. Do NOT use external knowledge. 

You MUST format each question exactly like this template:

**Question [Number]:** [Question text]
- A) [Option A]
- B) [Option B]
- C) [Option C]
- D) [Option D]

**Correct Answer:** [Correct Option Letter]

Do NOT output options in a single paragraph. Do NOT output a standalone row of letters. Follow the template exactly."""),
        ("user", "Content Sections:\n{sections}")
    ])
    chain = prompt | llm
    res = chain.invoke({"sections": state["sections"]})
    return {"quizzes": res.content}

def write_summary(state: CourseState) -> CourseState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Summarizer. Write a brief, inspiring summary of the course content based ONLY on the provided content sections. Do NOT use external knowledge."),
        ("user", "Content Sections:\n{sections}")
    ])
    chain = prompt | llm
    res = chain.invoke({"sections": state["sections"]})
    return {"summary": res.content}

def review_content(state: CourseState) -> CourseState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Reviewer. Verify that the content sections cover the objectives well and contain NO external knowledge outside the context. If good, respond exactly with 'APPROVED'. If bad or if it uses external knowledge, provide 1 sentence of feedback."),
        ("user", "Objectives:\n{objectives}\n\nContent:\n{sections}")
    ])
    chain = prompt | llm
    res = chain.invoke({"objectives": state["objectives"], "sections": state["sections"]})
    
    is_approved = "APPROVED" in res.content.upper()
    current_count = state.get("revision_count", 0)
    
    if is_approved or current_count >= 1:
        return {"review_feedback": None, "revision_count": current_count + 1}
    else:
        return {"review_feedback": res.content, "revision_count": current_count + 1}

def should_continue(state: CourseState):
    if state.get("review_feedback") is None:
        return "generate_quiz"
    return "write_content"

def check_relevance(state: CourseState):
    if "ERROR: UNRELATED" in state.get("objectives", ""):
        return "end"
    return "continue"

# Build Graph
workflow = StateGraph(CourseState)

workflow.add_node("extract_context", extract_context)
workflow.add_node("design_curriculum", design_curriculum)
workflow.add_node("write_content", write_content)
workflow.add_node("generate_quiz", generate_quiz)
workflow.add_node("write_summary", write_summary)
workflow.add_node("review_content", review_content)

workflow.set_entry_point("extract_context")
workflow.add_edge("extract_context", "design_curriculum")

workflow.add_conditional_edges(
    "design_curriculum",
    check_relevance,
    {
        "end": END,
        "continue": "write_content"
    }
)

workflow.add_edge("write_content", "review_content")

workflow.add_conditional_edges(
    "review_content",
    should_continue,
    {
        "generate_quiz": "generate_quiz",
        "write_content": "write_content"
    }
)

workflow.add_edge("generate_quiz", "write_summary")
workflow.add_edge("write_summary", END)

app = workflow.compile()

def generate_course_content(topic: str, folder_path: str):
    initial_state = {
        "topic": topic,
        "folder_path": folder_path,
        "context": "",
        "objectives": "",
        "sections": "",
        "quizzes": "",
        "summary": "",
        "review_feedback": None,
        "revision_count": 0
    }
    final_state = app.invoke(initial_state)
    return final_state

import json

def generate_course_stream(topic: str, folder_path: str):
    initial_state = {
        "topic": topic,
        "folder_path": folder_path,
        "context": "",
        "objectives": "",
        "sections": "",
        "quizzes": "",
        "summary": "",
        "review_feedback": None,
        "revision_count": 0
    }
    
    yield json.dumps({"status": "Reading and extracting context from reference documents...", "step": "extract_context"})
    
    for event in app.stream(initial_state):
        for node, state_update in event.items():
            initial_state.update(state_update)
            
            if node == "extract_context":
                yield json.dumps({"status": "Designing curriculum & learning objectives (Curriculum Designer)...", "step": "design_curriculum"})
            elif node == "design_curriculum":
                yield json.dumps({"status": "Writing detailed course content (Content Writer)...", "step": "write_content"})
            elif node == "write_content":
                yield json.dumps({"status": "Reviewing content alignment and depth (Reviewer)...", "step": "review_content"})
            elif node == "review_content":
                if initial_state.get("review_feedback") is not None:
                    yield json.dumps({"status": "Revising course content based on reviewer feedback...", "step": "write_content"})
                else:
                    yield json.dumps({"status": "Generating multiple-choice questions (Quiz Generator)...", "step": "generate_quiz"})
            elif node == "generate_quiz":
                yield json.dumps({"status": "Writing course summary...", "step": "write_summary"})
            elif node == "write_summary":
                yield json.dumps({"status": "Formatting and finalizing...", "step": "done"})

    yield json.dumps({
        "status": "Complete",
        "step": "complete",
        "result": {
            "objectives": initial_state.get("objectives", ""),
            "sections": initial_state.get("sections", ""),
            "quizzes": initial_state.get("quizzes", ""),
            "summary": initial_state.get("summary", "")
        }
    })

