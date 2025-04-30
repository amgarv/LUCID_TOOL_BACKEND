# LUCID GPT Qualtrics Backend

This repository contains the Python Flask backend server required for the LUCID GPT Qualtrics chat interface toolkit. It acts as a proxy to the OpenAI API, enabling researchers to conduct human-AI interaction studies within Qualtrics.

[Download the LUCID User Guide (.docx)](https://github.com/amgarv/LUCID_TOOL_BACKEND/raw/main/LUCIDToolkitUserGuide.docx)

Academic Citation for the LUCID Toolkit:

Garvey, Aaron M. and Simon J. Blanchard, (2025) “Generative AI as a Research Confederate: The “LUCID” Methodological Framework and Toolkit for Controlled Human-AI Interactions Research in Marketing,” Working Manuscript.

## Quick Deploy to Vercel

Click the button below to deploy your own instance of this backend service to Vercel. This provides the necessary API endpoint for your Qualtrics tool.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Famgarv%2FLUCID_TOOL_BACKEND&project-name=lucid-tool-backend&repository-name=my-lucid-backend-code&env=OPENAI_API_KEY&envDescription=INSTRUCTIONS%3A%20For%20OPENAI_API_KEY%20input%20your%20OpenAI%20API%20key%20(available%20at%20%22Learn%20more%22%20link%20below).&envLink=https%3A%2F%2Fplatform.openai.com%2Faccount%2Fapi-keys)

<a href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Famgarv%2FLUCID_TOOL_BACKEND&project-name=lucid-tool-backend&repository-name=my-lucid-backend-code&env=OPENAI_API_KEY&envDescription=INSTRUCTIONS%3A%20For%20OPENAI_API_KEY%20input%20your%20OpenAI%20API%20key%20(available%20at%20%22Learn%20more%22%20link%20below).&envLink=https%3A%2F%2Fplatform.openai.com%2Faccount%2Fapi-keys" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 15px 25px; background-color: #0070f3; color: white; text-align: center; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
  CLICK HERE TO SET UP YOUR LUCID BACKEND ON VERCEL
</a>

## Deployment Steps (Using the Deploy Button)

1.  **Click the "Deploy with Vercel" button** above.
2.  **Connect Git Provider:** When prompted, connect your GitHub account.
3.  **Create Project:**
    * Vercel will suggest a **Project Name**. You can keep it or change it (e.g., `my-lucid-backend-code`). This name will determine your default backend deployment URL that will be used by Qualtrics, so use a name you are comfortable with others (such a reviewers) potentially seeing.
    * Click "Create". Vercel will create a copy of the LUCID code from the repository into your account.
4.  **Configure Project:** This is crucial. After the project is created, Vercel will prompt you for:
    * **`OPENAI_API_KEY`**:
        * **Purpose:** Allows LUCID to access OpenAI ChatGPT models.
        * **Action:** Go to [OpenAI API Keys](https://platform.openai.com/api-keys), create a new "Secret key", copy it, and paste it into the `OPENAI_API_KEY` value field in Vercel. 
        * **Optional but Recommended:** For security, it is a good practice to disable your secret key on the OpenAI platform when you are not actively collecting data with a LUCID Qualtrics study. You can then re-enable the key on the OpenAI platform when you field a study.
6.  **Deploy:** Click the "Deploy" button in Vercel.
7.  **Wait:** Vercel will build and deploy your backend. This usually takes 1-2 minutes.

## Getting Your Backend URL for Qualtrics

1.  **Visit Your Deployment:** Once Vercel shows the deployment is complete ("Congratulations!"), click the image displayed that says in blue text "LUCID Backend Succesfully Deployed!".
2.  **Copy the Qualtrics URL:** The resulting page you visit should display "LUCID Backend Successfully Deployed!". It will clearly show the **exact URL needed for Qualtrics**. Click the "Copy Backend URL" button. Keep this URL handy for the Qualtrics setup.

## Qualtrics Setup

1.  Take the full URL you copied from your deployment's landing page (e.g., `https://your-project-name.vercel.app/lucid`).
2.  In your Qualtrics survey, go to the **Survey Flow**.
3.  Set the value of the Embedded Data field named `LUCIDBackendURL` exactly to the URL you copied.

Your Qualtrics tool should now be able to communicate with your deployed LUCID backend.

---