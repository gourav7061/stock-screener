# 🚀 Deploy to Streamlit Cloud - NOW!

**Your app will be live at:** `https://stock-screener-YOUR_USERNAME.streamlit.app`

**Time needed:** 30 minutes | **Cost:** FREE ✅

---

## 📋 What You'll Do

1. ✅ Prepare files (5 min)
2. ✅ Push to GitHub (10 min)
3. ✅ Deploy on Streamlit Cloud (10 min)
4. ✅ Add secrets & test (5 min)
5. ✅ Share your app 🎉

---

## ⚡ QUICK START (Just the Commands)

Already know what you're doing? Copy-paste these:

```bash
# 1. Create .gitignore
cat > .gitignore << 'EOF'
.env
*.db
data/
.venv/
__pycache__/
.streamlit/
EOF

# 2. Prepare git
git init
git add .
git commit -m "Initial commit: stock screener"

# 3. Add GitHub (REPLACE YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/stock-screener.git
git branch -M main
git push -u origin main
```

Then go to https://share.streamlit.io and deploy!

Full details below ↓

---

## 📖 STEP-BY-STEP

### STEP 1: Prepare Files (Terminal)

**Goal:** Make sure only production code is pushed (no secrets, no large databases)

#### 1a. Create `.gitignore`

This file tells Git what NOT to push to GitHub (keeps secrets safe):

```bash
cat > .gitignore << 'EOF'
.env
*.db
data/
.venv/
__pycache__/
.streamlit/
credentials.json
token.json
EOF
```

**Verify it worked:**
```bash
cat .gitignore
```

You should see your list of files to ignore.

#### 1b. Verify `requirements.txt` exists

```bash
cat requirements.txt
```

If it shows your dependencies, good! If not, create it:

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

#### 1c. Verify project structure

```bash
# These should all exist:
ls dashboard/app.py
ls stockscreener/
ls requirements.txt
```

If all three show output, you're ready for step 2!

---

### STEP 2: Create GitHub Repository (Web Browser)

**Goal:** Create a GitHub repo to store your code

#### 2a. Create Repo

1. Open: https://github.com/new
2. Fill in:
   - **Repository name:** `stock-screener` ← Exactly this
   - **Description:** `Professional Stock Screener with Flexible Strategy Builder`
   - **Visibility:** **PUBLIC** ← Required for Streamlit Cloud
3. Click **"Create repository"**

You'll see this message:
```
…or push an existing repository from the command line
git remote add origin https://github.com/YOUR_USERNAME/stock-screener.git
git branch -M main
git push -u origin main
```

Copy your repository URL:
```
https://github.com/YOUR_USERNAME/stock-screener.git
```

---

### STEP 3: Push Code to GitHub (Terminal)

**Goal:** Upload your code to GitHub

#### 3a. Initialize git (if needed)

```bash
git init
```

#### 3b. Add all files

```bash
git add .
```

**Verify this only adds code files, NOT secrets:**
```bash
git status
```

You should see:
- ✅ dashboard/
- ✅ stockscreener/
- ✅ *.md files
- ❌ NO `.env`
- ❌ NO `data/`

#### 3c. Commit

```bash
git commit -m "Initial commit: stock screener dashboard with flexible strategy builder"
```

#### 3d. Add GitHub remote

Replace `YOUR_USERNAME` with your actual username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/stock-screener.git
```

#### 3e. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

**Wait for completion.** You should see:
```
Enumerating objects: 142, done.
...
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

#### 3f. Verify on GitHub

