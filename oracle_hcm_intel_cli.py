#!/usr/bin/env python3

import argparse
import json
import os
import getpass
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

# 🔐 Decrypt encrypted .env.enc using runtime key (no persistence of decrypted file)
def decrypt_env_to_memory():
    if not os.path.exists(".env.enc"):
        print("❌ Missing encrypted environment file: .env.enc")
        exit(1)

    key = getpass.getpass("🔐 Enter encryption key for .env: ").strip().encode()

    try:
        f = Fernet(key)
        decrypted_bytes = f.decrypt(Path(".env.enc").read_bytes())
        with open(".env.temp", "wb") as temp:
            temp.write(decrypted_bytes)
        from dotenv import load_dotenv
        load_dotenv(".env.temp")
        os.remove(".env.temp")
    except InvalidToken:
        print("❌ Invalid decryption key.")
        exit(1)

# Load environment variables securely
decrypt_env_to_memory()

from Cohere_GenAI_Function import generate_response as call_cohere
import openai

# Load HCM metadata
TABLES_PATH = "tables_metadata.json"
VIEWS_PATH = "views_metadata.json"

with open(TABLES_PATH, "r", encoding="utf-8") as f:
    TABLES = json.load(f)

with open(VIEWS_PATH, "r", encoding="utf-8") as f:
    VIEWS = json.load(f)

def filter_metadata(context):
    context = context.lower()
    filtered = []
    for obj in TABLES + VIEWS:
        name = obj.get("table_name") or obj.get("view_name", "")
        if context in name.lower() or context in obj.get("description", "").lower():
            filtered.append(name)
    return filtered

def build_prompt(user_prompt, context=None, bip_template=False):
    context_tables = filter_metadata(context) if context else []
    relevant_objects = []

    for table in TABLES:
        if table["table_name"] in context_tables or not context:
            relevant_objects.append({
                "name": table["table_name"],
                "description": table["description"],
                "columns": [col["column_name"] for col in table["columns"]]
            })

    for view in VIEWS:
        if view["view_name"] in context_tables or not context:
            relevant_objects.append({
                "name": view["view_name"],
                "description": view["description"],
                "columns": [col["column_name"] for col in view["columns"]]
            })

    system_prompt = (
        "You are an expert Oracle Cloud HCM analyst. "
        "Based on the user's prompt and the metadata provided, help the user by generating SQL queries, suggesting joins, "
        "explaining tables or optimizing SQL statements. Be accurate and clear.\n\n"
    )

    if bip_template:
        system_prompt = (
            "You are an expert in building Oracle BI Publisher (BIP) data model queries for Oracle Cloud HCM. "
            "Given the prompt and metadata, generate a SQL query ready for use in BI Publisher, including joins, filters, "
            "and logical structure. Avoid unnecessary formatting. Focus on correctness and clarity.\n\n"
        )

    metadata_summary = json.dumps(relevant_objects, indent=2)
    return system_prompt + f"User prompt: {user_prompt}\n\nRelevant metadata:\n{metadata_summary}"

def interactive_mode():
    print("🔧 Interactive Mode Activated\n")

    print("Choose an LLM provider:")
    print("1. OpenAI (default)")
    print("2. Oracle OCI (Cohere)")
    provider = input("Enter number [1/2]: ").strip()
    provider = "oci" if provider == "2" else "openai"

    print("\nChoose an action:")
    actions = [
        "Suggest joins for a table",
        "Generate SQL query",
        "Semantic search",
        "Explain and optimize SQL",
        "Generate BI Publisher SQL template",
        "Custom prompt"
    ]
    for i, a in enumerate(actions, 1):
        print(f"{i}. {a}")
    choice = input("Enter number: ").strip()

    bip_template = False

    if choice == "1":
        table = input("Enter table name (e.g., PER_ALL_PEOPLE_F): ").strip()
        user_prompt = f"Suggest joins for {table}"
    elif choice == "2":
        user_prompt = input("Describe your SQL query need: ").strip()
    elif choice == "3":
        term = input("Enter semantic keyword (e.g., job assignments): ").strip()
        user_prompt = f"Find tables or views related to {term}"
    elif choice == "4":
        sql = input("Paste SQL statement to explain/optimize: ").strip()
        user_prompt = f"Explain the following SQL and suggest improvements:\n{sql}"
    elif choice == "5":
        user_prompt = input("Describe the BI Publisher report you want to generate: ").strip()
        bip_template = True
    else:
        user_prompt = input("Enter your custom prompt: ").strip()

    context = input("\nOptional: Add a context keyword to narrow results (press Enter to skip): ").strip() or None
    output = input("Enter output file name (e.g., result.txt): ").strip()
    markdown = input("Format output as markdown? (y/N): ").lower().strip() == "y"

    return {
        "prompt": user_prompt,
        "output": output,
        "provider": provider,
        "context": context,
        "markdown": markdown,
        "bip_template": bip_template
    }

def main():
    parser = argparse.ArgumentParser(description="HCM AI CLI Assistant")
    parser.add_argument("--prompt", type=str, help="User query (e.g., 'Suggest joins for PER_ALL_PEOPLE_F')")
    parser.add_argument("--output", type=str, help="Output file to save result")
    parser.add_argument("--provider", choices=["openai", "oci"], default="openai", help="LLM Provider to use")
    parser.add_argument("--context", type=str, help="Optional context for semantic filtering")
    parser.add_argument("--list-tables", action="store_true", help="List available table names")
    parser.add_argument("--list-views", action="store_true", help="List available view names")
    parser.add_argument("--markdown", action="store_true", help="Format output with markdown")
    parser.add_argument("--bip-template", action="store_true", help="Generate a BI Publisher SQL template")

    args = parser.parse_args()

    if args.list_tables:
        print("📄 Available Tables:")
        for t in TABLES:
            print("-", t["table_name"])
        return

    if args.list_views:
        print("👁️  Available Views:")
        for v in VIEWS:
            print("-", v["view_name"])
        return

    if not args.prompt and not args.bip_template or not args.output:
        args = argparse.Namespace(**{**vars(args), **interactive_mode()})

    prompt = build_prompt(args.prompt, args.context, bip_template=args.bip_template)

    if args.provider == "openai":
        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
    else:
        result = call_cohere(prompt)

    if args.markdown:
        result = f"```\n{result}\n```"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"✅ Response saved to {args.output}")

if __name__ == "__main__":
    main()