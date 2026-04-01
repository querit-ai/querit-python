# Copyright 2026 QUERIT PRIVATE LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
AI-powered search via tool use (function calling).

Unlike ai_search_summary.py which uses a two-step XML-based pipeline,
this example lets the LLM drive the search itself through tool use:

  Round 1 – Send the user's question with a `web_search` tool definition.
             The model decides whether and how to search, emitting one or more
             tool_call messages, each containing a JSON search query.
  Round 2 – Execute every requested Querit search, inject the results as
             tool messages, then ask the model to synthesize a final answer.

This is the natural fit for models that support function calling
(e.g. DeepSeek-V3, GPT-4o, Qwen-Max), because:
  - No XML parsing needed.
  - The model controls query decomposition autonomously.
  - Multiple parallel searches are expressed as multiple tool calls in one turn.

Required environment variables:
    OPENAI_API_KEY      – API key for the OpenAI-compatible endpoint.
    OPENAI_BASE_URL     – Base URL of the OpenAI-compatible endpoint.
                          e.g. https://api.deepseek.com/v1 for DeepSeek.
    OPENAI_MODEL        – Model name. Defaults to "deepseek-chat".
    QUERIT_API_KEY      – API key for the Querit Search API.

Usage:
    export OPENAI_API_KEY="sk-..."
    export OPENAI_BASE_URL="https://api.deepseek.com/v1"
    export OPENAI_MODEL="deepseek-chat"
    export QUERIT_API_KEY="qr-..."
    python examples/ai_search_tool_use.py "GDP Data of Laos for the Past 10 Years"
"""

import json
import os
import sys
from datetime import date
from typing import List

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from querit import QueritClient
from querit.models.request import SearchRequest

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

# Passed to the LLM in every Round-1 request.
# The model emits one tool_call per distinct search query it wants to run.
_WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for up-to-date information. "
            "Call this tool once per distinct search query. "
            "To compare multiple topics, make multiple calls with different queries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Concise search keywords, in the same language as the user.",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results to retrieve. Defaults to 10.",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
}

# System prompt for Round 1 (tool use turn).
_SYSTEM_PROMPT = f"""\
You are a helpful research assistant with access to a web_search tool.
Today's date is {date.today().isoformat()}.
When the user's question requires current or factual information, call web_search \
with concise keywords. You may call it multiple times for different sub-queries.
If the question does not need a search (e.g. a greeting or pure reasoning task), \
answer directly without calling any tool.\
"""

# System prompt for Round 2 (answer synthesis turn).
_SYNTHESIS_SYSTEM_PROMPT = f"""\
You are a helpful research assistant. Today's date is {date.today().isoformat()}.
Answer the user's question based on the search results provided.

Citation rules:
- Cite sources inline using [number] at the end of the relevant sentence.
- If a sentence draws from multiple sources, list all numbers, e.g. [1][3].
- Do not group all citations at the end.
- If none of the results are relevant, answer from your own knowledge.
- Respond in the same language as the user's question.\
"""

# ---------------------------------------------------------------------------
# Querit search executor
# ---------------------------------------------------------------------------

def execute_web_search(querit: QueritClient, query: str, count: int = 10) -> list:
    """
    Run a single Querit search and return results as a plain list of dicts.
    Each dict has: url, title, snippet, page_age.
    """
    req = SearchRequest(query=query, count=count)
    resp = querit.search(req)
    results = []
    for item in resp.results:
        results.append({
            "url": item.url or "",
            "title": item.title or item.url or "",
            "snippet": item.snippet or "",
            "page_age": item.page_age or "",
        })
    return results


