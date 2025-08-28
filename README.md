# HR Agent with MCP Integration

An **AI-powered HR conversational agent** built on top of **LangGraph**, **MCP (Model Context Protocol)**, and **Hugging Face LLMs**.  
This project demonstrates a **production-grade orchestration layer** where user inputs are interpreted as intents, clarified for missing arguments, executed via MCP tools, and returned in natural conversational form.

---

## Comparison with AI-enabled APPS

| Aspect                | **This Project (AI-Native with MCP)**                                                                              | **Typical AI-Enabled HR App**                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **Architecture**      | Orchestrated via **LangGraph** with explicit states (detect → clarify → execute → respond). Modular, future-proof. | AI features are “bolted on” to an existing HR app. Often ad-hoc integration, not core design. |
| **Tool Integration**  | Uses **MCP protocol** → tools are schema-driven, discoverable, reusable.                                           | Custom API calls, usually hard-coded per feature.                                             |
| **Conversation Flow** | Multi-turn, **clarifies missing info** automatically, maintains session history.                                   | Typically one-shot queries, fails silently or shows error if info missing.                    |
| **Extensibility**     | New HR services = just add new MCP tool; orchestrator auto-picks it up.                                            | Requires custom coding and wiring per new feature.                                            |
| **Response Quality**  | Tool results are passed through **LLM rephraser**, producing natural conversational Indonesian.                    | Usually template-based responses, less natural.                                               |
| **DevOps**            | Fully **Dockerized**, runs anywhere, uses `.env` config.                                                           | Requires manual setup, often environment-specific.                                            |
| **Future Potential**  | Foundation for **Agentic HR systems** (autonomous workflows, scheduling).                                          | Limited to point solutions (chatbot Q\&A, single API lookup).                                 |


## 🏗️ Architecture


- **Intent Detection** → Hugging Face model maps free-text input into structured intents + arguments.  
- **Clarifier** → Compares detected args against MCP tool schemas; asks user for missing fields.  
- **MCP Tools** → Executes business logic (leave request, payroll lookup, leave status).  
- **Response Builder** → Converts raw JSON results into polite, human-like HR responses in Indonesian.  
- **Fallback Layer** → Handles greetings and out-of-scope queries naturally.  
- **LangGraph Workflow** → Provides stateful, multi-turn flow (`detect → clarify → execute → respond`).  
- **Session Memory** → Tracks conversation history, tool calls, and clarifications.

---

## ✨ Features

- **End-to-end HR assistant**
  - Apply for leave (`leave_request`)
  - Check payroll details (`payroll_lookup`)
  - View leave balances (`leave_status`)
- **Multi-turn conversations**
  - Remembers session history and clarifications
  - Iteratively collects missing arguments
- **MCP integration**
  - Tools are exposed via MCP server
  - Client communicates via stdio and normalizes results
- **Resilient orchestration**
  - Detects invalid intents and routes to fallback
  - Supports multiple intents in one input
- **Fallback & greetings**
  - Natural greetings (“halo”, “pagi”, etc.)
  - Polite fallback responses for out-of-scope queries
- **Production-grade design**
  - Strong logging + tracing
  - Modular class-based structure
  - Schema-driven validation (Pydantic)

---

## 💡 Benefits

- **Human-like HR assistant**  
  Employees can interact naturally in Indonesian, and the system adapts to incomplete or unclear inputs.  

- **Scalable orchestration**  
  LangGraph makes it easy to extend new tools/intents without rewriting the agent logic.  

- **MCP alignment**  
  Demonstrates how MCP standardizes tool discovery and execution across different domains.  

- **Resilience in real use**  
  - Handles missing args gracefully  
  - Provides clarifications instead of failing  
  - Responds politely even for off-topic chat  

- **Developer-friendly**  
  - Code is modular (`detector`, `orchestrator`, `planner`, `clarifier`, `response_builder`, `mcp_client`, `tools`)  
  - Logging everywhere (`[TRACE]`, `[MCP-CLIENT]`, `[MULTI-INTENT]`)  
  - Easy to extend for new HR functions  

---

## 🚀 Getting Started

### Requirements
- Python 3.11
- Dependencies listed in `requirements.txt` (LangGraph, MCP SDK, Hugging Face client, etc.)

### Run MCP server + agent
```bash
# Start the server
uvicorn app.main:app --reload
```

