// Netlify serverless function for sending notifications via Resend

const { Resend } = require('resend');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    const resend = new Resend(process.env.RESEND_API_KEY);
    const { to, subject, html } = JSON.parse(event.body);

    try {
        await resend.emails.send({
            from: 'CCS Hyper <notifications@yourdomain.com>',
            to: to,
            subject: subject,
            html: html,
        });

        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Notification sent successfully.' })
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};