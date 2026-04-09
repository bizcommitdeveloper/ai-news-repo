import os
import requests
from supabase import create_client, Client
import json

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LLM_API_KEY = os.getenv("LLM_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FB_API_KEY = os.getenv("FB_API_KEY")

SUPABASE_TABLE = "posted_repos"

# Initialize Supabase client
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_top_repos():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = "https://api.github.com/search/repositories?q=stars:>10000&sort=stars&order=desc&per_page=50"
    resp = requests.get(url, headers=headers)
    return resp.json()["items"]

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    resp = requests.get(url, headers=headers)
    return resp.text if resp.status_code == 200 else None

def call_llm(prompt, content):
    # Replace with your LLM API call (OpenAI, Claude, etc.)
    return "LLM output here"

def schedule_facebook_post(content):
    # Replace with Buffer/ContentStudio/Facebook Graph API call
    pass

def is_repo_posted(supabase: Client, repo_url: str) -> bool:
    result = supabase.table(SUPABASE_TABLE).select("repo_url").eq("repo_url", repo_url).execute()
    return len(result.data) > 0

def mark_repo_posted(supabase: Client, repo_url: str):
    supabase.table(SUPABASE_TABLE).insert({"repo_url": repo_url}).execute()

def main():
    supabase = get_supabase_client()
    repos = get_top_repos()
    for repo in repos:
        repo_url = repo["html_url"]
        if is_repo_posted(supabase, repo_url):
            continue
        readme = get_readme(repo["owner"]["login"], repo["name"])
        if not readme:
            continue
        summary = call_llm(SYSTEM_PROMPT_SUMMARY, readme)
        journalist_piece = call_llm(SYSTEM_PROMPT_JOURNALIST, summary)
        bengali_piece = call_llm(SYSTEM_PROMPT_BENGALI, journalist_piece)
        hashtags = "#AI #Tech #OpenSource #Trending"
        post_content = f"{bengali_piece}\n\n🔗 {repo_url}\n{hashtags}"
        schedule_facebook_post(post_content)
        mark_repo_posted(supabase, repo_url)

SYSTEM_PROMPT_SUMMARY = """
You are a technical analyst. Summarize the following GitHub README into:
- Core value proposition (1-2 lines)
- Technical stack (bullet points)
- Main use case (1-2 lines)
Be concise and factual.
"""

SYSTEM_PROMPT_JOURNALIST = """
You are a Senior Tech Journalist for a leading magazine. Rewrite the summary into a short, punchy, slightly opinionated, and highly engaging write-up. Make it insightful and suitable for a LinkedIn/Facebook audience.
"""

SYSTEM_PROMPT_BENGALI = """
You are a Kolkata-based tech journalist. Rewrite the following English piece into authentic Kolkata Bengali, using informal yet professional tone, common Calcutta phrasing/slang, and avoiding overly formal or Bangladeshi dialect. Make it engaging for local techies.
"""

if __name__ == "__main__":
    main()
