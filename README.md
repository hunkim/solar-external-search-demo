# Solar Chat Test App

A simple Streamlit chat interface for the Solar LLM API with streaming support and optional external search integration.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables:**
    Edit `.env.test` and add your API keys:
    ```ini
    UPSTAGE_API_KEY=your_upstage_api_key_here
    EXTERNAL_SEARCH_URL=https://your-search-api-url.com/search/your_collection_name
    EXTERNAL_SEARCH_API_KEY=your_external_search_api_key
    ```

## Running the App

```bash
streamlit run app.py
```

## Features

*   **Streaming Responses:** Real-time token streaming from Solar API.
*   **External Search:** Optional integration with a custom search backend (configured via `.env.test`).
*   **Developer Tools:** View the equivalent `curl` command for the current configuration in the sidebar.
