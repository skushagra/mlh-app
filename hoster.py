import datetime
import random
from flask import Flask, request, render_template, redirect, send_file
import sqlite3
from cryptography.fernet import Fernet
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import requests
import logging
from blogs import get_blogs
# import webview

logging.basicConfig(filename='record.log', level=logging.DEBUG)
app = Flask(__name__)

def decrypt(password):
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    get_key_cmd = 'SELECT variable_value FROM global_variables where vid=15'
    key = bytes(list(c.execute(get_key_cmd))[0][0], "utf-8")
    suit = Fernet(key)
    user_password = str(suit.decrypt(bytes(password, "utf-8")), "utf-8")
    return user_password

def encrypt(password):
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    get_key_cmd = 'SELECT variable_value FROM global_variables where vid=15'
    key = bytes(list(c.execute(get_key_cmd))[0][0], "utf-8")
    suit = Fernet(key)
    user_password = str(suit.encrypt(bytes(password, "utf-8")), "utf-8")
    return user_password

def verify_user_email(email):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    smtp_email = "webprint.services@outlook.com"
    smtp_password = ""
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_email, smtp_password)
    OTP = random.randint(100000, 999999)
    ct = datetime.datetime.now()
    subject = "OTP for verification"
    message = f"""
    Your OTP for verification is {OTP}.

    Web Mail Printer Notifications
    {ct}
    """
    server.sendmail(smtp_email, email, message)
    server.quit()
    return OTP

@app.route('/')
def home():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    username = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=2"))[0][0]
    current_version = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=3"))[0][0]
    auto_update_pvm = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=4"))[0][0]
    current_version_release = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=5"))[0][0]
    last_update_date = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=6"))[0][0]
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]
    service_status = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=18"))[0][0]
    blogs = get_blogs()
    blog_data = []
    for i in range(len(blogs)):
        blog_data.append([blogs[f"{i+1}"]['blog_title'], blogs[f"{i+1}"]['blog_body'], blogs[f"{i+1}"]['uploaded_by'], blogs[f"{i+1}"]['uploaded_by_profile'], blogs[f"{i+1}"]['uploaded_on'], blogs[f"{i+1}"]['read_more_url']])
    if len(blogs) > 0:
        doblogs = True
    else:
        doblogs = False
    if iss == "True":
        return render_template(
            './index.html',
            username=username,
            current_version=current_version,
            auto_update_pvm=auto_update_pvm,
            current_version_release=current_version_release,
            last_update_date=last_update_date,
            css=css,
            sr=service_status,
            doblogs=doblogs,
            blogs=blog_data,
        )
    else:
        conn = sqlite3.connect('./webmailserver.db')
        date_data = list(str(datetime.date.today()).split('-'))
        uui = "pvm-" + str(date_data[0]) + "."  + str(date_data[1]) + str(date_data[2]) + str(random.randint(100000, 999999))
        conn.execute(f"UPDATE localPVMdesc SET variable_value = '{uui}' WHERE lid = 10")
        conn.commit()
        conn.close()
        return render_template(
            './setup.html',
        )

@app.route('/imap')
def imap():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    isa = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=5"))[0][0]
    ise = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=1"))[0][0]
    isp = decrypt(list(c.execute("SELECT variable_value FROM global_variables WHERE vid=2"))[0][0])
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]

    
    return render_template(
        './imap.html',
        iss=iss,
        isa=isa,
        ise=ise,
        isp=isp,
        css=css,
        page_name="imap",
    )

@app.route('/smtp')
def smpt():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    ssa = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=6"))[0][0]
    sse = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=3"))[0][0]
    ssport = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=7"))[0][0]
    sspass = decrypt(list(c.execute("SELECT variable_value FROM global_variables WHERE vid=4"))[0][0])
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]
    notification_html = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=2"))[0][0]



    
    return render_template(
        './smtp.html',
        iss=iss,
        ssa = ssa,
        sse = sse,
        ssport = ssport,
        sspass = sspass,
        css=css,
        notification_html=notification_html,
    )

