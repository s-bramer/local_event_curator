import os
import pandas as pd
from threading import Thread
from csv import DictReader
from flask import Flask, render_template, Markup, request, url_for, redirect, flash, jsonify
from flask_mail import Mail, Message
# from flask_track_usage import TrackUsage
# from flask_track_usage.storage.sql import SQLStrorage
# from flask_track_usage.storage.mongo import MongoEngineStrorage
from datetime import date

THIS_YEAR = date.today().year

app = Flask(__name__)
app.secret_key = "your_secret_key"

# status = None
# event_pages_data = "event_pages_new.csv"

# email details
EMAIL_PW = os.getenv("GM_EMAIL_PW")
SENDER_EMAIL = "pickled.sprout.bay@gmail.com"
RECEIVER_EMAIL = "s.schultchen@gmx.com"

# configure Flask-Mail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = SENDER_EMAIL
app.config["MAIL_PASSWORD"] = EMAIL_PW

mail = Mail(app)

# RUN SCRAPER FROM SITE | CURRENTLY INACTIVE
# def task():
#     global status
#     df_in = pd.read_csv(event_pages_data, header=0, index_col=None)
#     df_out_path = "events_database.csv"
#     df_out = pd.DataFrame()
#     for i, row in enumerate(range(0, len(df_in))):
#         link = str(df_in.iloc[row]['link'])
#         df_out = pd.concat(objs=[df_out, scraper.run_scraper(link, row, df_in)])
#         print(f"EVENTS: {len(df_out)}")
#         status = (i+1)*(10/len(df_in))
#     #SAVE DATAFRAME AS CSV
#     #first sort by sort_date
#     df_out = df_out.sort_values(by='sort_date',ascending=True,ignore_index=True)
#     #then remove month duplicates (for month subsection labels)
#     current_month = ""
#     for row in range(0, len(df_out)):
#         if df_out.loc[row, ('month')] != current_month:
#             current_month = df_out.loc[row, ('month')]
#         else:
#             #print(f"{df_out.loc[row, ('title')]} month {df_out.loc[row, ('month')]} deleted from row {row}")
#             df_out.loc[row, ('month')] = ""
#     df_out.to_csv(df_out_path,index=False)


# all Flask routes below
@app.route("/", methods=["GET", "POST"])
def home():
    print(request.method)
    with open('./events_database.csv', newline='', encoding="utf8") as csv_file:
        event_data = list(DictReader(csv_file))
        update_time = event_data[0]['update_date']
        total_events = len(event_data)
    with open('./event_pages.csv', newline='', encoding="utf8") as csv_file:
        event_page_data = list(DictReader(csv_file))
        # remove duplicates based on column name
        list_of_event_pages = {
            i['name']: i for i in reversed(event_page_data)}.values()
    # BUTTONS:
    if request.method == "POST":
        # rerun the scraper to update results | CURRENTLY INACTIVE
        if request.form.get('reload'):
            pass
            # t1 = Thread(target=task)
            # t1.start()
            # return redirect(url_for('home'))
        # send an email to you if someone makes a POST
        elif request.form.get('email'):
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')

            # send email
            msg = Message(
                "New message from website",
                recipients=[RECEIVER_EMAIL],
                sender=SENDER_EMAIL,
                body=f"Name: {name}\nEmail: {email}\nMessage: {message}"
            )
            mail.send(msg)

            flash("Thank you, your message has been sent.")

            # return redirect(url_for('home'))
            return redirect("/")
        else:
            return render_template("index.html", events=event_data, pages=list_of_event_pages, time=update_time, event_count=total_events, year=THIS_YEAR)

    return render_template("index.html", events=event_data, pages=list_of_event_pages, time=update_time, event_count=total_events, year=THIS_YEAR)

# PROGRESS BAR | CURRENTLY INACTIVE
# @app.route("/ajaxprogressbar",methods=["POST","GET"])
# def ajaxprogressbar():
#     msg = 'problem occured'
#     if request.method == 'POST':
#         # scraper.run_scraper('event_pages.csv')
#         msg = 'Results successfully updated!'
#     return jsonify(msg)


# @app.route('/status', methods=['GET'])
# def getStatus():
#     statusList = {'status':status}
#     print(f"getting status: {statusList}")
#     return json.dumps(statusList)

if __name__ == '__main__':
    app.run(debug=True)
