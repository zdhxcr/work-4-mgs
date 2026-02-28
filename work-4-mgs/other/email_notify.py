#! /DATA/pchen/miniconda3/bin/python
import subprocess
import os
import argparse
import smtplib
import time

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr


def parse_arguments() -> argparse.Namespace:
    """This function parses the arguments
    
    Returns:
        argparse.Namespace: The command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-jn','--job_name', required=False, type=str, help='set the name of your job to send',default=None)
#   parser.add_argument('-nn','--node_name', required=False, type=str, help='the node name, which machine finnished your job, e.g. gm41',default=None)
#   parser.add_argument('-wp','--work_path', required=False, type=str, help='the work directory',default=None)
    parser.add_argument('-to','--email_to', required=False, type=str, help='set the email site to recive the output',default='zhangyuxi2023@126.com')
    parser.add_argument('-fr','--email_from', required=False, type=str, help='set the email site to send the output',default='1015623540@qq.com')
    parser.add_argument('-pw','--password', required=False, type=str, help='the password of which account to send the output',default='lazqkifwkdnabfed')
#   parser.add_argument('-u','--user', required=False, type=str, help='user who started this job',default='user')
    parser.add_argument('-s','--smtp_server', required=False, type=str, help='get the Mail User Agent(MUA) in the website of the emailbox you use',default='smtp.qq.com')
    parser.add_argument('-p','--port', required=False, type=int, help='check the SMTP port on the email website', default=465)
    args = parser.parse_args()

    return args

def _format_addr(s) -> str:
    '''to format the str into name and address
    
    Returns:
        encoded Name and address
    '''
    name, addr = parseaddr(s)
    return formataddr((Header(name,'utf-8').encode(), addr))

def _get_current_time() -> list:
    t = time.localtime()
    return [t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec]

def sendemail(job_name: str, node_name: str, work_path:str, to_address: str, from_address: str, passwd: str, user: str, smtp_server, smtp_port) -> None:
    '''core code of this scripts, msg is used to determine what content to send, server is to send the email
    
    Returns:
        it returns nothing
    '''
    current_time = _get_current_time()
    
    msg = MIMEText(f'   Hello {user}! Your job on {node_name} has done now. Details are displayed below.\
                    \n  Node_name: {node_name}\
                    \n  Work_path: {work_path}\
                    \n  User_name: {user}\
                    \n  Current_time: {":".join(str(i) for i in current_time)}',\
                        'plain','utf-8')
    msg['From'] = _format_addr(f'Manager <{from_address}>')
    msg['To'] = _format_addr(f'User <{user}>')
    msg['Subject'] = Header(f'Your job "{job_name}" on @{node_name} has done.').encode()
    
    try:
        #server = smtplib.SMTP(smtp_server, smtp_port)
        # without input the port, can the email give out
        server = smtplib.SMTP(smtp_server)
        server.starttls()
        server.set_debuglevel(1)
        server.login(from_address, passwd)
        server.sendmail(from_address, [to_address], msg.as_string())
        server.quit()
    except Exception as err:
        print(f'Something wrong when sending the email: {str(err)}')


def main() -> None:
    args = parse_arguments()
    node_name = subprocess.check_output('echo $HOSTNAME', shell=True, text=True).strip()
    work_path = subprocess.check_output('pwd', shell=True, text=True).strip()
    user_name = subprocess.check_output('echo $USER', shell=True, text=True).strip()
    sendemail(args.job_name, node_name, work_path, args.email_to, args.email_from, args.password, user_name, args.smtp_server, args.port)

    
if __name__ == '__main__':
    main()
    
