from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta
import os, secrets, smtplib
from email.message import EmailMessage
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import (
    init_db,
    save_prediction,
    save_submission,
    update_prediction_result,
    get_stats,
    create_user,
    get_user_by_email,
    get_user_by_login,
    get_user,
    verify_password,
    update_user,
    update_password,
    get_user_predictions,
    set_verified,
    save_auth_code,
    verify_auth_code,
    get_prediction,
    get_all_predictions,
    update_prediction_state,
    save_message,
    get_messages,
    mark_messages_read,
)
from predict import predict
from auth import login_required, admin_required

APP_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(APP_DIR / "templates"),
    static_folder=str(APP_DIR / "static"),
)
app.secret_key = "visionassist-at-abandonment-secret-key"
init_db()


def login_session(user, role="user"):
    session.update(
        logged_in=True,
        role=role,
        user_id=user["id"],
        username=user["name"],
        email=user["email"],
    )


def send_email(to_email, subject, body):
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    port = int(os.getenv("SMTP_PORT", "587"))
    if not host or not user or not password:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.getenv("SMTP_FROM", user)
        msg["To"] = to_email
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception:
        return False


def issue_code(user_id, purpose, target):
    code = f"{secrets.randbelow(1000000):06d}"
    save_auth_code(
        user_id,
        purpose,
        target,
        code,
        (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
    )
    return code


def deliver_code(user, purpose, method):
    target = user["email"] if method != "phone" else (user["phone"] or user["email"])
    code = issue_code(user["id"], purpose, target)
    label = "verification" if purpose == "verify" else "password reset"
    sent = (
        send_email(
            user["email"],
            f"AT-RISK {label} code",
            f"Your AT-RISK {label} code is {code}. It expires in 10 minutes.",
        )
        if method != "phone"
        else False
    )
    return code, sent, target


def explain_prediction(row, result):
    factors = []
    actions = []
    if str(row["device_broken"] or "0") == "1":
        factors.append("The submitted feedback records a damaged or broken device.")
        actions.append(
            "Arrange repair or replacement support and confirm when the device is usable again."
        )
    if str(row["maintenance_available"] or "0") == "0":
        factors.append("Maintenance support was not reported as available.")
        actions.append("Connect the user with a local maintenance or service contact.")
    if str(row["user_trained"] or "0") == "0":
        factors.append("Training or orientation was not reported.")
        actions.append(
            "Offer a short practical training and check confidence using the device."
        )
    if (
        str(row["cost_affordable"] or "0") == "0"
        or str(row["financial_barrier"] or "0") == "1"
    ):
        factors.append("The feedback indicates a possible cost or financial barrier.")
        actions.append("Review funding, insurance, subsidy, or low-cost alternatives.")
    if str(row["satisfaction"] or "0") == "0":
        factors.append(
            "The submitted satisfaction response suggests the current solution may not meet expectations."
        )
        actions.append("Schedule a fit and needs review with the support team.")
    if not factors:
        factors.append(
            "No specific barrier flag was selected in the submitted answers."
        )
        actions.append(
            "Continue routine follow-up and check device use again at the next review."
        )
    message = f"Your feedback has been reviewed. The estimated abandonment risk is {result['risk']} ({result['risk_score']}%). "
    if str(row["device_broken"] or "0") == "1":
        message += (
            "Your device issue has been flagged for repair or replacement follow-up."
        )
    elif result["risk"] == "High":
        message += "The support team recommends an early follow-up conversation."
    elif result["risk"] == "Medium":
        message += "A follow-up check is recommended to prevent barriers from growing."
    else:
        message += "Please continue using the device and contact support if any barrier appears."
    return " ".join(factors), " ".join(actions), message


@app.context_processor
def shared_context():
    return {
        "unread_messages": (
            len(get_messages(True)) if session.get("role") == "admin" else 0
        )
    }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    return render_template("role_select.html")


@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        user = get_user_by_login(request.form.get("username", ""))
        if not user or not verify_password(user, request.form.get("password", "")):
            return render_template(
                "user_login.html", error="Invalid name or password."
            )
        if int(user["verified"] or 0) == 0:
            code, sent, target = deliver_code(
                user, "verify", request.form.get("verification_method", "email")
            )
            session["pending_user_id"] = user["id"]
            session["pending_code_demo"] = code
            return render_template(
                "otp_verify.html",
                info=f"Your account is not verified. A code was prepared for {target}.",
                demo_code=None if sent else code,
            )
        login_session(user)
        return redirect(url_for("user_dashboard"))
    return render_template("user_login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not name or not password:
            return render_template(
                "register.html",
                error="Please enter your name and password.",
            )

        if get_user_by_login(name):
            return render_template(
                "register.html",
                error="That name is already registered. Please choose another name or log in.",
            )

        # The legacy database keeps email NOT NULL for old records. This internal
        # placeholder is never shown as a required user field or used for login.
        safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip(
            "-"
        )
        local_email = f"{safe_name}-{secrets.token_hex(4)}@local.at-risk"
        user_id = create_user(name, local_email, password, phone)

        if not user_id:
            return render_template(
                "register.html",
                error="This account could not be created. Please try another name.",
            )

        set_verified(user_id)
        user = get_user(user_id)
        login_session(user)
        return redirect(url_for("user_dashboard"))

    return render_template("register.html")


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_user_id" not in session:
        return redirect(url_for("register"))
    if request.method == "POST":
        uid = session["pending_user_id"]
        if not verify_auth_code(uid, "verify", request.form.get("otp", "")):
            return render_template(
                "otp_verify.html",
                error="That code is invalid or expired.",
                demo_code=session.get("pending_code_demo"),
            )
        set_verified(uid)
        session.pop("pending_user_id", None)
        session.pop("pending_code_demo", None)
        user = get_user(uid)
        login_session(user)
        return redirect(url_for("user_dashboard"))
    return render_template(
        "otp_verify.html", demo_code=session.get("pending_code_demo")
    )


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        login_value = request.form.get("username", "").strip()
        user = get_user_by_login(login_value)
        if not user:
            return render_template(
                "forgot_password.html",
                error="No account was found for that name.",
            )
        code, sent, target = deliver_code(
            user, "reset", "phone" if user["phone"] else "email"
        )
        session["reset_user_id"] = user["id"]
        session["reset_code_demo"] = code
        return render_template(
            "reset_password.html",
            info="A reset code was prepared for your account.",
            demo_code=None if sent else code,
        )
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["POST"])
def reset_password():
    uid = session.get("reset_user_id")
    if not uid or not verify_auth_code(uid, "reset", request.form.get("otp", "")):
        return render_template(
            "forgot_password.html", error="Reset code is invalid or expired."
        )
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    if len(new) < 6 or new != confirm:
        return render_template(
            "reset_password.html",
            error="Passwords must match and contain at least 6 characters.",
            demo_code=session.get("reset_code_demo"),
        )
    update_password(uid, new)
    session.pop("reset_user_id", None)
    session.pop("reset_code_demo", None)
    return render_template(
        "user_login.html", success="Password reset successfully. You can now log in."
    )


@app.route("/user-dashboard")
@login_required
def user_dashboard():
    if session.get("role") != "user":
        return redirect(url_for("login"))
    records = get_user_predictions(session["user_id"])
    return render_template("user_dashboard.html", records=records, stats=get_stats())


@app.route("/form")
@login_required
def form():
    return (
        render_template("input_form.html")
        if session.get("role") == "user"
        else redirect(url_for("login"))
    )


@app.route("/submit-assessment", methods=["POST"])
@login_required
def submit_assessment():
    if session.get("role") != "user":
        return redirect(url_for("login"))
    data = request.form.to_dict()
    if data.get("device_received") not in {"0", "1"}:
        return (
            render_template(
                "input_form.html", error="Please answer the Device Received question."
            ),
            400,
        )
    payload = {
        "user_id": session["user_id"],
        **{
            k: data.get(k)
            for k in (
                "year",
                "age",
                "scenario",
                "setting",
                "sex",
                "device_needed",
                "disability_type",
                "device_source",
                "assessed",
                "appropriate_fit",
                "user_trained",
                "locally_manufactured",
                "maintenance_available",
                "device_broken",
                "cost_affordable",
                "insurance_covered",
                "financial_barrier",
                "availability_barrier",
                "distance_barrier",
                "functional_improvement",
                "independence_improved",
                "participation_improved",
                "satisfaction",
                "unmet_need",
            )
        },
        "risk": "Not applicable" if data["device_received"] == "0" else None,
        "risk_score": None,
        "status": "not_applicable" if data["device_received"] == "0" else "submitted",
    }
    save_submission(payload)
    return render_template(
        "dashboard.html", submitted=True, not_applicable=data["device_received"] == "0"
    )


@app.route("/predict", methods=["POST"])
@admin_required
def make_prediction():
    prediction_id = request.form.get("prediction_id", type=int)
    row = get_prediction(prediction_id) if prediction_id else None
    if not row or row["status"] != "submitted":
        return redirect(url_for("admin_dashboard"))
    try:
        result = predict(dict(row))
        explanation, action_plan, user_message = explain_prediction(row, result)
        update_prediction_result(
            prediction_id,
            result["risk"],
            result["risk_score"],
            explanation,
            action_plan,
            user_message,
        )
        target = get_user(row["user_id"])
        (
            send_email(target["email"], "AT-RISK feedback reviewed", user_message)
            if target
            else None
        )
    except Exception as exc:
        update_prediction_state(prediction_id, status="error")
        return redirect(
            url_for(
                "admin_dashboard",
                error=f"Prediction failed for #{prediction_id}: {exc}",
            )
        )
    return redirect(url_for("admin_record_detail", prediction_id=prediction_id))


@app.route("/admin/predict-all", methods=["POST"])
@admin_required
def predict_all():
    completed = 0
    for row in get_all_predictions():
        if row["status"] != "submitted":
            continue
        try:
            result = predict(dict(row))
            explanation, action_plan, user_message = explain_prediction(row, result)
            update_prediction_result(
                row["id"],
                result["risk"],
                result["risk_score"],
                explanation,
                action_plan,
                user_message,
            )
            target = get_user(row["user_id"])
            (
                send_email(target["email"], "AT-RISK feedback reviewed", user_message)
                if target
                else None
            )
            completed += 1
        except Exception:
            update_prediction_state(row["id"], status="error")
    return redirect(url_for("admin_dashboard", predicted=completed))


@app.route("/report")
@login_required
def report():
    prediction = (
        get_prediction(session.get("latest_prediction_id"), session["user_id"])
        if session.get("latest_prediction_id")
        else None
    )
    if not prediction or prediction["status"] != "predicted":
        return redirect(url_for("user_dashboard"))
    return render_template(
        "report.html", result=session.get("latest_result"), prediction=prediction
    )


@app.route("/report/<int:prediction_id>/pdf")
@login_required
def report_pdf(prediction_id):
    prediction = get_prediction(prediction_id, session["user_id"])
    if not prediction or prediction["status"] != "predicted":
        return redirect(url_for("user_dashboard"))
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60
    pdf.setFillColorRGB(0.06, 0.46, 0.43)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(50, y, "AT-RISK")
    pdf.setFillColorRGB(0.12, 0.16, 0.22)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y - 38, "Assistive Technology Risk Report")
    pdf.setFont("Helvetica", 11)
    y -= 82
    lines = [
        f"Report ID: AT-{prediction['id']:04d}",
        f"Generated: {prediction['created_at']}",
        f"Risk level: {prediction['risk']}",
        f"Risk score: {prediction['risk_score']}%",
        f"Device need: {prediction['device_needed'] or 'Not recorded'}",
        f"Disability type: {prediction['disability_type'] or 'Not recorded'}",
        f"Setting: {prediction['setting'] or 'Not recorded'}",
        "",
        "This report is a screening aid, not a medical diagnosis.",
        "Please discuss device barriers with an appropriate healthcare professional.",
    ]
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 22
    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"at-risk-report-{prediction_id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/my-records")
