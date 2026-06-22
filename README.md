# Multi-Agent AI Course Generator 🤖📚

An intelligent, full-stack educational course creator that leverages state-of-the-art Multi-Agent workflows to generate deeply grounded, structured learning content from local source documents (PDFs and Text files). 

## Features ✨

- 🚀 **Agentic Reflection Architecture**: Orchestrated via LangGraph, dividing work among specialized nodes (Curriculum Designer, Content Writer, Quiz Generator, Content Reviewer) featuring a quality control evaluation cycle loop.
- ⚡ **Asynchronous Streaming (SSE)**: Built with FastAPI `StreamingResponse` using Server-Sent Events (`text/event-stream`) to provide instant, real-time stage progress updates straight to the UI.
- 📁 **Local Document Grounding (RAG)**: Extracts binary PDF data and plain text using `PyMuPDF` (`fitz`), securely enforcing strict context boundaries to completely eliminate LLM hallucinations.
- 🎛️ **Native Native System Interoperability**: Seamlessly triggers native operating system directory selectors on-the-fly via a dedicated backend Tkinter workspace intercept route.
- ⚛️ **Modern Responsive UI**: Built with a decoupled **React 19 + Vite** frontend containing real-time asset parsing configurations via `react-markdown`.
- 🔋 **Cost-Optimized & Fast**: Fueled by **Llama 3.1 8B** via **Groq Cloud LPUs**, bounded cleanly with intelligent token budget constraints to comfortably operate inside strict free-tier consumption limits.

## Architecture & System Data Flow ✨

```mermaid
graph TD
   %% Frontend Layer
   subgraph Frontend [Client Layer: React 19 + Vite]
      UI[User Interface] -->|1. Submit Topic & Folder Path| API_Call[HTTP POST Request]
   end

   %% Backend Gateway Layer
   subgraph Backend [Backend Server Gateway: FastAPI]
      API_Call -->|2. Receive Payload| CORS[CORS Settings & Path Validation]
      CORS -->|3. Establish Connection| SSE[Server-Sent Events Stream]
   end

   %% Multi-Agent Core Layer
   subgraph AI_Engine [Multi-Agent Core: LangGraph Engine]
      SSE -->|4. Invoke Workflow| Node1[1. Extract Context Node <br> Reads PDFs/TXT via PyMuPDF]
      Node1 --> Node2[2. Curriculum Designer <br> Validates Relevancy]
      
      %% Relevance Check Conditional
      Node2 -->|If Unrelated| END_Early[Abrupt Termination]
      Node2 -->|If Related| Node3[3. Content Writer Agent <br> Drafts Course Material]
      
      %% Reflection Loop Routing
      Node3 --> Node_Rev[Reviewer Agent <br> Evaluates Content Depth]
      Node_Rev -->|If Rejected: Loops Feedback| Node3
      
      %% Finalizing Pipeline
      Node_Rev -->|If Approved| Node4[4. Quiz Generator <br> Crafts Grounded MCQs]
      Node4 --> Node5[5. Summarizer Agent <br> Generates Final Takeaway]
      Node5 -->|6. Compile Output| Graph_End([Workflow Complete])
   end

   %% Response Delivery
   Graph_End -->|7. Push Step State Events| SSE
   SSE -->|8. Stream text/event-stream| UI
   UI -->|9. Render Output| MD[React Markdown View Cards]

   %% Styling Elements
   style Frontend fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff
   style Backend fill:#111827,stroke:#10b981,stroke-width:2px,color:#fff
   style AI_Engine fill:#1e1b4b,stroke:#8b5cf6,stroke-width:2px,color:#fff
   style END_Early fill:#991b1b,stroke:#ef4444,color:#fff

## Quick Start 🚀

### Prerequisites

- Python 3.10+
- Node.js v22+
- A Groq Cloud API Key

### Step 1: Set Up the Backend Engine

1. Navigate to the backend folder:
```bash
   cd backend


Create and activate a virtual environment:

Bash 

python -m venv venv
   # On Windows (PowerShell):
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   venv\Scripts\activate

Install dependencies:

Bash
   pip install -r requirements.txt

Create a .env file in the root of the backend/ directory and add your key:

Code snippet
   GROQ_API_KEY=your_actual_groq_api_key_here

Spin up the FastAPI server:

Bash
   python main.py

The server will boot up locally at http://localhost:8000.

Step 2: Set Up the Frontend Interface
Open a new terminal window/tab and navigate to the frontend folder:

Bash
   cd frontend

Install the node modules:

Bash
   npm install

Boot up the Vite web application:

Bash
   npm run dev

Click the local server link displayed in your terminal (typically http://localhost:5173/) to launch the generator!

Project File Mapping

course-generator/
├── backend/
│   ├── graph.py             # LangGraph workflow, Agents, & State Machine
│   ├── main.py              # FastAPI server, endpoints, and SSE Generator
│   ├── requirements.txt     # Python system packages
│   └── .env                 # Environment configurations (Hidden)
├── frontend/
│   ├── src/                 # React UI layout components 
│   ├── package.json         # JavaScript modules & build tracking
│   ├── vite.config.js       # Vite development bundler configuration
│   └── eslint.config.js     # Code linter standards configuration
└── .gitignore               # Keeps secrets (.env) out of GitHub


Behind the Code: Deep Technical Core
1. Centralized State Engine (graph.py)
The collective data parameters passing between independent agents are controlled by a fixed state footprint utilizing Python's TypedDict:

Python
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

2. Guardrails & Reflection Mechanics
To guarantee absolute content factual accuracy, the system leverages conditional routing paths within the workflow configuration:

Python
workflow.add_conditional_edges(
    "review_content",
    should_continue,
    {
        "generate_quiz": "generate_quiz",
        "write_content": "write_content"  # Re-routes backwards to rewrite if feedback triggers
    }
)

3. Server-Sent Events (SSE) Interface (main.py)
The backend provides immediate step feedback metrics to the client browser by parsing yielding stream updates over a dedicated HTTP channel connection:

Python
@app.post("/generate")
async def generate_course(req: GenerationRequest):
    def event_generator():
        for message in generate_course_stream(req.topic, req.folder_path):
            yield f"data: {message}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

Performance & Token Budget Strategies ⚡
Context Optimization: To ensure the engine never breaks or drops due to strict rate limitations, source text inputs are automatically bounded to a strict 12,000 character maximum limit, retaining complete structural focus inside a tight, cost-effective processing loop.

Deterministic Prompt Alignment: Agent systems operate explicitly at a temperature=0.2 setting, forcing the structural reasoning weights of Llama-3.1 to generate analytical educational steps over arbitrary creative interpretations.

License 📄
This project is licensed under the MIT License - see your own preferences for commercial scalability details.

Built with ❤️ using LangGraph, FastAPI, and React 19

