# Setup

## Step 0: Get familiar with your shell

If you do not already know how your shell works, consider looking at the first couple of
lectures of the [MIT Missing Semester](https://missing.csail.mit.edu/).

## Step 1: Install GCC (required for compilation)

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install build-essential
```

**Windows:**

```bash
# Install Microsoft Visual C++ 14.0 (required for Python C extensions)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Or install via Visual Studio Installer and select "C++ build tools"

# Alternative: Install Visual Studio Community (includes build tools)
winget install Microsoft.VisualStudio.2022.Community
```

**Mac:**

```bash
# Install Xcode command line tools
xcode-select --install
```

## Step 2: Install uv (Python package manager)

```bash
# On Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Important:** Restart your terminal/command prompt after installing uv!

## Step 3: Verify everything works

```bash
uv run jpamb checkhealth
```

You should see several green "ok" messages. If you see any red errors, check the
troubleshooting section below!

## Troubleshooting

**"Command not found" errors:**

- Make sure you restart your terminal after installing uv
- Try `which uv` to see if it's installed correctly

**"Health check fails":**

- Make sure you're in the JPAMB directory
- Make sure GCC is installed (Step 1 above)
- Make sure docker or podman is installed

**Windows users:**

- Use PowerShell or Command Prompt
- Replace `/` with `\` in file paths if needed
- Consider using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for easier setup

**Still stuck?** Check the example solutions in `solutions/` directory or ask for help!