@login_required
def my_records():
    if session.get("role") != "user":
        return redirect(url_for("login"))
    return render_template(
        "history.html", records=get_user_predictions(session["user_id"])
    )


@app.route("/records/<int:prediction_id>")
@login_required
def user_record_detail(prediction_id):
    row = get_prediction(prediction_id, session["user_id"])
    return (
        render_template("record_detail.html", record=row, is_admin=False)
        if row
        else redirect(url_for("user_dashboard"))
    )


@app.route("/records/<int:prediction_id>/bookmark", methods=["POST"])
@login_required
def bookmark_record(prediction_id):
    row = get_prediction(prediction_id, session["user_id"])
    if row:
        update_prediction_state(
            prediction_id, is_bookmarked=0 if row["is_bookmarked"] else 1
        )
    return redirect(request.referrer or url_for("user_dashboard"))


@app.route("/records/<int:prediction_id>/status", methods=["POST"])
@login_required
def update_record_status(prediction_id):
    row = get_prediction(prediction_id, session["user_id"])
    if row:
        update_prediction_state(prediction_id, status=request.form.get("status", "new"))
    return redirect(request.referrer or url_for("user_dashboard"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        current_user = get_user(session["user_id"])
        if update_user(session["user_id"], name, current_user["email"], phone):
            session.update(username=name)
            return render_template(
                "profile.html",
                user=get_user(session["user_id"]),
                success="Profile updated successfully.",
            )
        return render_template(
            "profile.html",
            user=get_user(session["user_id"]),
            error="Your profile could not be updated.",
        )
    return render_template("profile.html", user=get_user(session["user_id"]))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current, new, confirm = (
            request.form.get("current_password", ""),
            request.form.get("new_password", ""),
            request.form.get("confirm_password", ""),
        )
        if not verify_password(get_user(session["user_id"]), current):
            return render_template(
                "settings.html", error="Current password is incorrect."
            )
        if len(new) < 6 or new != confirm:
            return render_template(
                "settings.html",
                error="Use a 6+ character password and make both new passwords match.",
            )
        update_password(session["user_id"], new)
        return render_template(
            "settings.html", success="Password changed successfully."
        )
    return render_template("settings.html")


@app.route("/assistant")
@login_required
def assistant():
    return render_template("assistant.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username", "").strip() == "admin"
            and request.form.get("password", "").strip() == "admin123"
        ):
            session.update(
                logged_in=True,
                role="admin",
                username="Administrator",
                email="admin@at-risk.local",
            )
            return redirect(url_for("admin_dashboard"))
        return render_template(
            "admin_login.html", error="Invalid administrator credentials."
        )
    return render_template("admin_login.html")


@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        stats=get_stats(),
        records=get_all_predictions(),
        messages=get_messages(),
    )