@app.route('/log')
def log():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]

    print_data  = c.execute("select file_sender,file_subject,file_request_time,total_attachments,duration from printer_log ORDER BY pid DESC LIMIT 5;")
    print_data = print_data.fetchall()
    total_printed = c.execute("select sum(total_attachments) from printer_log;")
    total_printed = total_printed.fetchall()
    total_printed = total_printed[0][0]
    average_print_time = c.execute("select avg(duration) from printer_log;")
    average_print_time = average_print_time.fetchall()
    average_print_time = average_print_time[0][0]
    if average_print_time < 1:
        average_print_time = "< 1 sec"
    most_popular_user = c.execute("select file_sender from printer_log ORDER BY file_sender LIMIT 1;")
    most_popular_user = most_popular_user.fetchall()
    most_popular_user = most_popular_user[0][0]

    distinct_operation_dates = c.execute("SELECT DISTINCT SUBSTR(file_request_time, 1, 10) FROM printer_log;")
    distinct_operation_dates = distinct_operation_dates.fetchall()

    avg_att_days = list()

    for i in distinct_operation_dates:
        date_of_operation = i[0]
        att_data = c.execute(f'select total_attachments from printer_log where SUBSTR(file_request_time, 1, 10) ="{date_of_operation}";')
        tl = list()
        att_data = att_data.fetchall()
        for i in att_data:
            tl.append(i[0])
        avg_att_days.append(tl)
    
    avreage_attachments_per_day = list()
    for i in avg_att_days:
        avreage_attachments_per_day.append(sum(i)/len(i))
    
    average_atpd = sum(avreage_attachments_per_day)/len(avreage_attachments_per_day)
    average_atpd = round(average_atpd, 2)
    
    # avreage_attachments_per_day = 
    return render_template(
        './log.html',
        iss=iss,
        css=css,
        print_data=print_data,
        page_name="log",
        total_printed=total_printed,
        average_print_time=average_print_time,
        most_popular_user=most_popular_user,
        average_atpd=average_atpd,
        f="",
    )

@app.route('/dbece')
def dbece():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()

    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]
    pmc = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=17"))[0][0]
    pma = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=16"))[0][0]
    scn = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=12"))[0][0]
    csfs = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=9"))[0][0]
    cs = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=10"))[0][0]
    uhd = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=9"))[0][0]
    sfs = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=10"))[0][0]
    pmd = list(c.execute("SELECT variable_value FROM global_variables WHERE vid=11"))[0][0]

    return render_template(
        './dbexe.html',
        page_name="dbece",
        iss=iss,
        css=css,
        pmc=pmc,
        pma=pma,
        scn=scn,
        cs=cs,
        uhd=uhd,
        sfs=sfs,
        pmd=pmd,
        csfs=csfs,
    )

@app.route('/service-status')
def service_status():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    ss = list(c.execute('SELECT variable_value FROM global_variables WHERE vid = 18'))[0][0]
    if ss == "True":
        return {"service_status": "running"}
    else:
        return {"service_status": "stopped"}

@app.route('/rev-smtp-to-def-format')
def rstd():
    conn = sqlite3.connect('./webmailserver.db')
    smtpc = list(conn.execute("SELECT variable_value FROM localPVMdesc WHERE lid=11"))[0][0]
    update_cmd = f"""UPDATE user_generated_frontend_preview SET variable_value = '{smtpc}' WHERE uid = 2"""
    conn.execute(update_cmd)
    conn.commit()
    conn.close()
    return "success"

