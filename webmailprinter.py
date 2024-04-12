from imap_tools import MailBox, AND
import subprocess
import datetime
import smtplib
import sqlite3 as db
from cryptography.fernet import Fernet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import threading

class printreader():
    global print_queue
    print_queue = list()

    global notification_queue
    notification_queue = list()

    def log_init(file_sender, file_subject, file_request_time, number_of_files, end_queue, duration):
        logger_cmd = "INSERT INTO printer_log (file_sender, file_subject, file_request_time, total_attachments, end_queue, duration) VALUES ('{file_sender}', '{file_subject}', '{file_reqquest_time}', '{number_of_files}', '{end_queue}', '{duration}'    );".format(file_sender=file_sender, file_subject=file_subject, file_reqquest_time=file_request_time, number_of_files=number_of_files, end_queue=end_queue, duration=duration)
        printreader.sql_executer(logger_cmd)

    def decrypter(connection, token):
        get_key_cmd = 'SELECT variable_value FROM global_variables where vid=15'
        key = bytes(list(printreader.sql_executer(get_key_cmd))[0][0], "utf-8")
        suit = Fernet(key)
        user_password = str(suit.decrypt(bytes(token, "utf-8")), "utf-8")
        return user_password


    def sql_executer(CMD):
        connection = db.connect("webmailserver.db")
        res = connection.execute(CMD)
        if "INSERT" in CMD:
            connection.commit()
        return res
    
    def principal():
        connection = db.connect("webmailserver.db")
        service_running = list(connection.execute("SELECT variable_value FROM global_variables WHERE vid=18")[0][0])
        if service_running == "True":
            principal_imap_server_cmd = 'SELECT variable_value FROM global_variables WHERE vid=5'
            principal_imap_server = list(printreader.sql_executer(principal_imap_server_cmd))[0][0]
            
            principal_imap_mail_cmd = 'SELECT variable_value FROM global_variables WHERE vid=1'
            principal_imap_mail = list(printreader.sql_executer(principal_imap_mail_cmd))[0][0]

            principal_imap_encrypted_password_cmd = 'SELECT variable_value FROM global_variables WHERE vid=2'
            principal_imap_encrypted_password = list(printreader.sql_executer(principal_imap_encrypted_password_cmd))[0][0]
            principal_imap_decrypted_password = printreader.decrypter(connection, principal_imap_encrypted_password)

            mail_box = MailBox(principal_imap_server).login(principal_imap_mail, principal_imap_decrypted_password, initial_folder='INBOX')

            check_subject_variable_cmd = 'SELECT variable_value FROM global_variables WHERE vid=6'
            check_subject_variable = list(printreader.sql_executer(check_subject_variable_cmd))[0][0]

            if check_subject_variable == True:
                subject_for_search_cmd = 'SELECT variable_value FROM global_variables WHERE vid=10'
                subject_for_search = list(printreader.sql_executer(subject_for_search_cmd))[0][0]

                mail_box_messages = mail_box.fetch(criteria=AND(seen=False, subject=subject_for_search),
                                    mark_seen=True,
                                    bulk=True)
            else:
                mail_box_messages = mail_box.fetch(criteria=AND(seen=False),
                                mark_seen=True,
                                bulk=True)
            
            storage_media_dir_cmd = 'SELECT variable_value FROM global_variables WHERE vid=11'
            storage_media_dir = list(printreader.sql_executer(storage_media_dir_cmd))[0][0]

            print_attachments_check_cmd = 'SELECT variable_value FROM global_variables WHERE vid=16'
            print_attachments = list(printreader.sql_executer(print_attachments_check_cmd))[0][0]
            print_content_check_cmd = 'SELECT variable_value FROM global_variables WHERE vid=17'
            print_mail_content = list(printreader.sql_executer(print_content_check_cmd))[0][0]

            for message in mail_box_messages:
                from_mail = message.from_
                mail_subject = message.subject
                ct = datetime.datetime.now()
                if print_mail_content == "True":
                    message_attachments = len(message.attachments)+1
                else:
                    message_attachments = len(message.attachments)

                notification_queue.append([from_mail, message_attachments, ct])

                if print_mail_content == "True":
                    content_path = storage_media_dir+f"{message.uid}.txt"
                    with open(content_path, "w", encoding="utf-8") as content_file:
                        content_file.write(message.text)
                    print_command = 'Start-Process "{}" -Verb Print'.format(content_path)
                    print_queue.append(print_command)


                if print_attachments == "True":
                    for att in message.attachments:
                        with open((storage_media_dir+att.filename), "wb") as mail_file:
                            mail_file.write(att.payload)
                        mail_file_path = storage_media_dir + att.filename
                        print_command = 'Start-Process "{}" -Verb Print'.format(mail_file_path)
                        print_queue.append(print_command)
                
                et = datetime.datetime.now()

                printreader.log_init(from_mail, mail_subject, ct, message_attachments, et, str(et-ct))    

