#!/usr/bin/env python3

import argparse
import json
import os
import getpass
from pathlib import Path
from datetime import datetime
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

def filter_metadata(context, include_tables=True, include_views=True):
    if not context:
        return []

    keywords = [k.strip().lower() for k in context.split(",")]
    filtered = []
    data_sources = []
    if include_tables:
        data_sources += TABLES
    if include_views:
        data_sources += VIEWS

    for obj in data_sources:
        name = obj.get("table_name") or obj.get("view_name", "")
        description = obj.get("description", "").lower()
        if any(kw in name.lower() or kw in description for kw in keywords):
            filtered.append(name)
    return filtered

def build_prompt(user_prompt, context=None, bip_template=False, include_tables=True, include_views=True):
    context_tables = filter_metadata(context, include_tables, include_views) if context else []
    relevant_objects = []

    if include_tables:
        for table in TABLES:
            if table["table_name"] in context_tables or not context:
                relevant_objects.append({
                    "name": table["table_name"],
                    "description": table["description"],
                    "columns": [col["column_name"] for col in table["columns"]]
                })

    if include_views:
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
    return system_prompt + f"User prompt: {user_prompt}\n\nRelevant metadata:\n{metadata_summary}", metadata_summary

def interactive_mode():
    print("\n🔧 Welcome to the Oracle HCM AI Assistant (Interactive Mode)")
    print("-----------------------------------------------------------")

    while True:
        print("\nChoose an LLM provider:")
        print("  1. OpenAI (default)")
        print("  2. Oracle OCI (Cohere)")
        print("  3. Exit")
        provider_choice = input("Enter number [1/2/3]: ").strip()
        if provider_choice == "3":
            print("\n👋 Exiting interactive mode.")
            exit(0)
        provider = "oci" if provider_choice == "2" else "openai"

        print("\nChoose an action:")
        actions = [
            "Suggest joins for a table",
            "Generate SQL query",
            "Semantic search",
            "Explain and optimize SQL",
            "Generate BI Publisher SQL template",
            "Custom prompt",
            "Exit"
        ]
        for i, a in enumerate(actions, 1):
            print(f"  {i}. {a}")
        choice = input("Enter number: ").strip()

        if choice == "7":
            print("\n👋 Exiting interactive mode.")
            exit(0)

        bip_template = False

        if choice == "1":
            table = input("\nEnter table name (e.g., PER_ALL_PEOPLE_F): ").strip()
            user_prompt = f"Suggest joins for {table}"
        elif choice == "2":
            user_prompt = input("\nDescribe your SQL query need: ").strip()
        elif choice == "3":
            term = input("\nEnter semantic keyword (e.g., job assignments): ").strip()
            user_prompt = f"Find tables or views related to {term}"
        elif choice == "4":
            sql = input("\nPaste SQL statement to explain/optimize: ").strip()
            user_prompt = f"Explain the following SQL and suggest improvements:\n{sql}"
        elif choice == "5":
            user_prompt = input("\nDescribe the BI Publisher report you want to generate: ").strip()
            bip_template = True
        else:
            user_prompt = input("\nEnter your custom prompt: ").strip()

        context = input("\nOptional: Add one or more context keywords (comma-separated): ").strip() or None
        output = input("Enter output file name (e.g., result.txt): ").strip()
        markdown = input("Format output as markdown? (y/N): ").lower().strip() == "y"

        use_tables = input("Include table metadata? (Y/n): ").strip().lower() != "n"
        use_views = input("Include view metadata? (Y/n): ").strip().lower() != "n"
        audit = input("Enable audit mode (log metadata)? (y/N): ").strip().lower() == "y"

        run_query(
            prompt=user_prompt,
            output=output,
            provider=provider,
            context=context,
            markdown=markdown,
            bip_template=bip_template,
            use_tables=use_tables,
            use_views=use_views,
            audit=audit
        )

def run_query(prompt, output, provider, context=None, markdown=False, bip_template=False, use_tables=True, use_views=True, audit=False):
    full_prompt, metadata_summary = build_prompt(
        prompt,
        context,
        bip_template=bip_template,
        include_tables=use_tables,
        include_views=use_views
    )

    if audit:
        logs_path = Path("Logs")
        logs_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_path / f"metadata_{timestamp}.json"
        with open(log_file, "w", encoding="utf-8") as log:
            log.write(metadata_summary)
        print(f"📋 Metadata logged to {log_file}")

    if provider == "openai":
        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": full_prompt}],
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
    else:
        result = call_cohere(full_prompt)

    if markdown:
        result = f"```\n{result}\n```"

    output_path = Path("Output")
    output_path.mkdir(exist_ok=True)
    output_file = output_path / output

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n✅ Response saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="HCM AI CLI Assistant")
    parser.add_argument("--prompt", type=str, help="User query (e.g., 'Suggest joins for PER_ALL_PEOPLE_F')")
    parser.add_argument("--output", type=str, help="Output file to save result")
    parser.add_argument("--provider", choices=["openai", "oci"], default="openai", help="LLM Provider to use")
    parser.add_argument("--context", type=str, help="Optional context for semantic filtering (comma-separated)")
    parser.add_argument("--list-tables", action="store_true", help="List available table names")
    parser.add_argument("--list-views", action="store_true", help="List available view names")
    parser.add_argument("--markdown", action="store_true", help="Format output with markdown")
    parser.add_argument("--bip-template", action="store_true", help="Generate a BI Publisher SQL template")
    parser.add_argument("--use-tables", action="store_true", help="Include table metadata in prompt")
    parser.add_argument("--use-views", action="store_true", help="Include view metadata in prompt")
    parser.add_argument("--audit", action="store_true", help="Enable audit mode to log metadata used")

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
        interactive_mode()
        return

    run_query(
        prompt=args.prompt,
        output=args.output,
        provider=args.provider,
        context=args.context,
        markdown=args.markdown,
        bip_template=args.bip_template,
        use_tables=args.use_tables or not args.use_views,
        use_views=args.use_views or not args.use_tables,
        audit=args.audit
    )

if __name__ == "__main__":
    main()