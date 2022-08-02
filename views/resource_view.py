import json
from datetime import datetime
from flask import current_app, session, redirect, url_for, render_template, Flask, Blueprint, send_file, request
from app import jawa_logger
import os
from werkzeug.utils import secure_filename

from bin.load_home import load_home
from bin.view_modifiers import response

log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'jawa.log'))
server_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'server.json'))
resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources'))
files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'files'))
img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'img'))

blueprint = Blueprint('resources_view', __name__, template_folder='templates')


@blueprint.route('/resources/files', methods=['GET', 'POST'])
def files():
    if 'username' not in session:
        return load_home()
    target_file = request.args.get('target_file')
    button_choice = request.args.get('button_choice')
    if target_file:
        if button_choice == "Download":
            jawa_logger().info(f"[{session.get('url')}] {session.get('username')} downloading file: {target_file}.")
            return send_file(f'{files_dir}/{target_file}', as_attachment=True)
        elif button_choice == "Delete":
            jawa_logger().info(f"[{session.get('url')}] {session.get('username')} deleting file: {target_file}.")
            if os.path.exists(os.path.join(files_dir, target_file)):
                os.remove(os.path.join(files_dir, target_file))
    if request.method == "POST":
        jawa_logger().info(f"[{session.get('url')}] {session.get('username')} {request.path} {request.method}")
        upload_files_list = request.files.getlist('upload')
        for each_upload in upload_files_list:
            if ' ' in each_upload.filename:
                each_upload.filename = each_upload.filename.replace(" ", "-")
            jawa_logger().info(f"[{session.get('url')}] {session.get('username')} uploaded {each_upload.filename}.")
            each_upload.save(os.path.join(files_dir, secure_filename(each_upload.filename)))
    jawa_logger().info(f"[{session.get('url')}] {session.get('username')} {request.path} {request.method}")
    file_list = os.listdir(files_dir)
    for file in file_list:
        if file[0] == '.':
            file_list.remove(file)
    print(file_list)
    files_list = []
    for each_file in file_list:
        mtime = os.path.getmtime(os.path.join(files_dir, each_file))
        pretty_mtime = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        files_list.append({"name": each_file, "mtime": pretty_mtime})
    return render_template('resources/files.html', username=session.get('username'), files_repo=files_dir,
                           files=files_list)


@blueprint.route('/branding', methods=['GET', 'POST'])
@response(template_file='setup/branding.html')
def rebrand():
    if 'username' not in session:
        return redirect(url_for('logout'))
    if not os.path.isfile(server_file):
        with open(server_file, "w") as fout:
            json.dump({}, fout)
    with open(server_file) as fin:
        server_json = json.load(fin)
    brand = server_json.get('brand')
    if request.method == "POST":
        upload_files_list = request.files.getlist('upload')
        if new_name := request.form.get('new_name'):
            server_json['brand'] = new_name
            brand = new_name

            with open(server_file, 'w') as fout:
                json.dump(server_json, fout, indent=4)
        if upload_files_list:
            if target_file := upload_files_list[0]:
                os.rename(f"{img_dir}/jawa_icon.png", f"{img_dir}/old_jawa_icon_{datetime.now()}.png")
                target_file.save(os.path.join(img_dir, "jawa_icon.png"))
                return redirect(url_for('resources_view.rebrand'))
            return {'username': session.get('username'), "app_name": brand}
        return {'username': session.get('username'), "app_name": brand}

    return {'username': session.get('username'), "app_name": brand}


@blueprint.route("/python")
@response(template_file="resources/python.html")
def python():
    if 'username' not in session:
        return redirect(url_for('logout'))
    return {"username": session.get('username')}


@blueprint.route("/bash")
@response(template_file="resources/bash.html")
def bash():
    if 'username' not in session:
        return redirect(url_for('logout'))
    return {"username": session.get('username')}


