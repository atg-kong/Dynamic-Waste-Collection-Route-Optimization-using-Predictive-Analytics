# 🚀 Launch Dashboard in Visual Studio Code

## Method 1: Using VS Code Terminal (Recommended)

### Step 1: Open VS Code
- Open Visual Studio Code
- Open your project folder: **File** → **Open Folder** → Select this project directory

### Step 2: Open Terminal in VS Code
- Press **`Ctrl + `` `** (backtick) or **Ctrl + J**
- Or go to: **Terminal** → **New Terminal**

### Step 3: Ensure You're in the Project Directory
```bash
# Check current directory
pwd

# Should show: /path/to/Dynamic-Waste-Collection-Route-Optimization-using-Predictive-Analytics
```

### Step 4: Activate Virtual Environment (if using one)
```bash
# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

### Step 5: Install Dependencies (if not already done)
```bash
pip install -r requirements.txt
```

### Step 6: Launch Dashboard
```bash
streamlit run app.py
```

### Step 7: Access Dashboard
- The terminal will show:
  ```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
  ```
- Click on the **Local URL** (it will be clickable in VS Code terminal)
- Or manually open browser and go to: **http://localhost:8501**

---

## Method 2: Using VS Code Run Configuration

### Step 1: Create Launch Configuration

Create a file: `.vscode/launch.json` in your project root:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit Dashboard",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "app.py",
                "--server.port=8501"
            ],
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

### Step 2: Run
- Press **F5** or click **Run** → **Start Debugging**
- Or click the green play button in the sidebar

---

## Method 3: Using VS Code Task

### Step 1: Create Tasks Configuration

Create a file: `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Launch Streamlit Dashboard",
            "type": "shell",
            "command": "streamlit run app.py",
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

### Step 2: Run Task
- Press **Ctrl+Shift+P** (Cmd+Shift+P on Mac)
- Type: **Tasks: Run Task**
- Select: **Launch Streamlit Dashboard**

---

## Method 4: Using Code Runner Extension (Easy!)

### Step 1: Install Code Runner Extension
- Open Extensions: **Ctrl+Shift+X**
- Search: **Code Runner**
- Click **Install**

### Step 2: Right-Click on app.py
- Open `app.py` in VS Code
- Right-click anywhere in the file
- Select **Run Code** or press **Ctrl+Alt+N**

**Note:** You may need to configure Code Runner to use the terminal.

---

## 🔧 Troubleshooting in VS Code

### Problem: "streamlit: command not found"

**Solution:**
```bash
# Install streamlit
pip install streamlit

# Verify installation
streamlit --version
```

### Problem: "Module not found" errors

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install streamlit pandas numpy scikit-learn folium plotly ortools
```

### Problem: Port 8501 already in use

**Solution 1: Kill existing process**
```bash
# On Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# On Mac/Linux
lsof -ti:8501 | xargs kill -9
```

**Solution 2: Use different port**
```bash
streamlit run app.py --server.port 8502
```

### Problem: Dashboard opens but shows errors

**Solution:**
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Clear Streamlit cache
streamlit cache clear
```

---

## 🎨 VS Code Tips for Better Experience

### 1. **Install Python Extension**
- Search: **Python** by Microsoft
- Provides IntelliSense, debugging, linting

### 2. **Install Pylance Extension**
- Search: **Pylance**
- Better code completion and type checking

### 3. **Setup Python Interpreter**
- Press **Ctrl+Shift+P**
- Type: **Python: Select Interpreter**
- Choose your Python version/virtual environment

### 4. **Enable Auto-Save**
- **File** → **Auto Save**
- Changes will auto-reload in Streamlit!

### 5. **Split Terminal**
- Run dashboard in one terminal
- Keep another terminal free for commands
- Click the **split terminal** icon in VS Code

---

## 📊 VS Code Integrated Dashboard View

### Option 1: Simple Browser Extension
- Install **Live Preview** extension
- Right-click on HTML files
- Select **Show Preview**

### Option 2: VS Code Browser
- Install **Browser Preview** extension
- Open browser inside VS Code
- Navigate to http://localhost:8501

---

## 🎬 Quick Start in VS Code (30 seconds)

```bash
# 1. Open terminal in VS Code (Ctrl + `)
# 2. Run dashboard
streamlit run app.py

# 3. Ctrl+Click on the URL shown in terminal
# 4. Dashboard opens in your browser!
```

---

## 💡 Pro Tips

### Keyboard Shortcuts in VS Code
- **Ctrl + `** - Toggle terminal
- **Ctrl + J** - Toggle panel (terminal/problems/output)
- **Ctrl + B** - Toggle sidebar
- **Ctrl + K Z** - Zen mode (distraction-free)
- **F11** - Full screen (great for presentations!)

### Streamlit Auto-Reload
- When you save changes to `app.py`, Streamlit auto-detects
- Click **"Rerun"** in the browser, or press **'R'**
- Or enable **"Always rerun"** in Streamlit settings

### Multi-Window Setup for Presentation
1. **VS Code** - Show code (F11 for full screen)
2. **Browser** - Show dashboard (F11 for full screen)
3. **Alt+Tab** - Switch between them during demo

---

## 🎯 Presentation Setup in VS Code

### Before Your Presentation:

1. **Increase Font Size** (for better visibility)
   ```
   Ctrl + =  (zoom in)
   Ctrl + -  (zoom out)
   ```

2. **Clean Up Terminal**
   ```bash
   clear  # or cls on Windows
   ```

3. **Hide Unnecessary Panels**
   - Close extra files
   - Hide sidebar (Ctrl+B)
   - Focus on terminal and code

4. **Launch Dashboard**
   ```bash
   streamlit run app.py
   ```

5. **Open in Browser & Go Full Screen (F11)**

---

## 🚀 One-Command Setup

Create a script: `launch_dashboard.sh` (Mac/Linux) or `launch_dashboard.bat` (Windows)

**Mac/Linux:**
```bash
#!/bin/bash
echo "🚀 Launching Waste Collection Dashboard..."
cd "$(dirname "$0")"
pip install -q -r requirements.txt
streamlit run app.py
```

**Windows:**
```batch
@echo off
echo 🚀 Launching Waste Collection Dashboard...
pip install -q -r requirements.txt
streamlit run app.py
```

Make it executable:
```bash
chmod +x launch_dashboard.sh
./launch_dashboard.sh
```

---

## ✅ Verification Checklist

Before presentation, verify in VS Code:

- [ ] Open project folder in VS Code
- [ ] Terminal opens successfully (Ctrl + `)
- [ ] Python interpreter is set correctly
- [ ] Dependencies installed: `pip list | grep streamlit`
- [ ] Dashboard launches: `streamlit run app.py`
- [ ] Browser opens to http://localhost:8501
- [ ] Dashboard loads without errors
- [ ] Can navigate all 4 tabs
- [ ] "Run Optimization" button works

---

## 🎊 You're Ready!

**Simplest way:**
1. Open VS Code
2. Open terminal: **Ctrl + `**
3. Run: `streamlit run app.py`
4. Click the URL
5. Present! 🌟

---

**Need help?** Check the troubleshooting section above or refer to:
- `DASHBOARD_INSTRUCTIONS.md` - Dashboard usage guide
- `PRESENTATION_SUMMARY.md` - Presentation talking points
- `QUICK_START.md` - Quick reference

**Good luck with your presentation!** 🚀
