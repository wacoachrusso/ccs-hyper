# CCS Hyper Deployment Guide

This guide provides step-by-step instructions for deploying the CCS Hyper application using Supabase for the backend and Netlify for the frontend and serverless functions.

## Prerequisites

1.  **Accounts:**
    *   GitHub account
    *   Supabase account
    *   Netlify account
    *   Resend account (for email notifications)
    *   Stripe account (for payments)

2.  **Tools:**
    *   Git
    *   Python 3.8+
    *   Node.js and npm
    *   Netlify CLI (`npm install netlify-cli -g`)

## Step 1: Set Up Supabase

1.  **Create a New Project:**
    *   Go to your Supabase dashboard and create a new project.
    *   Choose a name (e.g., `ccs-hyper`) and select a region.
    *   Make sure to save the **Database Password** securely.

2.  **Run Database Migrations:**
    *   Navigate to the `SQL Editor` in your Supabase project dashboard.
    *   Open the `supabase_migrations.sql` file from this repository.
    *   Copy and paste the entire content into a new query window in the SQL Editor.
    *   Click `Run`. This will create all the necessary tables, policies, and functions.
    *   **Note:** The line `ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';` might fail due to permissions. This is okay to ignore for now unless you need a custom JWT secret.

3.  **Get API Keys:**
    *   Go to `Project Settings` > `API`.
    *   You will need the **Project URL** and the **`anon` public key**. Keep these handy for the next steps.

## Step 2: Set Up Netlify

1.  **Fork and Clone the Repository:**
    *   Fork this repository to your own GitHub account.
    *   Clone your forked repository to your local machine.

2.  **Create a New Site from Git:**
    *   Log in to your Netlify account.
    *   Click `Add new site` > `Import an existing project`.
    *   Connect to your Git provider (GitHub) and select your forked repository.

3.  **Configure Build Settings:**
    *   Netlify should automatically detect the `netlify.toml` file and configure the build settings:
        *   **Build command:** `python build.py`
        *   **Publish directory:** `dist`
        *   **Functions directory:** `netlify/functions`
    *   If not, enter these settings manually.

4.  **Add Environment Variables:**
    *   Go to `Site settings` > `Build & deploy` > `Environment`.
    *   Add the following environment variables:
        *   `PYTHON_VERSION`: `3.8` (or your preferred version)
        *   `SUPABASE_URL`: Your Supabase Project URL from Step 1.
        *   `SUPABASE_ANON_KEY`: Your Supabase `anon` public key from Step 1.
        *   `SUPABASE_SERVICE_ROLE_KEY`: Found in `Project Settings` > `API` (keep this secret!).
        *   `RESEND_API_KEY`: Your API key from Resend.
        *   `STRIPE_SECRET_KEY`: Your secret key from Stripe.

## Step 3: Deploy

1.  **Trigger a Deploy:**
    *   Go to the `Deploys` tab for your site in Netlify.
    *   Click `Trigger deploy` > `Deploy site`.
    *   Netlify will now build and deploy your application.

2.  **Verify Deployment:**
    *   Once the deploy is complete, visit your Netlify site URL.
    *   The CCS Hyper application should be live.
    *   Test the functionality, especially login/signup, to ensure it's correctly connected to your Supabase backend.

## Local Development

To run the application locally, you can use the Netlify CLI.

1.  **Create a `.env` file:**
    *   Copy the contents of `.env.example` to a new file named `.env`.
    *   Fill in the values with your local or development keys.

2.  **Install Dependencies:**
    *   Run `pip install -r requirements.txt`.

3.  **Run the Dev Server:**
    *   Run `netlify dev`.
    *   This will start the Flask development server and the Netlify serverless functions emulator.
    *   The application will be available at `http://localhost:8888`.

## Troubleshooting

*   **Function Errors (500):** Check the function logs in your Netlify dashboard to debug serverless function issues.
*   **Supabase Connection Issues:** Double-check that your `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correctly set in Netlify's environment variables.
*   **Build Failures:** Review the deploy log in Netlify. Common issues include missing dependencies or incorrect build commands.
