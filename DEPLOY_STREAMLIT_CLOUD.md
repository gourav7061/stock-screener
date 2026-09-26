# Deploy to Streamlit Cloud - Complete Guide

Deploy your stock screener dashboard to the cloud in **30 minutes**. Your app will be live at:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

---

## 📋 Prerequisites

- ✅ GitHub account (create at https://github.com/signup)
- ✅ Streamlit Community Cloud account (free, uses GitHub login)
- ✅ Project files ready

---

## 🔑 Step 1: Prepare for GitHub

### 1a. Create `.gitignore` (Prevent Secrets & Large Files)

```bash
cat > .gitignore << 'EOF'
# Environment & Secrets
.env
.env.local
.env.*.local
credentials.json
token.json

# Database
*.db
data/
.tmp/

# Virtual Environment
.venv/
venv/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
eggs/
.eggs/
lib/
lib64/
parts/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# Streamlit
.streamlit/
EOF
```

**Verify it was created:**
```bash
cat .gitignore
```

### 1b. Clean Up Repository

Remove any uncommitted changes:
```bash
# See what will be committed
git status

# If needed, clean up
git clean -fd
```

### 1c. Create `requirements.txt` (If Missing)

```bash
cat > requirements.txt << 'EOF'
python-dotenv==1.0.1
google-auth==2.31.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
google-api-python-client==2.110.0
streamlit>=1.28.0
yfinance>=0.2.32
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
plotly>=5.17.0
tenacity>=8.2.0
EOF
```

Verify:
```bash
cat requirements.txt
```

---

## 🔗 Step 2: Create GitHub Repository

### 2a. Create Repo on GitHub (Web)

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `stock-screener`
   - **Description:** `Professional Stock Screener with Flexible Strategy Builder`
   - **Visibility:** **Public** (required for Streamlit Cloud)
   - Leave everything else as default
3. Click **"Create repository"**

### 2b. Copy Repository URL

After creation, you'll see this screen. Copy the URL shown:
```
https://github.com/YOUR_USERNAME/stock-screener.git
```

You'll use this in the next step.

---

## 📤 Step 3: Push Code to GitHub

### 3a. Initialize Git (If Not Already Done)

```bash
# Check if git is already initialized
git status

# If not, initialize
git init
```

### 3b. Add All Files

```bash
# Add all files (respecting .gitignore)
git add .

# Verify what will be added
git status
```

**Important:** Make sure you see:
- ✅ Python files, markdown files
- ✅ requirements.txt
- ❌ NO `.env` file
- ❌ NO `*.db` files
- ❌ NO `.venv` folder

### 3c. Create First Commit

```bash
git commit -m "Initial commit: stock screener dashboard with flexible strategy builder"
```

### 3d. Add Remote Repository

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/stock-screener.git
```

### 3e. Push to GitHub

```bash
# Set main branch
git branch -M main

# Push code
git push -u origin main
```

**Output should show:**
```
Enumerating objects: ...
Counting objects: ...
Writing objects: ...
...
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

### 3f. Verify on GitHub

1. Go to `https://github.com/YOUR_USERNAME/stock-screener`
2. You should see:
   - ✅ All your Python files
   - ✅ requirements.txt
   - ✅ dashboard/ folder
   - ✅ stockscreener/ folder
   - ❌ NO `.env`
   - ❌ NO `data/` folder

---

## 🚀 Step 4: Deploy on Streamlit Cloud

### 4a. Go to Streamlit Cloud

1. Open **https://share.streamlit.io**
2. Sign in with GitHub (click "Sign in with GitHub")
3. Authorize Streamlit Community Cloud to access your repositories

### 4b. Create New App

1. Click **"Create app"** (button in top right)
2. Fill in:
   - **Repository:** `YOUR_USERNAME/stock-screener`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
3. Click **"Deploy"**

### 4c. Wait for Deployment

You'll see:
```
Deploying...
⏳ Building the virtual environment...
⏳ Installing dependencies...
⏳ Starting the app...
✅ Deployed successfully!
```

This takes **2-3 minutes**.

### 4d. Your App is Live! 🎉

Once deployed, you'll see:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

Click the URL or bookmark it. Your dashboard is now public!

---

## 🔐 Step 5: Configure Secrets

Your `.env` file contains secrets (API keys, email). Streamlit Cloud won't access your local `.env`, so you need to add secrets in the cloud.

### 5a. Go to App Settings

1. On your Streamlit Cloud app page, click **⋯ (three dots)** → **Settings**
2. Click **"Secrets"** in left sidebar

### 5b. Add Secrets

In the "Secrets" editor, add:

```toml
SEC_EDGAR_USER_AGENT = "StockScreenerDashboard (your.email@example.com)"
```

Replace `your.email@example.com` with your actual email.

### 5c. Save and Restart

1. Click **"Save"**
2. Your app will automatically restart with the new secrets

---

## ✅ Step 6: Test Your Deployment

### 6a. Open Your App

Go to your app URL:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

You should see:
- ✅ Dashboard loads
- ✅ 5 pages in sidebar (Dashboard, Strategy Builder, Run Screener, Fundamentals, Data Refresh)
- ✅ No error messages

### 6b. Test Strategy Builder

1. Click **"Strategy Builder"** in sidebar
2. Paste this example strategy:

```json
{
  "name": "Test Strategy",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"}
    ]
  }
}
```

3. Click **"Save Strategy"**
4. You should see a success message

### 6c. Check Logs

If anything breaks, go to your Streamlit Cloud dashboard and click **"Logs"** to see error messages.

---

## 🔄 Step 7: Update Your Code

Whenever you make changes:

```bash
# Make your changes to files

# Commit
git add .
git commit -m "Describe what changed"

# Push to GitHub
git push origin main
```

**Streamlit Cloud automatically redeploys** when you push! 🚀

No manual steps needed.

---

## 📊 Share Your App

Your app is now public at:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

**Share this URL with:**
- Friends
- Colleagues
- Social media
- GitHub repository

---

## 🆘 Troubleshooting

### Problem: "App failed to load"

**Solution 1:** Check logs
- Go to your Streamlit Cloud app
- Click **"Logs"** button (bottom right)
- Look for error messages

**Solution 2:** Missing requirements
- Add missing packages to `requirements.txt`
- Push to GitHub
- App redeploys automatically

**Solution 3:** Database issue
- Streamlit Cloud can't access your local `data/stock_screener.db`
- You need to either:
  - A) Upload data via the Data Refresh page (first time)
  - B) Load sample data from a shared source

