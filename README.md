## About the project
This repository contains a **Geospatial AI Assistant**. The project aims to simplify the complex process of finding suitable land plots regarding user criteria. 
Instead of filtering through endless listings manually, users can describe their needs using natural language and wait for AI agent response.

## Data sources 
All land plot's data was taken from the **Belarusian National Cadastral Agency**. Dataset includes unused land plots placed by district executive committees with coverege in Minsk district.

## 🛠 Tech stack
### Backend 
- **Python** - Main backend logic using FastAPI
- **LangChain** - Agent building ang chain execution


### Frontend
- **TypeScript + React+** — Type-safe frontend development
- **Node.js** — Runtime environment for frontend services

### Model & AI
- **Hermes-2-Pro-Mistral-7B** — Main reasoning model (quantized Q5_K_M)
- **Sentence Transformers** — Text embeddings for semantic search

### Data
- **Qdrant** - Vector store for semantic search across land plots dataset
- **PostGIS** - Geospatial store for additional geospatial queries 
