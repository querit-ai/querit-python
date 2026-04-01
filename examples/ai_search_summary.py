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
AI-powered search with summarization example.

This module demonstrates a three-step pipeline inspired by Cherry Studio's
searchOrchestrationPlugin:

  1. Query generation  – call an OpenAI-compatible LLM to rephrase the user's
     question into optimized search keywords (XML-structured output).
  2. Web search        – execute the extracted queries against the Querit Search API.
  3. Answer synthesis  – feed the search results back to the LLM and ask it to
     produce a grounded, cited answer.

Required environment variables:
    OPENAI_API_KEY      – API key for the OpenAI-compatible endpoint.
    OPENAI_BASE_URL     – Base URL of the OpenAI-compatible endpoint.
                          Defaults to https://api.openai.com/v1 if not set.
    OPENAI_MODEL        – Model name to use.  Defaults to "gpt-4o-mini".
    QUERIT_API_KEY      – API key for the Querit Search API.

Usage:
    export OPENAI_API_KEY="sk-..."
    export OPENAI_BASE_URL="https://api.openai.com/v1"
    export OPENAI_MODEL="gpt-4o-mini"
    export QUERIT_API_KEY="qr-..."
    python examples/ai_search_summary.py "GDP Data of Laos for the Past 10 Years"
"""

import os
import re
import sys
from datetime import date
from typing import List, Optional

from openai import OpenAI

from querit import QueritClient
from querit.models.request import SearchRequest

# ---------------------------------------------------------------------------
# Prompt templates  (ported from Cherry Studio's prompts.ts)
# ---------------------------------------------------------------------------

# Step 1: rephrase the user question into search-friendly keywords.
# Directly mirrors SEARCH_SUMMARY_PROMPT_WEB_ONLY from Cherry Studio.
# {chat_history} and {question} are filled in at call time.
_QUERY_GEN_PROMPT = """\
  You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search.
  **Use user's language to rephrase the question.**
  Follow these guidelines:
  1. If the question is a simple writing task, greeting (e.g., Hi, Hello, How are you), or does not require searching for information (unless the greeting contains a follow-up question), return 'not_needed' in the 'question' XML block. This indicates that no search is required.
  2. If the user asks a question related to a specific URL, PDF, or webpage, include the links in the 'links' XML block and the question in the 'question' XML block. If the request is to summarize content from a URL or PDF, return 'summarize' in the 'question' XML block and include the relevant links in the 'links' XML block.
  3. For websearch, You need extract keywords into 'question' XML block.
  4. Always return the rephrased question inside the 'question' XML block. If there are no links in the follow-up question, do not insert a 'links' XML block in your response.
  5. Always wrap the rephrased question in the appropriate XML blocks: use <websearch></websearch> for queries requiring real-time or external information. Ensure that the rephrased question is always contained within a <question></question> block inside the wrapper.
  6. *use websearch to rephrase the question*

  There are several examples attached for your reference inside the below 'examples' XML block.

  <examples>
  1. Follow up question: What is the capital of France
  Rephrased question:`
  <websearch>
    <question>
      Capital of France
    </question>
  </websearch>
  `

  2. Follow up question: Hi, how are you?
  Rephrased question:`
  <websearch>
    <question>
      not_needed
    </question>
  </websearch>
  `

  3. Follow up question: What is Docker?
  Rephrased question: `
  <websearch>
    <question>
      What is Docker
    </question>
  </websearch>
  `

  4. Follow up question: Can you tell me what is X from https://example.com
  Rephrased question: `
  <websearch>
    <question>
      What is X
    </question>
    <links>
      https://example.com
    </links>
  </websearch>
  `

  5. Follow up question: Summarize the content from https://example1.com and https://example2.com
  Rephrased question: `
  <websearch>
    <question>
      summarize
    </question>
    <links>
      https://example1.com
    </links>
    <links>
      https://example2.com
    </links>
  </websearch>
  `

  6. Follow up question: Based on websearch, Which company had higher revenue in 2022, "Apple" or "Microsoft"?
  Rephrased question: `
  <websearch>
    <question>
      Apple's revenue in 2022
    </question>
    <question>
      Microsoft's revenue in 2022
    </question>
  </websearch>
  `
  </examples>

  Anything below is part of the actual conversation. Use the conversation history and the follow-up question to rephrase the follow-up question as a standalone question based on the guidelines shared above.

  <conversation>
  {chat_history}
  </conversation>

  **Use user's language to rephrase the question.**
  Follow up question: {question}
  Rephrased question:
"""

# Step 2: synthesize an answer from search results.
# Mirrors REFERENCE_PROMPT from Cherry Studio, with today's date injected.
_ANSWER_PROMPT = """\
Please answer the question based on the reference materials

## Citation Rules:
- Please cite the context at the end of sentences when appropriate.
- Please use the format of citation number [number] to reference the context in corresponding parts of your answer.
- If a sentence comes from multiple contexts, please list all relevant citation numbers, e.g., [1][2]. Remember not to group citations at the end but list them in the corresponding parts of your answer.
- If all reference content is not relevant to the user's question, please answer based on your knowledge.

## Today's date: {today}

## My question is:

{question}

## Reference Materials:

{references}

