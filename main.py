import os
import scraper
import smtplib
import requests
from csv import DictReader
from flask import Flask, render_template, Markup, request, url_for, redirect, flash, jsonify
from flask_bootstrap import Bootstrap
from flask_table import Table, Col, LinkCol
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


app = Flask(__name__)
app.secret_key = "any-string-you-want-just-keep-it-secret"
Bootstrap(app)

#email details
EMAIL_PW = os.getenv("GM_EMAIL_PW")
SENDER_EMAIL = "pickled.sprout.bay@gmail.com"
RECEIVER_EMAIL = "s.schultchen@gmx.com"
def send_email(name, email, message):
    """sends email"""
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.ehlo()
        connection.starttls() #make connection secure (Transport Layer Security)
        connection.ehlo()
        connection.login(user=SENDER_EMAIL, password=EMAIL_PW)
        connection.sendmail(from_addr=SENDER_EMAIL, to_addrs=RECEIVER_EMAIL, msg=email_message.encode("utf-8"))

# all Flask routes below
@app.route("/", methods=["GET", "POST"])
def home():
    print(request.method)
    with open('./events_database.csv', newline='', encoding="utf8") as csv_file:
        csv_data = DictReader(csv_file)
        list_of_events = list(csv_data)
    with open('./event_pages.csv', newline='', encoding="utf8") as csv_file:
        csv_data = DictReader(csv_file)
        list_of_event_pages = list(csv_data)
    # BUTTONS:
    if request.method == "POST":
        # rerun the scraper to update results
        if request.form.get('reload'):
            print("LETS RELOAD!!!!!!!!!")
            # scraper.run_scraper('event_pages.csv')
            return redirect(url_for('home'))
        # send an email to you if someone makes a POST
        elif request.form.get('email'):
            print("LETS WRITE AN EMAIL!!!!!!!")
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            send_email(name, email, message)
            # NEED TO SEND MESSAGE TO USER ON SENT (see https://www.youtube.com/watch?v=abCSKRMGZ3A)
            #  flash("Message sent succesfully. Thank you.")
            return redirect(url_for('home'))
        else:
            return render_template("index.html", events=list_of_events, pages=list_of_event_pages)

    return render_template("index.html", events=list_of_events, pages=list_of_event_pages)

#progress bar when scraper is rerun and results updated
@app.route("/ajaxprogressbar",methods=["POST","GET"])
def ajaxprogressbar():
    msg = 'problem occured'
    if request.method == 'POST':
        scraper.run_scraper('event_pages.csv')
        msg = 'New record created successfully'
    return jsonify(msg)


if __name__ == '__main__':
    app.run(debug=True)