class printer():

    def subprocesses_print_caller(print_command):
        result = subprocess.run(['powershell', '-Command', print_command], capture_output=False, text=False)

    def printing():
            if len(print_queue) != 0:
                print_command = print_queue.pop(0)
                printer.subprocesses_print_caller(print_command)
                threading.Timer(10, printer.printing).start()

class emailer():

    def send_in_queue(to_mail, total_attachments, ct):
        connection = db.connect('webmailserver.db')
        smtp_server = list(connection.execute('SELECT variable_value FROM global_variables WHERE vid=6'))[0][0]
        smtp_port = int(list(connection.execute('SELECT variable_value FROM global_variables WHERE vid=7'))[0][0])
        smtp_mail = list(connection.execute('SELECT variable_value FROM global_variables WHERE vid=3'))[0][0]
        smtp_epass = list(connection.execute('SELECT variable_value FROM global_variables WHERE vid=4'))[0][0]
        avg_duration = list(connection.execute('SELECT AVG(duration) FROM printer_log'))[0][0]
        notification_html = list(connection.execute('SELECT variable_value FROM user_generated_forntend_preview WHERE uid=2'))[0][0]
        smtp_dpass = printreader.decrypter(connection, smtp_epass)
        me = smtp_mail
        you = to_mail
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Print Notification"
        msg['From'] = me
        msg['To'] = you

        if "||user_mail||" in notification_html:
            notification_html = notification_html.replace("||user_mail||", to_mail)
        if "||num_attachments||" in notification_html:
            notification_html = notification_html.replace("||num_attachments||", str(total_attachments))
        if "||queue_length||" in notification_html:
            notification_html = notification_html.replace("||queue_length||", str(len(print_queue)))
        if "||avg_job_duration||" in notification_html:
            notification_html = notification_html.replace("||avg_job_duration||", str(avg_duration))
        if "||estimated_time||" in notification_html:
            notification_html = notification_html.replace("||estimated_time||", str(avg_duration*(len(print_queue)+total_attachments)))
        if "||current_time||" in notification_html:
            notification_html = notification_html.replace("||current_time||", str(ct))
        
        html = notification_html

        part2 = MIMEText(html, 'html')
        msg.attach(part2)
        mail = smtplib.SMTP(smtp_server, smtp_port)
        mail.ehlo()
        mail.starttls()
        mail.login(smtp_mail, smtp_dpass)
        mail.sendmail(me, you, msg.as_string())
        mail.quit()


    def emailing():
        if len(notification_queue) != 0:
            notification = notification_queue.pop(0)
            emailer.send_in_queue(notification[0], notification[1], notification[2])
            threading.Timer(10, emailer.emailing).start()

class threader():
    def start_threader(func, interval):
        threading.Timer(interval, threader.start_threader, [func, interval]).start()
        func()

class improvement():

    def send_user_data():
        consolidated_user_data = improvement.collect_user_data()
        

    def collect_user_data():
        conn = db.connect("webmailserver.db")
        c = conn.cursor()
        uui = c.execute('SELECT variable_value FROM localPVMdesc WHERE lid=10')
        uui = uui.fetchall()
        uui = uui[0][0]

        current_version = c.execute('SELECT variable_value FROM localPVMdesc WHERE lid=3')
        current_version = current_version.fetchall()
        current_version = current_version[0][0]

        au = c.execute('SELECT variable_value FROM localPVMdesc WHERE lid=4')
        au = au.fetchall()
        au = au[0][0]

        uhd = c.execute('SELECT variable_value FROM localPVMdesc WHERE lid=9')
        uhd = uhd.fetchall()
        uhd = uhd[0][0]

        print_log_data = c.execute('SELECT * FROM printer_log')
        print_log_data = print_log_data.fetchall()

        condensed_user_data = {
            'unique_user_identifier': uui,
            'current_version': current_version,
            'auto_update': au,
            'user_help_dev': uhd,
            'print_log_data': print_log_data
        }

        return condensed_user_data
        
        

threader.start_threader(printreader.principal, 10.0)
threader.start_threader(printer.printing, 3.0)
threader.start_threader(emailer.emailing, 3.0)
threader.start_threader(improvement.send_user_data, 10.0)