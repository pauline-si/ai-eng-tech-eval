# AI-Powered Shopify Assistant (Technical Evaluation)

A React + FastAPI assistant that manages Shopify products through OpenAI, remembers past actions using hybrid memory, and displays image-rich tasks with voice/chat input.

---

## 1. Setup & Configuration

### Docker Compatibility Fix

On my Intel Mac, I encountered `exec format error` when building Alpine-based containers.

**Fixes (in `Dockerfile` and `docker-compose.yml`):**
- Switched to Debian-based images (`node:20-bullseye`, `python:3.11-slim-buster`)
- Set `platform: linux/amd64` in `docker-compose.yml`

This made the app run successfully on my local setup.

---

### Environment Variables

Configured `.env` inside `./service/` (excluded from Git). Includes:
- `OPENAI_API_KEY`
- `SHOPIFY_API_KEY`, etc.

Loaded securely using Pydantic (`config.py`).



---
### Task 1 - Fix React Toggle Bug

**Bug:** Marking one task toggled all.

**How I Realized:** Console showed this warning:
> "Each child in a list should have a unique 'key' prop."

**Fix:**
- In `App.jsx`, added a unique ID to each todo using `crypto.randomUUID()` when mapping backend data.
- In `TodoList.jsx`, replaced `Date.now()` with `crypto.randomUUID()` when manually adding tasks.

 React now tracks each todo item correctly.

---

### Task 2 – Shopify Integration + Product Image Display

#### OpenAI + Shopify Integration

- Implemented functions in `shopify_utils.py`: `add_product`, `remove_product`, `list_products`
- Defined function schemas in `function_schemas.py`
- Registered functions in `llm_service.py` under `self.fn_map`


#### Image in Frontend (`TodoList.jsx`)
```jsx
{todo.image && <img src={todo.image} className="w-10 h-10 object-cover rounded mr-3" />}
```

- Prevented duplication in `App.jsx` by comparing IDs before inserting.

---

### Task 3 – Add Memory Capabilities (Hybrid Memory)

#### What I Did

- In `llm_service.py`, created a global `memory` dictionary and `message_history` list.
```python
memory = {}
message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
```

- Stored last added/deleted product:
```python
if func_name == "add_product":
    self.memory["last_added_product"] = result
```

- Created `prompt_builder.py` to build smarter prompts:
```python
if memory.get("last_added_product"):
    prompt += f"\nLast product added: {memory['last_added_product']['title']}"
```

 GPT can now understand vague follow-ups like “delete it.”

---

### Task 4 – Database Schema Design

Full schema (SQLite, 6 tables):

#### `users`
```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `customers`
```sql
CREATE TABLE customers (
  id TEXT PRIMARY KEY,
  name TEXT,
  email TEXT,
  address TEXT,
  city TEXT,
  postal_code TEXT,
  country TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `products`
```sql
CREATE TABLE products (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  price REAL,
  image_url TEXT,
  source TEXT CHECK(source IN ('chatbot', 'shopify')) DEFAULT 'chatbot',
  created_by_user_id TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);
```

#### `orders`
```sql
CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  total_amount REAL,
  source TEXT,
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

#### `order_items`
```sql
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  quantity INTEGER DEFAULT 1,
  price REAL,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

#### `chat_messages`
```sql
CREATE TABLE chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  role TEXT CHECK(role IN ('user', 'assistant')),
  message TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

###  Task 5 – Backend Code Review & Improvements

#### What I Improved

1. **Split logic for clarity**
   - Moved prompt formatting from `llm_service.py` → `prompt_builder.py`
   - Example:
```python
# In prompt_builder.py
def build_prompt(message, todo_list, memory):
    ...
```

2. **Used SOLID principles**
   - **SRP**: `llm_service.py` only handles LLM logic; prompt logic is elsewhere
   - Easier to debug and test

---

#### Suggested Improvements

**1.Add a unique user ID**
- Track memory per `user_id` in `memory` or DB (not done yet)
- Required for multi-user scaling

**2. Add a real database**
- Replace in-memory `memory` with persistent SQLite/Postgres

Could also explore **Neo4j (graph DB)** + **RAG** architecture for semantic memory and deeper relationship tracking


**3. Add webhook support (Shopify → app)**
- Currently, our app only sends requests to Shopify.
- With webhooks, Shopify could notify our backend automatically when something happens (e.g. a product is added/deleted manually).
- This would improve memory sync and reduce the need for polling.


**4. Add logging**
- Log incoming requests, GPT calls, errors
- Add in `chat.py`:
```python
@app.post("/chat")
async def chat(...):
    logger.info(f"Incoming prompt: {prompt}")
```

**5. Prompt suggestions in frontend**
- Add clickable preset prompts:
```json
["Add product Ballet Shoes", "List last 3 products", "Delete last added item"]
```
- Store in JSON or expose via `/prompts` endpoint
- Speeds up testing, avoids typos, improves UX

---

### Task 6 – Testing Strategy & Unit Test

####  Test Strategy

1. **Unit tests**: Prompt formatting, memory logic
2. **Integration tests**: `/chat` route + GPT (mocked)
3. **E2E**: Optional future scope

#### Example Test

```python
from services.prompt_builder import build_prompt

def test_build_prompt_with_memory():
    todo_list = [{"text": "Fix bug", "status": "pending"}]
    memory = {
        "last_added_product": {"title": "Tutu", "id": "123"},
        "last_deleted_product": {"title": "Shoes", "id": "456"}
    }
    prompt = build_prompt("What did I just delete?", todo_list, memory)

    assert "Tutu" in prompt
    assert "Shoes" in prompt
    assert "User message: What did I just delete?" in prompt
```

---