@app.route("/admin/submissions")
@admin_required
def admin_submissions():
    return render_template("admin_submissions.html", records=get_all_predictions())


@app.route("/admin/inbox")
@admin_required
def admin_inbox():
    return render_template("admin_inbox.html", messages=get_messages())


@app.route("/admin/records/<int:prediction_id>")
@admin_required
def admin_record_detail(prediction_id):
    row = get_prediction(prediction_id)
    return (
        render_template("record_detail.html", record=row, is_admin=True)
        if row
        else redirect(url_for("admin_dashboard"))
    )


@app.route("/admin/records/<int:prediction_id>/state", methods=["POST"])
@admin_required
def admin_record_state(prediction_id):
    update_prediction_state(
        prediction_id,
        status=request.form.get("status"),
        is_bookmarked=int(request.form.get("is_bookmarked", 0)),
    )
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/messages/read", methods=["POST"])
@admin_required
def read_messages():
    mark_messages_read()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin-profile", methods=["GET", "POST"])
@admin_required
def admin_profile():
    if request.method == "POST":
        return render_template(
            "profile.html",
            user={"name": "Administrator", "email": "admin@at-risk.local", "phone": ""},
            success="Admin profile preferences saved.",
            admin=True,
        )
    return render_template(
        "profile.html",
        user={"name": "Administrator", "email": "admin@at-risk.local", "phone": ""},
        admin=True,
    )


@app.route("/admin-settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        mark_messages_read()
        return render_template(
            "settings.html", success="Notification settings saved.", admin=True
        )
    return render_template("settings.html", admin=True)


@app.route("/api/stats")
@admin_required
def api_stats():
    return jsonify(get_stats())


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        internal_email = session.get("email", "no-email@local.at-risk")
        if name and message:
            save_message(
                session.get("user_id"),
                name,
                internal_email,
                subject or "Support enquiry",
                message,
            )
            if os.getenv("ADMIN_EMAIL"):
                send_email(
                    os.getenv("ADMIN_EMAIL"),
                    "AT-RISK new feedback",
                    f"{name}\n{subject}\n\n{message}",
                )
            return render_template(
                "contact.html",
                success="Feedback sent. The admin team has been notified.",
            )
        return render_template(
            "contact.html",
            error="Please enter your name and message.",
        )
    return render_template("contact.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
