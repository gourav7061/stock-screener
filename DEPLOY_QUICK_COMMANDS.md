# Streamlit Cloud Deployment - Quick Commands

Copy-paste these commands in order. Takes ~30 minutes total.

---

## 🔑 BEFORE YOU START

1. Create GitHub account: https://github.com/signup (if you don't have one)
2. Know your GitHub username
3. Have terminal/PowerShell open in your project directory

---

## ✅ STEP 1: Prepare Files (5 minutes)

### Create .gitignore

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

### Verify files exist

```bash
# Check these files/folders exist in your project
ls dashboard/app.py
ls stockscreener/
ls requirements.txt
cat requirements.txt
```

If `requirements.txt` is missing, create it:

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

---

## 📤 STEP 2: Push to GitHub (10 minutes)

### 2a. Initialize Git

```bash
# Check if git repo exists
git status

# If error, initialize:
git init
```

### 2b. Add files to git

```bash
git add .
git status  # Verify .env and data/ are NOT listed
```

### 2c. Create commit

```bash
git commit -m "Initial commit: stock screener dashboard"
```

### 2d. Create GitHub repo (WEB ONLY - No command)

1. Go to: https://github.com/new
2. Repository name: `stock-screener`
3. Visibility: **PUBLIC** (required for Streamlit Cloud)
4. Click **"Create repository"**
5. Copy the URL shown (looks like: `https://github.com/YOUR_USERNAME/stock-screener.git`)

### 2e. Add GitHub remote

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/stock-screener.git
```

### 2f. Push code to GitHub

```bash
git branch -M main
git push -u origin main
```

**Output should show:**
```
Enumerating objects: ...
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

### 2g. Verify on GitHub (WEB ONLY)

1. Go to: `https://github.com/YOUR_USERNAME/stock-screener`
2. You should see all your files
3. Make sure NO `.env` or `data/` folder appears

---

## 🚀 STEP 3: Deploy on Streamlit Cloud (10 minutes)

### 3a. Go to Streamlit Cloud (WEB ONLY)

1. Open: https://share.streamlit.io
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit

### 3b. Create App (WEB ONLY)

1. Click **"Create app"** (top right button)
2. Fill in:
   - **Repository:** `YOUR_USERNAME/stock-screener`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
3. Click **"Deploy"**

### 3c. Wait for Deployment

The page will show:
```
⏳ Deploying...
Building the virtual environment...
Installing dependencies...
Starting the app...
```

**Takes 2-3 minutes.** Refresh if it seems stuck.

### 3d. Get Your Public URL (WEB ONLY)

Once deployed, you'll see:
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

✅ **Your app is LIVE!** Bookmark this URL.

---

## 🔐 STEP 4: Add Secrets (5 minutes)

### 4a. Go to Settings (WEB ONLY)

1. On your Streamlit Cloud app page
2. Click **⋯ (three dots)** → **Settings**

### 4b. Add Secret (WEB ONLY)

1. Click **"Secrets"** in left sidebar
2. In the text area, paste:

```toml
SEC_EDGAR_USER_AGENT = "StockScreenerDashboard (your.email@example.com)"
```

Replace `your.email@example.com` with your email.

3. Click **"Save"**
4. App will restart automatically (2-3 seconds)

---

## ✅ STEP 5: Test Deployment (5 minutes)

### 5a. Open Your App (WEB ONLY)

1. Go to: `https://stock-screener-YOUR_USERNAME.streamlit.app`
2. You should see the dashboard with 5 pages

### 5b. Test Strategy Builder

1. Click **"Strategy Builder"** in sidebar
2. Scroll down to "Define Strategy"
3. Paste this:

```json
{
  "name": "Test",
  "root": {
    "logic": "AND",
    "items": [
      {"metric": "sma50", "operator": ">", "compare_type": "metric", "compare_metric": "sma200"}
    ]
  }
}
```

4. Click **"Save Strategy"**
5. You should see: ✅ "Strategy saved successfully"

### 5c. Done! 🎉

Your dashboard is live and working!

---

## 📝 Update Your Code (Automatic Deployment)

Whenever you make changes to your code:

```bash
git add .
git commit -m "Describe your changes"
git push origin main
```

**Streamlit Cloud automatically redeploys** within 1-2 minutes. No manual steps!

---

## 🆘 If Something Goes Wrong

### App won't load?

```bash
# Check logs on Streamlit Cloud
# Click your app → "Logs" button (bottom right)
# Look for error messages
```

### Git push failed?

```bash
# If you get "permission denied", try:
git push origin main --force

# Or check your GitHub token is valid
git config --list | grep github
```

### Module not found error?

```bash
# Make sure these files exist in your repo:
git ls-files | grep -E "(app.py|requirements.txt|stockscreener)"

# If missing, add them:
git add dashboard/
git add stockscreener/
git add requirements.txt
git commit -m "Add missing files"
git push origin main
```

---

## 📊 Your App is Now Live!

**Share this URL with anyone:**
```
https://stock-screener-YOUR_USERNAME.streamlit.app
```

They can:
- View your dashboard
- Create strategies
- Run screeners
- NO installation needed!

---

## 🔄 Next: Load Data (Optional)

Once deployed, you can load stock data:

1. Go to your live app
2. Click **"Data Refresh"** page
3. Click **"Refresh US Companies Universe"**
4. Click **"Refresh Price Data"**
5. Wait for completion

This takes 30-60 minutes but only needed once.

---

## ⭐ Done!

You now have:
- ✅ Code on GitHub
- ✅ Live dashboard on Streamlit Cloud
- ✅ Public URL to share
- ✅ Auto-deployment on code changes

**Enjoy!** 🚀
