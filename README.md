# LUCID GPT Qualtrics Backend

This repository contains the Python Flask backend server required for the LUCID GPT Qualtrics chat interface toolkit. It acts as a proxy to the OpenAI API, enabling researchers to conduct human-AI interaction studies within Qualtrics.

## Quick Deploy to Vercel

Click the button below to deploy your own instance of this backend service to Vercel. This provides the necessary API endpoint for your Qualtrics tool.

[![Deploy with Vercel](https://vercel.com/button)](
https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Famgarv%2FLUCID_TOOL_BACKEND&project-name=lucid-tool-backend&repository-name=my-LUCID-backend-code&env=OPENAI_API_KEY,ALLOWED_ORIGINS&envDescription=OpenAI%20secret%20key%20and%20comma-separated%20CORS%20allowlist&envLink=https%3A%2F%2Fplatform.openai.com%2Faccount%2Fapi-keys)

## Deployment Steps (Using the Deploy Button)

1.  **Click the "Deploy with Vercel" button** above.
2.  **Connect Git Provider:** When prompted, connect your GitHub account and click "Import". Vercel will create a copy of the LUCID code from the repository into your account.
3.  **Configure Project:**
    * Vercel will suggest a **Project Name**. You can keep it or change it (e.g., `lucid-tool-backend`). This name will determine your default backend deployment URL that will be used by Qualtrics, so use a name you are comfortable with others (such a reviewers) potentially seeing.
4.  **Set Environment Variables:** This is crucial. Vercel will prompt you for:
    * **`openai_api_key`**:
        * **Purpose:** Allows LUCID to access OpenAI ChatGPT models.
        * **Action:** Go to [OpenAI API Keys](https://platform.openai.com/api-keys), create a new "Secret key", copy it, and paste it into the `openai_api_key` value field in Vercel.
    * **`ALLOWED_ORIGINS`**:
        * **Purpose:** Security setting (CORS) to control which website(s) (i.e., your Qualtrics survey) can access this backend.
        * **Action (Simplest Start - Use Caution):** You can leave this field **blank** during the Vercel setup. The Vercel LUCID backend will default to allowing requests from *any* origin (`*`). This is easy for testing but **less secure** and other people will be able to user your endpoint (if you adopt this more flexible but less secure approach I recommend disabling the backend between studies).
        * **Action (Recommended):** Find your Qualtrics survey URL (e.g., by previewing the survey). Copy the main origin part (e.g., `https://youruniversity.qualtrics.com` or `https://subdomain.youruniversity.qualtrics.com`). Paste *only this origin* into the `ALLOWED_ORIGINS` value field in Vercel. This is more secure.
        * **Action (Multiple Origins):** For multiple origins, you enter comma-separated origins like: `https://youruniversity.qualtrics.com,http://coauthoruniversity.qualtrics.com`.
5.  **Deploy:** Click the "Deploy" button in Vercel.
6.  **Wait:** Vercel will build and deploy your backend. This usually takes 1-2 minutes.

## Getting Your Backend URL for Qualtrics

1.  **Visit Your Deployment:** Once Vercel shows the deployment is complete ("Ready"), click the "Visit" button or navigate directly to the main deployment URL Vercel provides (e.g., `https://your-project-name.vercel.app`).
2.  **Copy the Qualtrics URL:** The page you visit should display "LUCID Backend Successfully Deployed!". It will clearly show the **exact URL needed for Qualtrics**.

## Qualtrics Setup

1.  Take the full URL you copied from your deployment's landing page (e.g., `https://your-project-name.vercel.app/lucid`).
2.  In your Qualtrics survey, go to the **Survey Flow**.
3.  Set the value of the Embedded Data field named `LUCIDBackendURL` exactly to the URL you copied.

Your Qualtrics tool should now be able to communicate with your deployed LUCID backend.

---
*(Add link to the main LUCID toolkit documentation)*