Please respond in the same language as the user's question.
"""


# ---------------------------------------------------------------------------
# XML helper  (mirrors Cherry Studio's extractInfoFromXML / extract.ts)
# ---------------------------------------------------------------------------

def extract_search_queries(xml_text: str) -> List[str]:
    """
    Extract <question> values from inside a <websearch> block.

    Returns an empty list when the model indicates no search is needed
    (i.e. the sole question is 'not_needed').
    """
    # Grab everything inside <websearch>…</websearch>
    ws_match = re.search(r"<websearch>(.*?)</websearch>", xml_text, re.DOTALL)
    if not ws_match:
        return []

    block = ws_match.group(1)
    questions = re.findall(r"<question>\s*(.*?)\s*</question>", block, re.DOTALL)
    # Filter out the sentinel value
    return [q.strip() for q in questions if q.strip().lower() != "not_needed"]


# ---------------------------------------------------------------------------
# Step 1 – Query generation
# ---------------------------------------------------------------------------

def generate_search_queries(
    client: OpenAI,
    model: str,
    user_question: str,
    chat_history: str = "",
) -> tuple[List[str], int, int]:
    """Call the LLM to convert *user_question* into search keywords.

    Returns a tuple of (queries, prompt_tokens, completion_tokens).
    """
    prompt = _QUERY_GEN_PROMPT.format(chat_history=chat_history, question=user_question)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content or ""
    queries = extract_search_queries(raw)
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return queries, prompt_tokens, completion_tokens


# ---------------------------------------------------------------------------
# Step 2 – Querit search
# ---------------------------------------------------------------------------

def run_querit_searches(
    querit: QueritClient,
    queries: List[str],
    count_per_query: int = 10,
) -> List[dict]:
    """
    Execute each search query against the Querit API and collect results.

    Returns a flat list of result dicts, each containing url, title, snippet.
    """
    all_results: List[dict] = []
    seen_urls: set = set()

    for query in queries:
        print(f"  [search] {query!r}")
        try:
            req = SearchRequest(query=query, count=count_per_query)
            resp = querit.search(req)
            for item in resp.results:
                url = item.url or ""
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "url": url,
                        "title": item.title or url,
                        "snippet": item.snippet or "",
                        "page_age": item.page_age or "",
                    })
        except Exception as exc:
            print(f"  [search] warning: query {query!r} failed – {exc}", file=sys.stderr)

    return all_results


# ---------------------------------------------------------------------------
# Step 3 – Answer synthesis
# ---------------------------------------------------------------------------

def synthesize_answer(
    client: OpenAI,
    model: str,
    user_question: str,
    search_results: List[dict],
) -> tuple[str, int, int]:
    """Ask the LLM to produce a cited answer from search results.

    Returns a tuple of (answer, prompt_tokens, completion_tokens).
    """
    # Format as numbered references matching Cherry Studio's REFERENCE_PROMPT style.
    # The LLM is instructed to cite via [number] inline.
    references_text = "\n\n".join(
        f"[{i + 1}] title: {r['title']}\nurl: {r['url']}\n"
        + (f"date: {r['page_age']}\n" if r['page_age'] else "")
        + r['snippet']
        for i, r in enumerate(search_results)
    )
    prompt = _ANSWER_PROMPT.format(
        today=date.today().isoformat(),
        question=user_question,
        references=references_text or "(no search results available)",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return response.choices[0].message.content or "", prompt_tokens, completion_tokens


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def ai_search_and_summarize(user_question: str) -> None:
    # --- load config from environment ---
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    querit_api_key = os.environ.get("QUERIT_API_KEY")

    if not openai_api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable is not set.")
    if not querit_api_key:
        sys.exit("Error: QUERIT_API_KEY environment variable is not set.")

    ai_client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    querit_client = QueritClient(api_key=querit_api_key)

    print(f"\n{'='*60}")
    print(f"Question: {user_question}")
    print(f"{'='*60}\n")

    # --- Step 1: generate search queries ---
    print("Step 1 – Generating search queries …")
    queries, gen_prompt_tokens, gen_completion_tokens = generate_search_queries(
        ai_client, openai_model, user_question
    )

    if not queries:
        print("No search required for this question.\n")
        # Fall back to a direct LLM answer without search
        response = ai_client.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": user_question}],
        )
        print("Answer:\n")
        print(response.choices[0].message.content)
        usage = response.usage
        total_prompt = gen_prompt_tokens + (usage.prompt_tokens if usage else 0)
        total_completion = gen_completion_tokens + (usage.completion_tokens if usage else 0)
        print(f"\n{'─'*60}")
        print(f"Statistics: searches=0  tokens(prompt={total_prompt}, completion={total_completion}, total={total_prompt + total_completion})")
        return

    print(f"Extracted {len(queries)} query(ies): {queries}\n")

    # --- Step 2: execute searches ---
    print("Step 2 – Searching via Querit …")
    results = run_querit_searches(querit_client, queries, count_per_query=10)
    search_count = len(queries)
    print(f"Retrieved {len(results)} unique result(s).\n")
    for i, r in enumerate(results):
        print(f"  [{i + 1}] {r['title']}")
        print(f"       {r['url']}" + (f"  ({r['page_age']})" if r['page_age'] else ""))
        if r['snippet']:
            print(f"       {r['snippet'][:120]}…")
    print()

    # --- Step 3: synthesize answer ---
    print("Step 3 – Synthesizing answer …\n")
    answer, syn_prompt_tokens, syn_completion_tokens = synthesize_answer(
        ai_client, openai_model, user_question, results
    )

    print("Answer:\n")
    print(answer)
    print()

    total_prompt = gen_prompt_tokens + syn_prompt_tokens
    total_completion = gen_completion_tokens + syn_completion_tokens
    print(f"{'─'*60}")
    print(f"Statistics: searches={search_count}  tokens(prompt={total_prompt}, completion={total_completion}, total={total_prompt + total_completion})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-powered search with summarization.")
    parser.add_argument("question", help="Question to search and summarize.")
    args = parser.parse_args()
    ai_search_and_summarize(args.question)
