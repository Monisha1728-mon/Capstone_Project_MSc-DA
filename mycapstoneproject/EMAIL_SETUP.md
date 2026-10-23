# Email notifications and OTP

The project works locally without email credentials. In that mode, verification and reset codes are shown on the page as a temporary local demo code.

To send real emails, set these environment variables before starting Flask in PowerShell:

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:SMTP_FROM="your-email@gmail.com"
$env:ADMIN_EMAIL="admin-email@example.com"
python app\app.py
```

For Gmail, use a Google App Password rather than your normal password. The app sends:

- account verification codes
- password-reset codes
- a user email after an administrator completes a prediction
- a new-feedback email to `ADMIN_EMAIL`

The phone option is kept safe for local development: without an SMS provider it shows the code on screen. Real SMS delivery needs an SMS provider such as Twilio and its credentials; no SMS credentials are included in the project.