### Run using Docker 
This project is fully containerized. You can run it immediately without installing Python or dependencies manually.
#### 1. Clone the repository
```bash
git clone https://github.com/t91jauhari/HRAIAGENT_MCP.git
cd HRAIAGENT_MCP

cp .env.example .env

fill the token value HF_TOKEN=[xxxx]

docker-compose up --build 

```

### Example request
```json
POST /chat
{
    "session_id":"1",
    "message":"cek gaji saya donk , terus sisa jumlah cuti saya berapa ya "
}
```


---


### Sample full response from AGENT and MCP tools 
```json
{
    "trace_id": "c191915c-2d0a-43c0-8226-54accdea3e51",
    "session_id": "1",
    "intents": [
        {
            "name": "payroll_lookup",
            "confidence": 0.95,
            "args": {
                "employee_id": null
            }
        },
        {
            "name": "leave_status",
            "confidence": 0.8,
            "args": {
                "employee_id": null
            }
        }
    ],
    "results": {},
    "clarifications": [
        {
            "intent": "payroll_lookup",
            "missing": [
                "employee_id"
            ]
        },
        {
            "intent": "leave_status",
            "missing": [
                "employee_id"
            ]
        }
    ],
    "assistant_response": "Maaf, saya masih perlu beberapa informasi lebih lanjut untuk memproses permintaan Anda. Untuk memastikan bahwa saya dapat membantu Anda dengan benar, dapatkah Anda memberitahu saya ID karyawan yang Anda cari informasi tentang?",
    "history": {
        "session_id": "1",
        "created_at": "2025-08-28T19:55:51.456430",
        "messages": [
            {
                "id": "1ba586f8-bd7f-48d3-9c35-ab598680a80d",
                "time": "2025-08-28T19:55:59.199199",
                "role": "user",
                "content": "cek gaji saya donk , terus sisa jumlah cuti saya berapa ya "
            },
            {
                "id": "44c0aa83-f0be-4449-9695-954a1af5f055",
                "time": "2025-08-28T19:56:00.871017",
                "role": "assistant",
                "content": "Maaf, saya masih perlu beberapa informasi lebih lanjut untuk memproses permintaan Anda. Untuk memastikan bahwa saya dapat membantu Anda dengan benar, dapatkah Anda memberitahu saya ID karyawan yang Anda cari informasi tentang?"
            }
        ],
        "intents": [
            {
                "id": "7bbd09fd-3e30-42ba-a40c-15d784a5fb11",
                "time": "2025-08-28T19:55:59.199276",
                "intents": [
                    {
                        "name": "payroll_lookup",
                        "confidence": 0.95,
                        "args": {
                            "employee_id": null
                        }
                    },
                    {
                        "name": "leave_status",
                        "confidence": 0.8,
                        "args": {
                            "employee_id": null
                        }
                    }
                ]
            }
        ],
        "tool_calls": [],
        "clarifications": [
            {
                "id": "7ba983a9-99db-4b86-a51b-5692c5288d55",
                "time": "2025-08-28T19:55:59.225922",
                "intent": "payroll_lookup",
                "missing": [
                    "employee_id"
                ]
            },
            {
                "id": "3f2a388e-ad03-4e93-a057-04391dc140fd",
                "time": "2025-08-28T19:55:59.248472",
                "intent": "leave_status",
                "missing": [
                    "employee_id"
                ]
            }
        ]
    }
}

```

## 🔧 Project Structure

```
app/
 ├── graph/
 │   ├── agent_graph.py       # LangGraph workflow
 │   ├── orchestrator.py      # Orchestrator entrypoint
 │   ├── multi_intent_planner.py
 │   ├── response_builder.py
 │   ├── clarifier.py
 │   ├── mcp_client.py
 │   └── schema_utils.py
 ├── intent/
 │   ├── detector.py
 │   ├── hf_client.py
 │   └── prompts.py
 ├── memory/
 │   └── session_store.py
 ├── mcp_server/
 │   ├── server.py
 │   ├── hr_tools.py          # HR MCP tools
 │   └── models.py
 └── main.py                  # FastAPI entrypoint
```

---

## 🧩 Extending the Agent

- Add new HR tools in `mcp_server/hr_tools.py` with proper `Input` / `Output` Pydantic models.  
- Register in `list_tools()`.  
- Intent system prompt will auto detect changes of registered tools from MCP server
- Orchestrator + planner handle the rest automatically.

---

## 📈 Roadmap

- 

---
