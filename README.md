# 📌 Web Scraping Project Setup with `uv`

This project uses `uv` for dependency management, virtual environments, and multiple environments (development, testing, production). Follow this guide to set up and run the project in different environments.

---

## 📥 Installation

### 1️⃣ **Install `uv` (if not installed)**
```sh
pip install uv
```

### 2️⃣ **Clone the Repository**
```sh
git clone <repository-url>
cd <project-folder>
```

### 3️⃣ **Create a Virtual Environment**
```sh
uv sync
```

### 4️⃣ **Activate the Virtual Environment**
- **macOS/Linux**:
  ```sh
  source .venv/bin/activate
  ```
- **Windows (PowerShell)**:
  ```sh
  .venv\Scripts\activate
  ```

---

## 📦 Installing Dependencies

### **For Production** (default environment)
```sh
uv add requests beautifulsoup4 lxml selenium playwright httpx
```

### **For Development**
```sh
uv add --dev black flake8 isort mypy dotenv-linter
```

### **For Testing**
```sh
uv add --group test pytest pytest-mock responses
```

---

## 🛠️ Environment Setup

This project supports multiple environments using `.env` files.

### 1️⃣ **Create `.env` Files**

#### **📌 `.env.dev` (Development)**
```ini
ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
```

#### **📌 `.env.test` (Testing)**
```ini
ENV=testing
DEBUG=False
LOG_LEVEL=INFO
```

#### **📌 `.env.prod` (Production)**
```ini
ENV=production
DEBUG=False
LOG_LEVEL=WARNING
```

### 2️⃣ **Modify `pyproject.toml` (Optional, for grouping dependencies)**
```toml
[tool.uv]
python = "3.11"  # Adjust to your Python version

[tool.uv.groups]
dev = ["black", "flake8", "isort", "mypy", "dotenv-linter"]
test = ["pytest", "pytest-mock", "responses"]
```

---

## 🚀 Running the Project in Different Environments

### **1️⃣ Development Mode**
```sh
export ENV=development && uv run python main.py
```

### **2️⃣ Testing Mode**
```sh
export ENV=testing && uv run pytest
```

### **3️⃣ Production Mode**
```sh
export ENV=production && uv run python main.py
```
*(For Windows, use `set ENV=...` instead of `export ENV=...`)*

---

## 📁 Project Structure
```plaintext
📂 project-folder/
├── 📂 .venv/          # Virtual environment (created by uv venv)
├── 📂 src/            # Main source code folder
│   ├── main.py        # Entry point of the project
│   ├── utils.py       # Helper functions
├── 📄 .env.dev        # Development environment variables
├── 📄 .env.test       # Testing environment variables
├── 📄 .env.prod       # Production environment variables
├── 📄 pyproject.toml  # Dependency management
├── 📄 README.md       # Project documentation
```

---

## 🔄 Updating Dependencies

### **Update All Dependencies**
```sh
uv pip freeze > requirements.txt
```

### **Install New Libraries**
```sh
uv add new-library-name
```

### **Remove a Library**
```sh
uv remove unwanted-library
```

---

## 🎯 Key Takeaways
✅ `uv` provides fast dependency management.
✅ Uses `.env` files for environment-based configurations.
✅ Easy to switch between `dev`, `test`, and `prod` environments.
✅ Supports grouped dependencies for better project organization.

---

### 🎉 **You're Ready to Start!**
Now you can run the project, switch environments, and manage dependencies seamlessly! 🚀


## Cheatsheet: Common Operations in `uv` Workflows

| Operation | `uv` Command | Explanation |
|-----------|-------------|-------------|
| Project dependency file | `pyproject.toml` | Base/core dependencies are defined here. |
| Project lock file | `uv.lock` | Derived dependencies are managed here. |
| Installing Python | `uv sync` or `uv run` | Installs Python if needed as part of syncing or running code. |
| Creating virtual environments | `uv sync` or `uv run` | Automatically creates a virtual environment if needed. |
| Installing packages | `uv sync` or `uv run` | Installs all necessary packages into the environment. |
| Building dependencies | `uv sync` or `uv run` | Rebuilds the lockfile from dependencies. |
| Add a package | `uv add <package>` | Adds the package to `pyproject.toml`, updates `uv.lock`, and syncs the environment. |
| Remove a package | `uv remove <package>` | Removes the package and syncs the environment. |
| Upgrade a package | `uv sync --upgrade-package <package>` | Upgrades a specific package in `uv.lock`. |
| Upgrade all packages | `uv lock --upgrade` | Upgrades all packages according to `pyproject.toml` constraints. |
