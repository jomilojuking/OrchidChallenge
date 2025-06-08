# 🌸 Orchids SWE Intern Challenge

This project is a submission for the **Orchids SWE Intern Challenge**. It includes:

- ⚙️ A **FastAPI** backend using [`uv`](https://github.com/astral-sh/uv)
- 🖥️ A **Next.js + TypeScript** frontend
- 🧠 Integration with **Bright Data** and **Anthropic Claude API**

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend/` folder with the following variables:

```env
API_TOKEN=your-brightdata-api-token
BROWSER_AUTH=your-browser-auth-string
BRIGHT_DATA_PASSWORD=your-brightdata-password
ANTHROPIC_API_KEY=your-anthropic-api-key
🛠️ Backend Setup (FastAPI)
✅ Make sure you have Python 3.10+ installed

✅ Install uv if you haven’t already:

pip install uv
Inside the backend/ folder:
uv sync
uv run fastapi dev
🔁 Go to the frontend/ directory

💾 Install dependencies:
npm install
▶️ Start the dev server:

npm run dev
🌐 Frontend runs at: http://localhost:3000

✅ Once everything is set up, the backend and frontend should work together smoothly. Follow the steps above, and you're good to go!
