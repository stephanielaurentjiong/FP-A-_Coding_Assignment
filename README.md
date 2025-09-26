# 🚀 How to Run CFO Copilot Locally

This guide will help you run the CFO Copilot app on your computer, even if you're not a programmer. Just follow these steps carefully!

## 🛠 Step 1: Install Python

### For Mac Users:
1. Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter)
2. Check if Python is already installed by typing:
   ```bash
   python3 --version
   ```
3. If you see something like "Python 3.8" or higher, you're good! Skip to Step 2.
4. If not, install Python from: https://www.python.org/downloads/
   - Download the latest version for Mac
   - Run the installer and follow the prompts

### For Windows Users:
1. Go to https://www.python.org/downloads/
2. Click "Download Python" (latest version)
3. Run the downloaded file
4. **IMPORTANT**: Check the box "Add Python to PATH" during installation
5. Click "Install Now"
6. Open **Command Prompt** (press `Win + R`, type "cmd", press Enter)
7. Test by typing: `python --version`

### For Linux Users:
Most Linux systems have Python pre-installed. Open terminal and check:
```bash
python3 --version
```
If not installed, use your package manager (e.g., `sudo apt install python3` for Ubuntu).

## 📁 Step 2: Download the App

### Option A: If you have the code folder already
- Skip to Step 3

### Option B: Download from GitHub (if this is a GitHub project)
1. Go to the GitHub repository page
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to your Desktop or Documents folder

### Option C: If someone sent you the folder
- Just make sure you have the folder with all the files

## 💻 Step 3: Open Terminal/Command Prompt

### Mac Users:
- Press `Cmd + Space`, type "Terminal", press Enter

### Windows Users:
- Press `Win + R`, type "cmd", press Enter

### Linux Users:
- Press `Ctrl + Alt + T` or search for "Terminal"

## 📂 Step 4: Navigate to the App Folder

In your terminal/command prompt, you need to go to the folder where the app is located.

1. Type `cd ` (with a space after "cd")
2. Drag and drop the FP-A-_Coding_Assignment folder from your file browser into the terminal window
3. Press Enter

Example:
```bash
cd /Users/yourname/Desktop/FP-A-_Coding_Assignment
```

You should see something like `FP-A-_Coding_Assignment$` or similar in your terminal.

## 🔧 Step 5: Install Required Software

Copy and paste these commands one by one (press Enter after each):

### Create a virtual environment (keeps things organized):
```bash
python3 -m venv .venv
```

### Activate the virtual environment:

**Mac/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

You should see `(.venv)` appear at the beginning of your command line.

### Install the required packages:
```bash
pip install -r requirements.txt
pip install streamlit
pip install plotly
```

This might take a few minutes. You'll see lots of text - that's normal!

## 🎉 Step 6: Run the App

Now for the exciting part! Type this command:

```bash
streamlit run app.py
```

You should see something like:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

## 🌐 Step 7: Open the App in Your Browser

The app should automatically open in your web browser. If it doesn't:

1. Open your web browser (Chrome, Firefox, Safari, etc.)
2. Go to: `http://localhost:8501`

## 🎯 Step 8: Use the App!

Congratulations! The CFO Copilot app is now running. You can:

### Try these sample questions:
- "What was June 2025 revenue vs budget?"
- "Show me gross margin trends for the last 3 months"
- "Break down OpEx by category for June"
- "What is our cash runway right now?"

### Use the interface:
- Click on the **"Ask Question"** tab
- Type your question in the text box
- Click **"Analyze"** button
- See your results with charts and organized data!

## 🛑 How to Stop the App

When you're done:
1. Go back to your terminal/command prompt
2. Press `Ctrl + C` (on both Mac and Windows)
3. Type `deactivate` to exit the virtual environment

## 🔄 Running the App Again Later

Next time you want to use the app:

1. Open Terminal/Command Prompt
2. Navigate to the folder: `cd /path/to/FP-A-_Coding_Assignment`
3. Activate virtual environment:
   - Mac/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Run the app: `streamlit run app.py`
5. Open browser to `http://localhost:8501`

## 🆘 Troubleshooting

### "Command not found" error:
- Make sure Python is properly installed and added to PATH
- Try `python` instead of `python3` (especially on Windows)

### "Permission denied" error:
- On Mac/Linux, try adding `sudo` before commands
- Make sure you're in the right folder

### "Module not found" error:
- Make sure virtual environment is activated (you should see `(.venv)`)
- Try running `pip install -r requirements.txt` again

### App won't open in browser:
- Manually go to `http://localhost:8501`
- Try `http://127.0.0.1:8501`
- Check if another app is using port 8501

### Still having issues?
- Make sure you followed each step exactly
- Try restarting your terminal and starting over
- Check that all files are in the FP-A-_Coding_Assignment folder

## 📞 Need Help?

If you're still stuck:
1. Double-check you followed every step
2. Try googling the specific error message
3. Ask a tech-savvy friend to help with the setup

## 🎉 You're All Set!

Enjoy exploring your financial data with the CFO Copilot! The app will help you analyze revenue, expenses, margins, and cash flow with just simple questions.

---

*This guide was written for non-technical users. If you're comfortable with programming, see the main README.md for developer instructions.*
