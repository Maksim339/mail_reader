import dotenv
import os
from datetime import datetime
import json
from credentials import credentials
from mail_tools import Mail
import time
from attachment_processing import *
import tempfile

env = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_path=env)
folder_path = "folder/"  # os.getenv('folder_path')
mail_path = os.getenv('server_path')
pidfile = os.getenv('pidfile')
index_file = open(os.getenv('index_file'))
index = None
current_file_path = None
fds = []
project_path = os.getcwd()

now = datetime.now()
date_now = now.strftime("%d-%m-%Y")
email_from = 'upload@gio.ru'
days = 0


# def check_logs():
#     try:
#         d1 = datetime.fromtimestamp(os.path.getctime('skrepka_file_logs.txt'))
#         d2 = datetime.now()
#         time_cla = d2 - d1
#         try:
#             days = int(str(time_cla).split(',')[0].split(' ')[0])
#         except ValueError as r:
#             r
#         if days > 0.9:
#             os.remove('skrepka_file_logs.txt')
#     except FileNotFoundError as e:
#         e
#
#
# def write_logs():
#     try:
#         logs = open("skrepka_file_logs.txt", "w+")
#         logs.write(f"filename | company | time | login_from | size\n")
#         logs.close()
#     except FileExistsError as e:
#         e
#     except PermissionError as e:
#         e

def time_logs(f_name, s_name, s_login):
    global folder_path
    time_created = os.path.getctime(os.path.join(folder_path, s_name, 'upload/scans/',
                                                 f_name))
    print('fileName=', f_name)
    time_for_logs = datetime.fromtimestamp(time_created)
    utctime = datetime.utcfromtimestamp(time_created)
    current_time = time.mktime(utctime.timetuple())
    index_time = str(index) + '(' + str(current_time) + ')'
    size = os.path.getsize(folder_path + s_name + '/upload/scans/' + f_name)
    mb_size = str(round(size / (1024 * 1024), 3)) + ' Megabytes'
    f = open("skrepka_file_logs.txt", "a")
    f.write(f"{f_name} | {s_name} | {time_for_logs} | {s_login} | {mb_size}\n")
    f.close()
    return index_time


def load_and_dump():
    global index
    index += -1
    with open("var/www/mail/index.json", "r") as jsonFile:
        data = json.load(jsonFile)

    data[f"{system_name}"] = index

    with open("var/www/mail/index.json", "w") as jsonFile:
        json.dump(data, jsonFile)


def check_folder_success(for_success):
    status = '-success'
    if not os.path.exists(for_success + status):
        os.rename(for_success, for_success + status)
    else:
        shutil.rmtree(for_success + status)
        os.rename(for_success, for_success + status)
    os.chmod(for_success + status, 0o0777)


def is_folder_existed():
    fds = []
    try:
        fds = os.listdir(os.path.join(folder_path, system_name, 'upload/scans'))
        return True, fds
    except Exception as e:
        return False, fds


if __name__ == "__main__":
    json_file = json.load(index_file)
    if os.path.exists(pidfile):
        print('Process already started')
    else:
        with open(pidfile, "w") as file:
            file.write(str(os.getpid()))
        try:
            for cred in credentials:
                mail_obj = Mail(cred)
                system_name, system_login = mail_obj.get_name_and_login()
                index = json_file[system_name]
                status_folder, fds = is_folder_existed()
                if not status_folder:
                    print('folder doesn\'t exist')
                elif not fds:
                    print(f'no new letters in "{system_name}" ')
                else:
                    for fileName in fds:
                        i_time = time_logs(fileName, system_name, system_login)
                        current_file_path = os.path.join(mail_path, system_name, system_login,
                                                         email_from, i_time, 'file_1')
                        os.makedirs(current_file_path, 0o777, True)
                        filePath = os.path.join(current_file_path, fileName)
                        original, extension = rename_with_extension(filePath, current_file_path,
                                                                    folder_path, system_name, fileName)
                        with tempfile.TemporaryDirectory() as path:
                            if extension == '.pdf':
                                pdf_processing(original, filePath, current_file_path)
                            elif extension == '.jpg' or extension == '.jpeg' or extension == '.png' or extension == '.tif':
                                image_processing(original, current_file_path)
                            else:
                                print('bad-extension: ' + extension)
                        for_success = os.path.join(mail_path, system_name, system_login,
                                                   email_from, i_time)
                        check_folder_success(for_success)
        except:
            print('Ooops')
            os.remove(pidfile)
    os.remove(pidfile)
