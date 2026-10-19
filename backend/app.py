from flask import Flask, render_template
from auth import auth
from dashboard import dashboard
from phishing import phishing_bp
from usb_baiting import usb_baiting
from fakejoboff import fakejoboff_bp
from password_attack import password_attack
from baiting import baiting
from social_media_privacy import social_media_privacy
from fake_shopping import fake_shopping
from smishing import smishing
from fake_otp import fake_otp
from permission_checker import permission_checker
from url_inspection import url_inspection
from deepfake_voice import deepfake_voice
from vulnerability_assessment import vulnerability_assessment

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = "SEVT_SECRET_KEY"

# Register auth blueprint
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(phishing_bp)
app.register_blueprint(usb_baiting)
app.register_blueprint(fakejoboff_bp)
app.register_blueprint(password_attack)
app.register_blueprint(baiting)
app.register_blueprint(social_media_privacy)
app.register_blueprint(fake_shopping)
app.register_blueprint(smishing)
app.register_blueprint(fake_otp)
app.register_blueprint(permission_checker)
app.register_blueprint(url_inspection)
app.register_blueprint(deepfake_voice)
app.register_blueprint(vulnerability_assessment)

# -----------------------
# HOME PAGE
# -----------------------
@app.route("/")
def home():
    return render_template("01 home.html")



# -----------------------
# RUN APPLICATION
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)