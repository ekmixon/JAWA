#!/usr/bin/python
# encoding: utf-8
import os
import json
from time import sleep
import re
from werkzeug.utils import secure_filename
from flask import (Flask, request, render_template,
                   session, redirect, url_for, escape,
                   send_from_directory, Blueprint, abort)

from crontab import CronTab

from app import jawa_logger
from bin.view_modifiers import response

cron_json_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'cron.json'))
time_json_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'time.json'))
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

blueprint = Blueprint('cron', __name__)


@blueprint.route('/cron', methods=['GET', 'POST'])
@response(template_file='cron/home.html')
def cron_home():
    if 'username' not in session:
        return redirect(url_for('logout'))
    jawa_logger().info(f"[{session.get('url')}] {session.get('username').title()} viewed {request.path}")
    with open(cron_json_file, 'r') as fin:
        cron_json = json.load(fin)
    print(cron_json)
    return {"username": session.get('username'), "cron_list": cron_json}


@blueprint.route('/cron/new', methods=['GET', 'POST'])
def new_cron():
    if 'username' not in session:
        return redirect(url_for('logout'))
    jawa_logger().info(f"[{session.get('url')}] {session.get('username').title()} viewed {request.path}")
    with open(time_json_file, 'r+') as fin:
        content = fin.read()
        time_data = json.loads(content)

    days_data = time_data['days']
    hours_data = time_data['hours']
    frequencies_data = time_data['frequencies']

    i = 0
    days = []
    for item in days_data:
        days.append(days_data[i])
        i += 1

    i = 0
    hours = []
    for item in hours_data:
        hours.append(hours_data[i])
        i += 1

    i = 0
    frequencies = []
    for item in frequencies_data:
        frequencies.append(frequencies_data[i])
        i += 1

    if 'username' not in session:
        return render_template('home.html',
                               login="false")
    if request.method != 'POST':
        return render_template('cron/new.html',
                               cron="cron",
                               frequencies=frequencies,
                               days=days,
                               hours=hours,
                               username=str(escape(session['username'])))

    if ' ' in request.form.get('cron_name'):
        error_message = "Single-string name only."
        return render_template('error.html',
                               error_message=error_message,
                               error="error",
                               username=str(escape(session['username'])))

    cron_description = request.form.get('description')
    cron_name = request.form.get('cron_name')

    if not os.path.isdir(scripts_dir):
        os.mkdir(scripts_dir)
    owd = os.getcwd()
    os.chdir(scripts_dir)
    script = request.files['script']
    if ' ' in script.filename:
        script.filename = script.filename.replace(" ", "-")
        print(script.filename)
    new_script_name = f"cron_{cron_name}_{script.filename}"
    script.save(secure_filename(new_script_name))
    script_file = os.path.join(scripts_dir, new_script_name)

    os.chmod(script_file, mode=0o0755)
    os.chdir(owd)
    frequency = request.form.get('frequency')

    if not os.path.isfile(cron_json_file):
        data = []
        with open(cron_json_file, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    data = json.load(open(cron_json_file))

    for i in data:
        print(i)
        print(" ~ ~ ~ ~ ~")  # Mister Krabs
        if str(i['name']) == cron_name:
            error_message = "Name already exists!"
            return render_template('error.html',
                                   error_message=error_message,
                                   error="error",
                                   username=str(escape(session['username'])))
    try:
        cron = CronTab(user='jawa')
    except IOError as err:
        print(err)
        os.remove(script_file)
        return render_template('error.html', error=err, username=session.get('username'))

    data.append({"name": cron_name,
                 "description": cron_description,
                 "frequency": frequency,
                 "script": script_file})

    with open(cron_json_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    if frequency == "everyhour":
        job1 = cron.new(command=script_file, comment=cron_name)
        job1.every().hours()
        job1.minute.on(0)
        cron.write()

    if frequency == "everyday":
        time = request.form.get('daytime')
        job1 = cron.new(command=script_file, comment=cron_name)
        job1.day.every(1)
        job1.hour.on(time)
        job1.minute.on(0)
        cron.write()

    if frequency == "everyweek":
        day = request.form.get('weekday')
        time = request.form.get('weektime')
        job1 = cron.new(command=script_file, comment=cron_name)
        job1.dow.on(day)
        job1.hour.on(time)
        job1.minute.on(0)
        cron.write()

    if frequency == "everymonth":
        day = request.form.get('monthday')
        time = request.form.get('monthtime')
        job1 = cron.new(command=script_file, comment=cron_name)
        job1.day.on(day)
        job1.hour.on(time)
        job1.minute.on(0)
        cron.write()

    return render_template('success.html',
                           webhooks="success",
                           username=str(escape(session['username'])))


@blueprint.route('/cron/delete', methods=['GET', 'POST'])
def delete_cron():
    if 'username' not in session:
        return redirect(url_for('logout'))
    jawa_logger().info(f"[{session.get('url')}] {session.get('username')} viewed {request.path}")
    with open(cron_json_file) as fin:
        cron_json = json.load(fin)
    names = [str(cron_json[i]['name']) for i, item in enumerate(cron_json)]
    if not names:
        return render_template('cron/home.html',
                               username=str(escape(session['username'])))

    if request.method != 'POST':
        return render_template('cron/delete.html',
                               content=names,
                               delete_cron="delete_cron",
                               username=str(escape(session['username'])))
    timed_job = request.form.get('timed_job')

    data = json.load(open(cron_json_file))

    for d in data:
        if d['name'] == timed_job:
            script_path = (d['script'])
            new_script_path = f'{script_path}.old'
            if os.path.exists(script_path):
                os.rename(script_path, new_script_path)

    try:
        cron = CronTab(user='jawa')
    except IOError as err:
        print(err)
        return render_template('error.html', error=err, username=session.get('username'))

    for job in cron:
        if job.comment == timed_job:
            jawa_logger().info(f"[{session.get('url')}] {session.get('username')} removed cron job {timed_job}")
            cron.remove(job)
            cron.write()

    data[:] = [d for d in data if d.get('name') != timed_job]

    with open(cron_json_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    return render_template('success.html',
                           webhooks="success",
                           username=str(escape(session['username'])))