1. Go to: `https://github.com/YOUR_USERNAME/stock-screener`
2. You should see all your Python files
3. Verify NO `.env` file appears (it shouldn't, thanks to .gitignore)

---

### STEP 4: Deploy on Streamlit Cloud (Web Browser)

**Goal:** Make your app live on the internet

#### 4a. Go to Streamlit Cloud

Open: https://share.streamlit.io

#### 4b. Sign in with GitHub

Click **"Sign in with GitHub"** and authorize Streamlit to access your repos.

#### 4c. Create new app

Click **"Create app"** button (top right).

Fill in:
- **Repository:** `YOUR_USERNAME/stock-screener`
- **Branch:** `main`
- **Main file path:** `dashboard/app.py`

Click **"Deploy"**

#### 4d. Wait

You'll see:
```
⏳ Deploying...
🔨 Building...
📦 Installing dependencies...
▶️ Starting the app...
```

Takes **2-3 minutes**. Grab coffee! ☕

#### 4e. Your App is Live! 🎉

Once done, you'll see your public URL:

```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

**Bookmark this!** This is your public dashboard.

---

### STEP 5: Configure Secrets (Web Browser)

**Goal:** Add sensitive settings to Streamlit Cloud (not stored in code)

Your `.env` file isn't uploaded to GitHub (thanks to `.gitignore`), so you need to add secrets to Streamlit Cloud.

#### 5a. Go to App Settings

On your Streamlit Cloud app page, click the **⋯ (three dots)** in top right → **Settings**

#### 5b. Click "Secrets"

In the left sidebar, click **"Secrets"**

#### 5c. Add your secret

In the text area, paste:

```toml
SEC_EDGAR_USER_AGENT = "StockScreenerDashboard (your.email@example.com)"
```

Replace `your.email@example.com` with ANY email you want.

#### 5d. Save

Click **"Save"**

Your app will restart automatically.

---

### STEP 6: Test Your App (Web Browser)

#### 6a. Open your app

Go to: `https://stock-screener-YOUR_USERNAME.streamlit.app`

#### 6b. Verify it loads

You should see:
- ✅ Dashboard title: "📈 Professional Stock Screener"
- ✅ 5 pages in sidebar (Dashboard, Strategy Builder, etc.)
- ✅ No red error messages

#### 6c. Test Strategy Builder

1. Click **"Strategy Builder"** in sidebar
2. Paste this:

```json
{
  "name": "Test Strategy",
  "root": {
    "logic": "AND",
    "items": [
      {
        "metric": "sma50",
        "operator": ">",
        "compare_type": "metric",
        "compare_metric": "sma200"
      }
    ]
  }
}
```

3. Click **"Save Strategy"**
4. You should see: ✅ "Strategy saved successfully"

---

## ✅ You're Done! 🎉

Your dashboard is now:
- 🌐 Live on the internet
- 🔒 Secure with secrets
- 🔄 Auto-updating with code changes
- 📤 Ready to share

**Your public URL:**
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

---

## 📤 Update Your Code (Automatic)

To make changes:

```bash
# 1. Edit your code

# 2. Push to GitHub
git add .
git commit -m "Description of changes"
git push origin main
```

**That's it!** Streamlit Cloud automatically redeploys within 1-2 minutes. 🚀

No manual steps needed.

---

## 📊 Share Your App

Send this URL to anyone:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

They can:
- View your dashboard
- Explore strategies
- Run screeners
- Build custom strategies

**No installation needed!** They just click the link.

---

## 🆘 Help

### App won't load?

Check the logs:
1. Go to your Streamlit Cloud app
2. Click **"Logs"** (bottom right)
3. Look for error messages
4. Fix the error locally
5. Push to GitHub: `git push origin main`

### Forgot your URL?

Go to: https://share.streamlit.io

Your app is listed there.

### Want to delete the app?

On Streamlit Cloud, click **⋯** → **Delete app**

---

## 📚 Full Guides

- **[DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md)** - Complete detailed guide
- **[DEPLOY_QUICK_COMMANDS.md](DEPLOY_QUICK_COMMANDS.md)** - Just the commands

---

## 🎯 Next Steps

1. ✅ Deploy (you just did this!)
2. Load stock data:
   - Go to your live app
   - Click "Data Refresh" page
   - Click "Refresh Price Data"
   - Takes 30-60 min, only needed once
3. Create strategies
4. Test and iterate
5. Share with others!

---

**Congratulations! Your stock screener is live!** 🚀📈
