#!/usr/bin/env python3
"""
Streamlit test app for simple chat with Solar LLM API
Uses streaming and reads environment variables from .env.test
"""

import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env.test
load_dotenv(".env.test")

# Configuration
SOLAR_SEARCH_URL = "https://solar-web-search.cosmic.upstage.ai/v1/chat/completions"
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
EXTERNAL_SEARCH_BASE_URL = os.getenv("EXTERNAL_SEARCH_BASE_URL")
EXTERNAL_SEARCH_COLLECTION_NAME = os.getenv("EXTERNAL_SEARCH_COLLECTION_NAME")
EXTERNAL_SEARCH_API_KEY = os.getenv("EXTERNAL_SEARCH_API_KEY")

# Streamlit page config
st.set_page_config(page_title="Solar Chat Test", page_icon="💬", layout="wide")

# Header with title and new chat button
col1, col2 = st.columns([6, 1])
with col1:
    st.title("💬 Solar Chat Test - Streaming")
with col2:
    st.write("")  # Spacing
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Check if API key is configured
if not UPSTAGE_API_KEY:
    st.error("❌ UPSTAGE_API_KEY not found in .env.test")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        # Timing variables
        start_time = time.time()
        first_token_time = None
        total_time = None
        full_response = ""
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {UPSTAGE_API_KEY}"
        }
        
        data = {
            "model": "solar-pro2-search",
            "messages": [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ],
            "stream": True
        }
        
        # Add external search options if configured
        if EXTERNAL_SEARCH_BASE_URL and EXTERNAL_SEARCH_COLLECTION_NAME and EXTERNAL_SEARCH_API_KEY:
            data["web_search_options"] = {
                "search_context_size": "medium",
                "external_search_engine_only": True,
                "servers": [
                    {
                        "url": f"{EXTERNAL_SEARCH_BASE_URL.rstrip('/')}/search/{EXTERNAL_SEARCH_COLLECTION_NAME}",
                        "key": EXTERNAL_SEARCH_API_KEY
                    }
                ]
            }
        
        # Create placeholders for response and timing
        message_placeholder = st.empty()
        timing_placeholder = st.empty()
        
        try:
            # Make streaming request
            with requests.post(
                SOLAR_SEARCH_URL, 
                headers=headers, 
                data=json.dumps(data), 
                stream=True
            ) as response:
                
                if response.status_code != 200:
                    st.error(f"Error {response.status_code}: {response.text}")
                    st.stop()
                
                # Process streaming response
                for line in response.iter_lines():
                    # Show spinner while waiting for first token
                    if first_token_time is None:
                        message_placeholder.markdown("🔍 *Searching and thinking...*")
                    
                    if line:
                        line_text = line.decode('utf-8')
                        
                        # Skip empty lines and "data: [DONE]"
                        if not line_text.strip() or line_text.strip() == "data: [DONE]":
                            continue
                        
                        # Parse SSE format (data: {...})
                        if line_text.startswith("data: "):
                            json_str = line_text[6:]  # Remove "data: " prefix
                            
                            try:
                                chunk = json.loads(json_str)
                                
                                # Extract content from chunk
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    
                                    if content:
                                        # Record time to first token
                                        if first_token_time is None:
                                            first_token_time = time.time() - start_time
                                        
                                        full_response += content
                                        message_placeholder.markdown(full_response + "▌")
                            
                            except json.JSONDecodeError:
                                continue
                
                # Calculate total time
                total_time = time.time() - start_time
                
                # Display final response
                message_placeholder.markdown(full_response)
                
                # Display timing information
                if first_token_time and total_time:
                    timing_placeholder.caption(
                        f"⏱️ Time to first token: {first_token_time:.2f}s | Total time: {total_time:.2f}s"
                    )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Sidebar with configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Developer Tools - cURL command
    st.subheader("👨‍💻 Developer Tools")
    
    # Build curl command based on configuration
    if EXTERNAL_SEARCH_BASE_URL and EXTERNAL_SEARCH_COLLECTION_NAME and EXTERNAL_SEARCH_API_KEY:
        curl_cmd = f"""curl --location '{SOLAR_SEARCH_URL}' \\
  --header 'Authorization: Bearer YOUR_UPSTAGE_API_KEY' \\
  --header 'Content-Type: application/json' \\
  --data '{{
    "model": "solar-pro2-search",
    "messages": [
      {{"role": "user", "content": "Your question here"}}
    ],
    "web_search_options": {{
      "search_context_size": "medium",
      "external_search_engine_only": true,
      "servers": [
        {{
          "url": "{EXTERNAL_SEARCH_BASE_URL.rstrip('/')}/search/{EXTERNAL_SEARCH_COLLECTION_NAME}",
          "key": "YOUR_EXTERNAL_SEARCH_KEY"
        }}
      ]
    }},
    "stream": true
  }}'"""
    else:
        curl_cmd = f"""curl --location '{SOLAR_SEARCH_URL}' \\
  --header 'Authorization: Bearer YOUR_UPSTAGE_API_KEY' \\
  --header 'Content-Type: application/json' \\
  --data '{{
    "model": "solar-pro2-search",
    "messages": [
      {{"role": "user", "content": "Your question here"}}
    ],
    "stream": true
  }}'"""
    
    st.code(curl_cmd, language="bash")
    st.caption("💡 Copy this command for API testing")
    
    st.divider()
    
    # API Configuration
    st.subheader("🔑 API Settings")
    if UPSTAGE_API_KEY:
        st.success("**API Key:** ✓ Configured")
    else:
        st.error("**API Key:** ✗ Not configured")
    
    st.info(f"**Model:** solar-pro2-search")
    st.info(f"**Streaming:** ✓ Enabled")
    
    # External Search Configuration
    st.subheader("🔍 Search Settings")
    if EXTERNAL_SEARCH_BASE_URL and EXTERNAL_SEARCH_COLLECTION_NAME and EXTERNAL_SEARCH_API_KEY:
        st.success("**External Search:** ✓ Enabled")
        with st.expander("External Search Details"):
            st.write(f"**Collection:** {EXTERNAL_SEARCH_COLLECTION_NAME}")
            st.write(f"**Mode:** External only (skips Perplexity)")
            st.write(f"**Context Size:** medium")
    else:
        st.warning("**External Search:** ✗ Disabled")
        st.caption("Using default Perplexity search")
    
    # Actions
    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Status
    st.divider()
    st.caption(f"Messages: {len(st.session_state.messages)}")
    st.caption("Status: Ready ✓")

