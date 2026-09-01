# Setup

This section details how to setup the JAMB benchmark suite.
It assumes that you have already installed:

- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [docker](https://docs.docker.com/desktop/) or [podman](https://podman.io/docs/installation)

It also assumes that you already know how your shell works.
If it is new for you to operate your computer through the terminal
consider looking at the first couple of lectures of the [MIT Missing Semester](https://missing.csail.mit.edu/).

## Step 1: Install GCC (required for compilation)

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install build-essential
```

**Windows:**

It is recommended to use the WSL subsystem, please consult the
[Guide](https://learn.microsoft.com/en-us/windows/wsl/install).
But, JPAMB does also work on Windows.

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

To install uv, follow the guide [here](https://docs.astral.sh/uv/getting-started/installation/).
In short, it is a single step:

```bash
# On Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Important:** Restart your terminal/command prompt after installing uv!

## Step 3: Download the repository

Clone the repo and navigate to it.

```bash
git clone https://github.com/kalhauge/jpamb.git
cd jpamb
```

## Step 4: Verify everything works

Finally, you should be able to verify that everything works:

```bash
uv run jpamb checkhealth
```

You should see several green "ok" messages. If you see any red errors, check the
troubleshooting section below!

**IMPORTANT**, if you want to use Python, follow the guide [here](docs/python.md).
Then come back and run `checkhealth` without uv:

```bash
jpamb checkhealth
```

## Troubleshooting

### Issue: "Command not found" errors:

- Make sure you restart your terminal after installing uv
- Try `which uv` to see if it's installed correctly

### Issue: "Health check fails"

- Make sure you're in the JPAMB directory
- Make sure GCC is installed (Step 1 above)
- Make sure docker or podman is installed

### Issue: Build fails on Windows with "Microsoft Visual C++ 14.0 or greater is required"

**Cause:** The `runit` dependency requires a C compiler for its `timer.c` extension, which is often missing on standard Windows setups.
**Solution:**

- **Option A:** Open Visual Studio Installer and add the "Desktop development with C++" workload.
- **Option B (Recommended):** Use Windows Subsystem for Linux (WSL) instead. Run `wsl --install -d Ubuntu` and follow the Linux setup instructions.

### Issue: "Operation not permitted" inside WSL

Example error: `error: [Errno 1] Operation not permitted: '/mnt/c/Users/.../jpamb.egg-info/tmpum76ils9'*`

**Cause:** Running the build inside a mounted Windows directory (`/mnt/c/...`), especially one synced by OneDrive, causes file permission and symlink errors during the Python build process.
**Solution:** Move the project directly into the native Linux home directory (`~`), delete the broken environment, and rebuild.

```bash
cp -r "/mnt/c/Users/<YourUser>/.../jpamb" ~/jpamb
cd ~/jpamb
rm -rf .venv
uv run jpamb checkhealth
```

### Issue: "subprocess.TimeoutExpired: Command ... timed out after X seconds"

**Cause:** The Docker image `ghcr.io/kalhauge/jvm2json:jdk-latest` is not cached locally, and downloading it takes longer than the health check's built-in time limit.
**Solution:** Manually pull the image before running the check.

```bash
docker pull ghcr.io/kalhauge/jvm2json:jdk-latest
uv run jpamb checkhealth
```

### Windows users:

- Use PowerShell or Command Prompt
- Replace `/` with `\` in file paths if needed
- Consider using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for easier setup
