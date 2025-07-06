# 🧠 Oracle HCM Intel CLI Tool

A professional-grade, Python-based command-line assistant that leverages Oracle HCM Cloud metadata and Generative AI (OpenAI or Oracle OCI GenAI) to help you intelligently interact with HCM tables and views for support, analysis, reporting, and insight.

---

## 🔍 Features

| Capability                    | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `--prompt`                   | Ask natural-language questions or give instructions to the assistant        |
| `--bip-template`             | Generate an Oracle BI Publisher-ready SQL template based on user intent     |
| `--provider openai|oci`      | Choose between OpenAI API or Oracle OCI GenAI (Cohere)                      |
| `--context`                  | Filter metadata using keywords (e.g. "payroll", "onboarding")              |
| `--list-tables`              | Print all available table names                                             |
| `--list-views`               | Print all available view names                                              |
| `--markdown`                 | Wraps output in a Markdown code block (`​```​`)                             |
| `--output filename.txt`      | Save AI response to file instead of printing                                |
| **Interactive Mode**         | If no arguments are passed, launches a guided prompt for less technical users |
| **Encrypted .env**           | Secure environment configuration with encryption key prompt at runtime      |

---

## 🤖 Example Actions Supported

| Prompt Example                                           | Result                                           |
|----------------------------------------------------------|--------------------------------------------------|
| "Suggest joins for PER_ALL_PEOPLE_F"                     | Natural join suggestions based on keys           |
| "Generate a query to get employee names and emails"      | Oracle SQL query generated                       |
| "Find tables related to job assignments"                 | Semantic search results                          |
| "Explain this SQL and suggest improvements..."           | Optimized explanation of SQL                     |
| `--bip-template` with "payroll summary report"           | Starter SQL ready for Oracle BI Publisher usage  |

---

## ⚙️ Setup

### 1. 📁 Clone the Project & Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. 🔐 Create and Encrypt Your Environment File

Create a file named `env_example.env`:

```env
OCI_COMPARTMENT_ID=...
OCI_TENANCY_ID=...
OCI_USER_ID=...
OCI_FINGERPRINT=...
OCI_REGION=us-chicago-1
OCI_PRIVATE_KEY_PATH=...
OCI_PROFILE=DEFAULT
OCI_MODEL_ID=...
OPENAI_API_KEY=...
```

Encrypt it securely with:

```bash
python env_encryption.py encrypt
```

You'll be prompted for an encryption key (not stored). This creates `.env.enc`.

> 💡 You must enter the same encryption key **every time you run the CLI** so the assistant can decrypt `.env.enc` in memory.

---

## 🧪 Example Usage

### Basic Prompt (OpenAI)

```bash
python oracle_hcm_intel_cli.py --prompt "Suggest joins for PER_ALL_PEOPLE_F" --output joins.txt --provider openai
```

### BI Publisher SQL Template (OpenAI or OCI)

```bash
python oracle_hcm_intel_cli.py --prompt "Generate a payroll summary report" --bip-template --output bip_template.sql
```

### With Context (Filtered Metadata)

```bash
python oracle_hcm_intel_cli.py --prompt "List views related to onboarding" --context onboarding --output context.txt
```

### Use Oracle GenAI (Cohere)

```bash
python oracle_hcm_intel_cli.py --prompt "Generate a salary report" --context salary --output report.txt --provider oci
```

### Markdown Output

```bash
python oracle_hcm_intel_cli.py --prompt "Get person ID and full name" --output result.txt --markdown
```

### Launch Interactive Mode (No Flags)

```bash
python oracle_hcm_intel_cli.py
```

---

## 📁 File Structure

| File                       | Purpose                                               |
| -------------------------- | ----------------------------------------------------- |
| `oracle_hcm_intel_cli.py`  | The main CLI assistant script                         |
| `env_encryption.py`        | Tool to encrypt and decrypt your `.env`               |
| `.env.enc`                 | Your encrypted environment config (runtime decrypted) |
| `tables_metadata.json`     | Parsed HCM table metadata                             |
| `views_metadata.json`      | Parsed HCM view metadata                              |
| `Cohere_GenAI_Function.py` | LLM interface for Oracle GenAI (Cohere)               |
| `config.json`              | Oracle LLM model ID and API configuration             |
| `env_example.env`          | Template for creating your own `.env`                 |

---

## 🔒 Security

* No plaintext `.env` is required at runtime — only the encrypted `.env.enc`
* Decryption happens in memory only after the user provides the correct encryption key
* The decrypted file is immediately removed after loading

---

## ⚖️ Disclaimer

This tool is not affiliated with Oracle. The metadata is sourced from publicly available Oracle documentation and is used solely for internal support and educational purposes. Please ensure your usage complies with Oracle’s licensing terms and your organization's policies.