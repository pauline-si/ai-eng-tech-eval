# Umain's AI technical evaluation challenge

## Application description
This technical evaluation application contains a frontend client (React + Vite) and a backend service (FastAPI) packed in multi-container application that can be easily run using Docker Compose.

This app is your smart AI assistant for chatting, managing tasks, and using voice commands. You can talk to it or type your questions, and it will respond with helpful answers. If you mention things you need to do, the app can turn them into a to-do list for you. You can also use your voice to interact, and the app can talk back to you.

Additionally, this application contains LLM tools that allow **interaction with some of Shopify's API endpoints (e.g. orders handling)**. You can prompt the assistant to help you complete some Shopify tasks!

## Running with Docker Compose (Recommended for Development)

This is the recommended way to run both applications for development, as it handles dependencies and networking.

1.  **Prerequisites:**
    *   Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (which includes Docker Compose).

2.  **Build and Run:**
    Navigate to the root directory of the project (`/Users/markschellhas/apps/tech-eval/`) in your terminal and run:
    ```bash
    docker-compose up --build
    ```
    *   The `--build` flag is only needed the first time or when you change `Dockerfile`s, dependencies (`package.json`, `requirements.txt`), or copy new static files into an image. For subsequent runs, `docker-compose up` is usually sufficient.
    *   The client will be available at `http://localhost:5173`.
    *   The service will be available at `http://localhost:8000`.
    *   Hot reloading is enabled for both client and service. Changes to your local source code will be reflected automatically.

3.  **Stopping the Applications:**
    Press `CTRL+C` in the terminal where `docker-compose up` is running. To remove the containers, you can run:
    ```bash
    docker-compose down
    ```

## Manual Startup (Alternative)

### Starting frontend client:
To start the client:
1. `cd client`
2. `npm install` (if you haven't already or dependencies changed)
3. `npm run dev`

### Start backend service
To start the backend:
1. `cd service`
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. `pip install -r requirements.txt` (if you haven't already or dependencies changed)
4. `fastapi dev main.py`

---
*The `start_apps.sh` script provides a way to run these manual commands concurrently, primarily for macOS.*


# Documentation

## Project structure
The project in this directory follows this structure:
```
.
├── .gitignore
├── README.md
├── client
│   ├── ...
│   ├── public
│   │   └── ...
│   ├── src
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── assets
│   │   │   └── react.svg
│   │   ├── components
│   │   │   ├── ChatFeed.jsx # Component for showing messages
│   │   │   ├── ChatInput.jsx # Prompt-input window
│   │   │   ├── TodoList.jsx # To-do list component
│   │   │   └── VoiceInput.jsx # Voice input button
│   │   ├── index.css
│   │   └── main.jsx # Main application page
│   ├── tailwind.config.js
│   └── vite.config.js
├── docker-compose.yml # Compose file for managing the app's containers
├── service
│   ├── .dockerignore
│   ├── .env
│   ├── .gitignore
│   ├── Dockerfile
│   ├── api
│   │   └── chat.py # Chat router for backend service
│   ├── config.py
│   ├── main.py # The FastAPI server (e.g. middleware, router inclusion etc.)
│   ├── models # Request/Response models
│   │   └── chat.py
│   ├── requirements.txt 
│   ├── services # Services layer
│   │   ├── __init__.py
│   │   ├── function_schemas.py # Schemas for function tools of the LLM
│   │   └── llm_service.py # The OpenAI LLM service that handles interactions with OpenAI's APIs
│   └── utils
│       ├── prompt_builder.py # System prompt and prompt builder
│       └── shopify_utils.py # Tool-functions for interactions with the Shopify store
└── start_apps.sh # Bash script to manually start the application without Docker-Compose
```

### The React frontend
The frontend is built using React and involves several components under [./client/src/components](./client/src/components/) like:
- A todo list
- A chat feed
- A prompt window
- A voice input button

### The backend service for interaction with a conversation agent using OpenAI's models
The backend service, which interacts with the front-end code to update the UI and populate the chat feed with LLM generated responses is built with FastAPI. The endpoints can be found under [./service/api](./service/api/) :
- [chat.py](./service/api/chat.py):  A router including all the chat-related endpoints of the service

This application also uses **Pydantic models** for request/response typings. The models can be found [here](./service/models/).


### Backend service environment variables and configuration
The backend service makes use of a few environment variables passed during build. To configure the application **please add your own `.env` file under `./service/.env`. The necessary environment variables needed can be also found in our Pydantic Settings model [here](./service/config.py).


### Enhancing the LLM with tools for interaction with Shopify's API
Finally,as mentioned the LLM's capabilities are enhanced using custom tools for interaction with Shopify's API. The python functions with the tools implementation can be found [here](./service/utils/shopify_utils.py) and their OpenAI schema definitions can be found [here](./service/services/function_schemas.py).


## Coding challenge: Instructions for candidate
Welcome to Umain’s AI coding challenge!

Take some time to get to know the application’s structure and how the frontend and backend work together. Once you’re comfortable, your task is to add new features and put your own unique spin on the app. We’re excited to see your ideas and improvements!

Your main tasks for this challenge are the following but feel free to add your own touch!

**Task list**

- **Resolve a minor (but frustrating) front-end issue**:
There’s a subtle bug in the [client](./client/) code affecting the toggle functionality of the todo list buttons. When you mark a single task as done, the status of all tasks changes instead of just the selected one. Can you find and fix the problem?

- **Extend Shopify Integration**:
Implement functionality to add, remove, and list products from Shopify. When a product is added to the to-do list, **also display its image in the front-end**.

- **Add memory capabilities to the conversational chatbot**:
Update the existing [LLM Service](./service/services/llm_service.py) class so that the system maintains conversational context and memory across interactions (e.g. the chatbot should have awareness of previous messages exchanged with the user)

- **Think about a possible database integration**:
If we move from in-memory storage to a database, what would the database schema look like? Please think of a suitable schema for this use case. P.S. You don't need to implement the actual database integration for this challenge!

- **How could our backend service be improved?**:
It's time for some code reviewing! Think about how would you improve the architecture, structure, or code of the FastAPI backend service.

- **Testing**:
How should we test this system? Please write a unit test to demonstrate your approach.
