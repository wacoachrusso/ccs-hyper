# CCS Hyper - Flight Log & Crew Tracking App

CCS Hyper is a modern, web-based application designed for airline crews to track their schedules, log flights, manage crew lists, and view detailed statistics. It integrates directly with Supabase for a secure and scalable backend and is deployed as a JAMstack application on Netlify.

## Features

*   **Flight Log:** Automatically parse and log trip pairings and individual flights from CCS print-view schedules.
*   **Crew Lists:** Maintain personal lists of "Friends I Fly With" and "Do Not Fly" crew members, with notifications for upcoming trips.
*   **Statistics:** View detailed statistics about your flying history, including block hours, miles flown, and aircraft types.
*   **Google Calendar Sync:** Sync your flight schedule directly to your Google Calendar.
*   **PWA Support:** Installable as a Progressive Web App on both mobile and desktop for a native-like experience.
*   **Secure Authentication:** User accounts are managed securely through Supabase Auth.
*   **Serverless Architecture:** Powered by Netlify Functions for backend logic, ensuring scalability and low maintenance.

## Tech Stack

*   **Frontend:** HTML, CSS, JavaScript, Bootstrap
*   **Backend:** Python (Flask) for local development, Node.js for serverless functions
*   **Database:** Supabase (PostgreSQL with RLS)
*   **Deployment:** Netlify (Frontend Hosting + Serverless Functions)
*   **Authentication:** Supabase Auth
*   **Scraping:** Selenium & BeautifulSoup
*   **Integrations:** Google Calendar API, Resend (Email), Stripe (Payments)

## Getting Started

For detailed instructions on how to deploy and run this application, please see the [DEPLOYMENT.md](DEPLOYMENT.md) guide.

### Quick Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ccs-hyper.git
    cd ccs-hyper
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    npm install
    ```

3.  **Set up environment variables:**
    *   Copy `.env.example` to `.env`.
    *   Fill in your Supabase, Google, and other API keys.

4.  **Run the development server:**
    ```bash
    netlify dev
    ```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