### Problem: "ModuleNotFoundError: No module named 'stockscreener'"

**Solution:**
1. Check your repository structure:
   - `dashboard/app.py` exists ✓
   - `stockscreener/` folder exists ✓
2. Check `.gitignore` doesn't exclude these folders
3. Push changes:
   ```bash
   git add .
   git commit -m "Fix: ensure all modules are in repo"
   git push origin main
   ```

### Problem: "Streamlit Cloud says 'Secrets' feature is locked"

**Solution:** This is a free tier limitation. You have two options:

**Option A:** Use environment variables
Replace the Secrets UI with direct code:
```python
import os
user_agent = os.environ.get("SEC_EDGAR_USER_AGENT", "StockScreenerDashboard (default)")
```

Then add to GitHub Actions secrets (advanced).

**Option B:** Use Streamlit+ paid tier (optional)

For now, Option A works fine for basic setup.

### Problem: "Port already in use" error

**Solution:** This only happens locally. Not an issue in Streamlit Cloud.

If deploying locally and getting this error:
```bash
streamlit run dashboard/app.py --server.port 8502
```

---

## 📈 Monitor Your App

### View App Analytics

1. Go to **https://share.streamlit.io**
2. Click your app
3. You'll see:
   - Total viewers
   - Recent activity
   - Performance metrics

### View Logs

On your app page:
- Click **"Logs"** (bottom right)
- See real-time errors and output

### Set Up Custom Domain (Optional)

Streamlit Cloud supports custom domains. Go to **Settings** → **Custom domain** to set up your own URL.

---

## 🎯 Common Next Steps

### Add More Data

1. Deploy your app (done! ✅)
2. Go to your live app: `https://stock-screener-YOUR_USERNAME.streamlit.app`
3. Click **"Data Refresh"** page
4. Click **"Refresh US Companies Universe"**
5. Click **"Refresh Price Data"**
6. Wait for completion

This loads data into the cloud database.

### Create Custom Strategies

1. Go to **Strategy Builder** page
2. Create your strategies
3. Go to **Run Screener** page
4. Test them on different stocks

### Export Results

1. Run a strategy in **Run Screener**
2. Click **"Download as CSV"**
3. Use results in Excel or analysis tools

### Share with Others

Send them your app URL:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

They can:
- View strategies
- Run screeners
- Explore data
- NO local installation needed!

---

## ✅ Deployment Checklist

- [ ] Created `.gitignore` (prevents secrets leakage)
- [ ] Created `requirements.txt` (all dependencies)
- [ ] Committed code: `git commit -m "..."`
- [ ] Added GitHub remote: `git remote add origin ...`
- [ ] Pushed to GitHub: `git push origin main`
- [ ] Verified files on GitHub (no `.env`, no `data/`)
- [ ] Created Streamlit Cloud app
- [ ] Deployed successfully
- [ ] Added secrets (SEC_EDGAR_USER_AGENT)
- [ ] Tested Strategy Builder (created + saved strategy)
- [ ] Got public URL: `https://stock-screener-YOUR_USERNAME.streamlit.app`

---

## 📚 Quick Reference

| Step | Command |
|------|---------|
| Create `.gitignore` | `cat > .gitignore << 'EOF'` |
| Add files to git | `git add .` |
| Commit | `git commit -m "message"` |
| Add GitHub remote | `git remote add origin URL` |
| Push to GitHub | `git push -u origin main` |
| View logs | Streamlit Cloud → Logs button |
| Update code | Make changes → `git push origin main` (auto-redeploys) |

---

## 🎉 You're Done!

Your stock screener dashboard is now:
- ✅ Live on the internet
- ✅ Accessible 24/7
- ✅ Shareable with anyone
- ✅ Auto-updating with code changes

**Your app is at:**
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

**Next:** Share it with others, load data, and start screening! 🚀
