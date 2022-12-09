import os
import smtplib
import requests
import json
import pandas as pd
from threading import Thread
from csv import DictReader
from flask import Flask, render_template, Markup, request, url_for, redirect, flash, jsonify
from flask_bootstrap import Bootstrap
from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStrorage
from flask_track_usage.storage.mongo import MongoEngineStrorage
from datetime import date, datetime

THIS_YEAR = date.today().year

app = Flask(__name__) 
Bootstrap(app)

status = None
event_pages_data = "event_pages_new.csv"

# email details
EMAIL_PW = os.getenv("GM_EMAIL_PW")
SENDER_EMAIL = "pickled.sprout.bay@gmail.com"
RECEIVER_EMAIL = "s.schultchen@gmx.com"


def send_email(name, email, message):
    """sends email"""
    email_message = f"Subject:Message from STM webpage\n\nName: {name}\nEmail: {email}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.ehlo()
        connection.starttls()  # make connection secure (Transport Layer Security)
        connection.ehlo()
        connection.login(user=SENDER_EMAIL, password=EMAIL_PW)
        connection.sendmail(
        from_addr=SENDER_EMAIL, to_addrs=RECEIVER_EMAIL, msg=email_message.encode("utf-8"))




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
        csv_data = list(DictReader(csv_file))
        # remove items that are marked with "page not found"
        list_of_events = [i for i in csv_data if not (
            i['title'] == "page not found")]
        list_of_events = [i for i in csv_data if not (
            i['council_abbr'] == "out")]
        update_time = list_of_events[0]['update_date']
        total_events = len(list_of_events)
    with open('./event_pages.csv', newline='', encoding="utf8") as csv_file:
        csv_data = list(DictReader(csv_file))
        # remove duplicates based on column name
        list_of_event_pages = {
            i['name']: i for i in reversed(csv_data)}.values()
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
            print(
                f"name:{name} email:{email} message:{message} email_PW:{EMAIL_PW}")
            send_email(name, email, message)
            # NEED TO SEND MESSAGE TO USER ON SENT
            # flash("Message sent succesfully. Thank you.")
            return redirect(url_for('home'))
        else:
            return render_template("index.html", events=list_of_events, pages=list_of_event_pages, time=update_time, event_count=total_events, year=THIS_YEAR)

    return render_template("index.html", events=list_of_events, pages=list_of_event_pages, time=update_time, event_count=total_events, year=THIS_YEAR)

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