def format_tool_result(query: str, results: list, start: int = 1) -> str:
    """
    Serialize search results to a compact JSON string suitable as a tool message.

    Each result is tagged with a globally-unique ``ref`` number starting from
    *start*, so that citation numbers are consistent across multiple tool calls
    within the same conversation turn.
    """
    numbered = [{"ref": start + i, **r} for i, r in enumerate(results)]
    return json.dumps(
        {"query": query, "results": numbered},
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def ai_search_tool_use(user_question: str) -> None:
    # --- load config ---
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    openai_model = os.environ.get("OPENAI_MODEL", "deepseek-chat")
    querit_api_key = os.environ.get("QUERIT_API_KEY")

    if not openai_api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable is not set.")
    if not querit_api_key:
        sys.exit("Error: QUERIT_API_KEY environment variable is not set.")

    ai_client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    querit_client = QueritClient(api_key=querit_api_key)

    print(f"\n{'='*60}")
    print(f"Question : {user_question}")
    print(f"Model    : {openai_model}")
    print(f"{'='*60}\n")

    # -----------------------------------------------------------------
    # Round 1 – ask the model what to search
    # -----------------------------------------------------------------
    messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    print("Round 1 – Asking model for search queries …")
    round1 = ai_client.chat.completions.create(
        model=openai_model,
        messages=messages,
        tools=[_WEB_SEARCH_TOOL],
        tool_choice="auto",
    )
    assistant_msg = round1.choices[0].message
    total_prompt_tokens = round1.usage.prompt_tokens if round1.usage else 0
    total_completion_tokens = round1.usage.completion_tokens if round1.usage else 0

    # No tool calls → model answered directly, nothing left to do.
    if not assistant_msg.tool_calls:
        print("\nModel answered directly (no search needed):\n")
        print(assistant_msg.content)
        print(f"\n{'─'*60}")
        print(f"Statistics: searches=0  tokens(prompt={total_prompt_tokens}, completion={total_completion_tokens}, total={total_prompt_tokens + total_completion_tokens})")
        return

    print(f"Model requested {len(assistant_msg.tool_calls)} search(es):\n")
    search_count = len(assistant_msg.tool_calls)

    # Append the assistant turn (with tool_calls) to the message history.
    messages.append(assistant_msg)  # type: ignore[arg-type]

    # -----------------------------------------------------------------
    # Execute each requested search and collect tool result messages
    # -----------------------------------------------------------------
    all_results: list = []
    next_ref = 1  # global citation counter across all tool calls

    for tc in assistant_msg.tool_calls:
        args = json.loads(tc.function.arguments)
        query = args.get("query", "")
        count = int(args.get("count", 10))

        print(f"  [search] {query!r}  (count={count})")
        try:
            results = execute_web_search(querit_client, query, count)
        except Exception as exc:
            print(f"           ↳ failed: {exc}", file=sys.stderr)
            results = []

        # Print retrieved results with globally-unique ref numbers
        for i, r in enumerate(results):
            ref = next_ref + i
            age = f"  ({r['page_age']})" if r["page_age"] else ""
            print(f"    [{ref}] {r['title']}")
            print(f"          {r['url']}{age}")
            if r["snippet"]:
                print(f"          {r['snippet'][:100]}…")

        all_results.extend(results)

        # Inject as a tool message with globally-sequential ref numbers.
        tool_result_content = format_tool_result(query, results, start=next_ref)
        next_ref += len(results)
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": tool_result_content,
        })

    print(f"\nTotal unique results collected: {len(all_results)}\n")

    # -----------------------------------------------------------------
    # Round 2 – synthesize the final answer
    # -----------------------------------------------------------------
    # Replace the system prompt with the synthesis-focused one.
    messages[0] = {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT}

    print("Round 2 – Synthesizing answer …\n")
    round2 = ai_client.chat.completions.create(
        model=openai_model,
        messages=messages,
    )
    if round2.usage:
        total_prompt_tokens += round2.usage.prompt_tokens
        total_completion_tokens += round2.usage.completion_tokens

    print("Answer:\n")
    print(round2.choices[0].message.content)
    print()

    print(f"{'─'*60}")
    print(f"Statistics: searches={search_count}  tokens(prompt={total_prompt_tokens}, completion={total_completion_tokens}, total={total_prompt_tokens + total_completion_tokens})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI-powered search via tool use (function calling)."
    )
    parser.add_argument("question", help="Question to search and summarize.")
    args = parser.parse_args()
    ai_search_tool_use(args.question)
