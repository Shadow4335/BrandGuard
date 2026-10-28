# AI, services, datasets and libraries

## AI and external services

| Service | Purpose | Data it receives |
|---|---|---|
| Google Gemini API (default `LLM_PROVIDER=gemini`, model from `LLM_MODEL`, e.g. `gemini-2.5-flash`) | Layer B: tone and claim-vs-fact review, rewrite suggestions | The content text under review and the retrieved brand-source excerpts, per review. Only when `LLM_API_KEY` is set and `MOCK_LLM=false` |
| Gemini embeddings (`gemini-embedding-001`, 768 dims) | Retrieval of relevant source chunks | Source chunks (when sources are added) and sentences of the content under review |
| Anthropic / OpenAI (optional adapters, `LLM_PROVIDER=anthropic\|openai`) | Alternative LLM providers | Same as Gemini |
| Supabase (Postgres, Auth, Storage, pgvector) | Data, sign-in, private files, vector search | All application data |
| Vercel | Hosts the Next.js frontend | Static assets, page requests |
| Render | Hosts the FastAPI backend (Docker) | API requests |

With no LLM key, nothing is sent to any AI provider; an offline heuristic runs instead.

## Datasets and templates
No external datasets and no model training. The GlowLeaf Naturals brand, sources, facts and 30 days of history are **fictional and generated** (`backend/app/seed_data.py`). Regulatory summaries (CCPA 2022 misleading-advertisement guidelines, ASCI influencer guidelines, ASCI code, Drugs and Magic Remedies Act) are short paraphrases with a link to the official source: consumeraffairs.nic.in, ascionline.in, indiacode.nic.in. They are not legal advice and should be checked against the official text. UI built with Tailwind; shadcn-style conventions, no copied templates.

## Backend libraries (Python)
FastAPI, uvicorn, pydantic v2, supabase-py, python-multipart, httpx, python-dotenv, PyYAML, PyMuPDF (PDF), python-docx (DOCX), pytesseract + **Tesseract OCR** (system package), Pillow (images, colour analysis), BeautifulSoup4 (HTML), rapidfuzz (fuzzy terminology), google-genai (Gemini), pytest, pytest-asyncio.

## Frontend libraries (npm)
Next.js, React, Tailwind CSS, @supabase/supabase-js, @supabase/ssr, Recharts (charts), react-diff-viewer-continued (version diffs), lucide-react (icons), clsx, tailwind-merge.