@app.route('/dbexe-update', methods=['POST'])
def dbexe_update():
    if request.form['changing'] == "sfs":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        nsfs = request.form['updater']
        update_cmd = f'UPDATE global_variables SET variable_value = "{nsfs}" WHERE vid = 10'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "msd":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        msd = request.form['updater']
        update_cmd = f'UPDATE global_variables SET variable_value = "{msd}" WHERE vid = 11'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "sdd":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        sdd = request.form['updater']
        if sdd == "True":
            sdd = "False"
            update_cmd = f'UPDATE localPVMdesc SET variable_value = "{sdd}" WHERE lid = 9'
        else:
            sdd = "True"
            update_cmd = f'UPDATE localPVMdesc SET variable_value = "{sdd}" WHERE lid = 9'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "csfs":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        csfs = request.form['updater']
        if csfs == "True":
            csfs = "False"
            update_cmd = f'UPDATE global_variables SET variable_value = "{csfs}" WHERE vid = 9'
        else:
            csfs = "True"
            update_cmd = f'UPDATE global_variables SET variable_value = "{csfs}" WHERE vid = 9'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "sun":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        sun = request.form['updater']
        if sun == "True":
            sun = "False"
            update_cmd = f'UPDATE global_variables SET variable_value = "{sun}" WHERE vid = 12'
        else:
            sun = "True"
            update_cmd = f'UPDATE global_variables SET variable_value = "{sun}" WHERE vid = 12'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "sun":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        sun = request.form['updater']
        if sun == "True":
            sun = "False"
            update_cmd = f'UPDATE global_variables SET variable_value = "{sun}" WHERE vid = 12'
        else:
            sun = "True"
            update_cmd = f'UPDATE global_variables SET variable_value = "{sun}" WHERE vid = 12'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "rk":
        conn = sqlite3.connect('./webmailserver.db')
        nk = Fernet.generate_key()
        nk = nk.decode("utf-8")
        smtp_pass = decrypt(list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=4"))[0][0])
        imap_pass = decrypt(list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=2"))[0][0])
        update_cmd = f'UPDATE global_variables SET variable_value = "{nk}" WHERE vid = 15'
        conn.execute(update_cmd)
        conn.commit()
        new_smtp_pass = encrypt(smtp_pass)
        new_imap_pass = encrypt(imap_pass)
        updateimap = f'UPDATE global_variables SET variable_value = "{new_imap_pass}" WHERE vid = 2'
        updatesmtp = f'UPDATE global_variables SET variable_value = "{new_smtp_pass}" WHERE vid = 4'
        conn.execute(updateimap)
        conn.execute(updatesmtp)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    
    if request.form['changing'] == "pma":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        pma = request.form['updater']
        if pma =="True":
            update_cmd = f'UPDATE global_variables SET variable_value = "False" WHERE vid = 16'
        else:
            update_cmd = f'UPDATE global_variables SET variable_value = "True" WHERE vid = 16'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')

    if request.form['changing'] == "smtp-notify-code":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        smtp_notify_code = request.form['updater']
        update_cmd = f'UPDATE user_generated_frontend_preview SET variable_value = "{smtp_notify_code}" WHERE uid = 2'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return {"status":"success"}
   
    if request.form['changing'] == "pmc":
        conn = sqlite3.connect('./webmailserver.db')
        c = conn.cursor()
        pmc = request.form['updater']
        if pmc =="True":
            update_cmd = f'UPDATE global_variables SET variable_value = "False" WHERE vid = 17'
        else:
            update_cmd = f'UPDATE global_variables SET variable_value = "True" WHERE vid = 17'
        c.execute(update_cmd)
        conn.commit()
        conn.close()
        return redirect('/dbece')
    

@app.route('/email-log', methods=['POST'])
def mail_logs():

    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    server = list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=6"))[0][0]   
    email = list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=3"))[0][0]
    port = list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=7"))[0][0]
    password = decrypt(list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=4"))[0][0])
    data = c.fetchall()
    file_path = list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=11"))[0][0] + "printer_log.csv"
    with open(file_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        conn.close()
    
    mail_to = request.form['email']
    mail_subject = "Web Mail Server Logs have been shared with you"
    mail_body = """
    Please find the attached file for the logs

    Regards,
    Web Mail Printer Notification
    """
    mail_attachment = file_path

    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = mail_to
    msg['Subject'] = mail_subject
    msg.attach(MIMEText(mail_body, 'plain'))

    with open(mail_attachment, 'rb') as f:
        attach = MIMEApplication(f.read(), _subtype='txt')
        attach.add_header('Content-Disposition', 'attachment', filename=mail_attachment)
        msg.attach(attach)
    
    mail_server = smtplib.SMTP(server, port)
    mail_server.starttls()
    mail_server.login(email, password)
    mail_server.sendmail(email, mail_to, msg.as_string())
    mail_server.quit()

    return {
        "status": "success"
    }

@app.route('/check-for-updates')
def check_for_updates():
        conn = sqlite3.connect("webmailserver.db")
        url = 'https://skushagra.github.io/pvm/latest.json'
        user_version = list(conn.execute("SELECT variable_value FROM localPVMdesc WHERE lid=3"))[0][0]
        response = requests.get(url)
        if response.status_code == 200:
            latest_version = response.json()
            if latest_version['latest_version'] != user_version:
                return 'True'
            elif latest_version['latest_version'] == user_version:
                return 'False'
        else:
            print('Failed to retrieve latest version data.')

@app.route('/block-user', methods=['POST'])
def block_user():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    user = request.form['username']
    bl = "SELECT user_mail FROM blocked_users;"
    blocked_list = list(c.execute(bl))
    for i in blocked_list:
        if user == i[0]:
            return "Already Blocked"
    block_cmd = f'INSERT INTO blocked_users (user_mail) VALUES ("{user}")'
    c.execute(block_cmd)
    conn.commit()
    conn.close()
    return "Success"

@app.route('/changepvm', methods=['POST'])
def changepvm():
    conn = sqlite3.connect('./webmailserver.db')
    ct = request.form['change_to']
    conn.execute(f'UPDATE global_variables SET variable_value = "{ct}" WHERE vid = 18')
    conn.commit()
    conn.close()
    return "success"

@app.route('/startstopservice', methods=['POST'])
def startstopservice():
    conn = sqlite3.connect('./webmailserver.db')
    new_status = request.form['new_status']
    if new_status == "false":
        conn.execute(f'UPDATE global_variables SET variable_value = "False" WHERE vid = 18')
    else:
        conn.execute(f'UPDATE global_variables SET variable_value = "True" WHERE vid = 18')
    conn.commit()
    conn.close()
    return "success"

@app.route('/verify-user', methods=['POST'])
def verify_user():
    phase = request.form['phase']

    if phase == "phase1":
        conn = sqlite3.connect('./webmailserver.db')
        fullname = request.form['fullname']
        email = request.form['email']
        conn.execute(f"UPDATE localPVMdesc SET variable_value = '{fullname}' WHERE lid = 2")
        OTP_STR = verify_user_email(email)
        conn.execute(f"UPDATE localPVMdesc SET variable_value = '{OTP_STR}' WHERE lid = 12")
        conn.commit()
        conn.close()
        return {
                "status": "success",
                "email": email,
            }
    
    elif phase == "phase2":
        OTP_STR = request.form['otp']
        conn = sqlite3.connect('./webmailserver.db')
        OTP = list(conn.execute("SELECT variable_value FROM localPVMdesc WHERE lid=12"))[0][0]
        if OTP_STR == OTP:
            uemail = request.form['email']
            conn.execute(f"UPDATE localPVMdesc SET variable_value = '{uemail}' WHERE lid = 7")
            conn.commit()
            return "success"
        else:
            return "failed"
    
    elif phase == "phase3":
        accepted = request.form['accepted']
        if accepted:
            conn = sqlite3.connect('./webmailserver.db')
            conn.execute('UPDATE localPVMdesc SET variable_value="True" where lid=1 ')
            conn.commit()
            conn.close()
            return 'success'

    
    return "success"

@app.route('/all-user-data')
def all_u_data():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()

    iss = list(c.execute("SELECT variable_value FROM localPVMdesc WHERE lid=1"))[0][0]
    css = list(c.execute("SELECT variable_value FROM user_generated_frontend_preview WHERE uid=1"))[0][0]

    all_data = c.execute("select * from printer_log;")
    all_data = all_data.fetchall()
    

    return render_template(
        './all-user-data.html',
        page_name="all-user-data",
        iss=iss,
        css=css,
    )

@app.route('/setfullname', methods=['POST'])
def setname():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    c.execute('UPDATE localPVMdesc SET variable_value = ? WHERE lid = 2', (request.form['full_name'],))
    conn.commit()
    conn.close()
    return render_template('./index.html')

@app.route('/update-imap', methods=['POST'])
def update_imap():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    c.execute('UPDATE global_variables SET variable_value = ? WHERE vid = 5', (request.form['imap_server_address'],))
    c.execute('UPDATE global_variables SET variable_value = ? WHERE vid = 1', (request.form['imap_server_email'],))
    user_password = encrypt(request.form['imap_server_password'])
    c.execute('UPDATE global_variables SET variable_value = ? WHERE vid = 2', (user_password,))
    conn.commit()
    conn.close()
    return render_template('./index.html')

@app.route('/update-smtp', methods=['POST'])
def update_smtp():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    c.execute(f'UPDATE global_variables SET variable_value = "{request.form["smtp_server_address"]}" WHERE vid = 6')
    c.execute(f'UPDATE global_variables SET variable_value = "{request.form["smtp_server_email"]}" WHERE vid = 3')
    c.execute(f'UPDATE global_variables SET variable_value = "{request.form["smtp_server_port"]}" WHERE vid = 7')
    user_password = encrypt(request.form['smtp_server_password'])
    c.execute(f'UPDATE global_variables SET variable_value = "{user_password}" WHERE vid = 4')
    conn.commit()
    conn.close()
    return render_template('./index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name'] 
    email = request.form['email']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    conn.close()
    return render_template('success.html', name=name, email=email)

@app.route('/reset-log')
def reset_log():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    c.execute("delete from printer_log;")
    c.execute('INSERT INTO printer_log (file_sender, file_subject, file_request_time, total_attachments, end_queue, duration) VALUES ("kushagra.rigel@gmail.com", "Default LOG", "2004-10-05 16:04:00:000000", 0, "2004-10-05 16:04:00:000000", 0)')
    conn.commit()
    conn.close()
    return redirect('/log')

@app.route('/download-log')
def download_log():
    conn = sqlite3.connect('./webmailserver.db')
    c = conn.cursor()
    c.execute("SELECT * FROM printer_log")
    data = c.fetchall()
    file_path = list(conn.execute("SELECT variable_value FROM global_variables WHERE vid=11"))[0][0] + "printer_log.csv"
    with open(file_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        conn.close()
    return send_file(file_path, as_attachment=True)

@app.route('/report-issue-log')
def report_issue_log():
    return send_file('./record.log', as_attachment=True)


if __name__ == '__main__':
    # webview.create_window("Webmail Server", app, width=800, height=600, resizable=True)
    # webview.start()
    app.run(debug=True)
