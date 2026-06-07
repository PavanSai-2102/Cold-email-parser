# Deployment Plan: The Closer (Cold Email Parser)

The project includes both a CLI interface (`main.py`) and a web dashboard built with Streamlit (`app.py`). To make the project accessible online without requiring a local setup, the best approach is to deploy the Streamlit web app.

Below are the proposed deployment strategies. Streamlit Community Cloud is highly recommended due to its native integration and free tier.

## Prerequisites & Secrets

Before deploying, you will need the following credentials configured as secrets in the cloud environment:
- `SMTP_USER` and `SMTP_PASSWORD` (or App Password)
- `LLM_API_KEY` (Groq API Key, if enabled)

## Option 1: Streamlit Community Cloud (Recommended)
This is the simplest way to deploy a Streamlit app directly from your GitHub repository.

**Steps:**
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **New app** and authorize Streamlit to access your GitHub repositories.
3. Select the `PavanSai-2102/Cold-email-parser` repository.
4. Set the **Branch** to `main`.
5. Set the **Main file path** to `app.py`.
6. Click **Advanced settings** and paste the contents of your `.env` file (excluding `DRY_RUN=true` if you want it live, though it's safer to keep it as true initially) into the **Secrets** text box.
7. Click **Deploy!**

## Option 2: Render (Alternative)
Render is a cloud platform that makes it easy to host web apps.

**Steps:**
1. Create an account on [Render](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub account and select the `Cold-email-parser` repository.
4. Fill in the deployment details:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT`
5. Scroll down to **Environment Variables** and add your secrets (e.g., `SMTP_USER`, `SMTP_PASSWORD`, `LLM_API_KEY`).
6. Select the **Free** instance type and click **Create Web Service**.

## Verification
1. Once deployed, open the provided public URL.
2. Upload a sample `contacts.csv` or `contacts.json` file.
3. Ensure the UI loads the contacts and displays the email preview successfully.
4. If using `LLM_ENABLED`, verify that the Groq API call completes without errors.
5. In `DRY_RUN` mode, click the "Send" button and verify that the logs update successfully without actually sending an email.
