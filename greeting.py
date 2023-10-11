import openai
import paramiko
import requests
import json
import os
import logging
import sys
import subprocess
import re
from webex_bot.models.command import CALLBACK_KEYWORD_KEY, Command, COMMAND_KEYWORD_KEY
from adaptivecards.adaptivecard import AdaptiveCard
from webex_bot.models.response import Response
from webex_bot.models.command import Command
from webex_bot.websockets.webex_websocket_client import WebexWebsocketClient
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup



logging.basicConfig(filename='log.txt', level=logging.INFO, force=True, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.info("Logging file is created")

username1 = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
hostname1 = os.environ.get("HOSTNAME")
cisco_username = os.environ.get("USER")
cisco_pw = os.environ.get("PASS")
file1_path ="./inp-card.json"
file2_path ="./inp2-card.json"

with open(file1_path,"r") as card1:
    INPUT_CARD1 = json.load(card1)
with open(file2_path,"r") as card2:
    INPUT_CARD2 = json.load(card2)

    
# Creating folder in remote server using the folder name as input from user 
class CreatefolderBYNAME(Command):
    def __init__(self):
        super().__init__(command_keyword = "release_folders",
                        card = INPUT_CARD1,
                        help_message = "Phase - 1 Release"
                        )
    def execute(self, message, attachment_actions, activity):
        global Folder_NAME
        try: 
            Folder_NAME = attachment_actions.inputs['name']
            ssh=paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname1,username=username1,password=password)
            command_creating_folder = f'mkdir {Folder_NAME}'
            stdin, stdout, stderr = ssh.exec_command(command_creating_folder)
            if_folder_already_there = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                logging.error(f"Error: {error.strip()}")
            else:
                logging.info(f"Command executed successfully: {command_creating_folder}")
            command_listing_files = 'ls -m'
            stdin, stdout,stderr = ssh.exec_command(command_listing_files)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode()
            if error:
                raise Exception(f"Error: {error.strip()}")
            else:
                logging.info(f"Command executed successfully: {command_listing_files}")
            folder_list = [l.strip().replace("'", "") for l in output.split(",")]
            if Folder_NAME in folder_list:
                logging.info("{} file got created".format(Folder_NAME))
            else:
                logging.info("The file {} couldn't be created".format(Folder_NAME))
                logging.info(if_folder_already_there)
        except ValueError as ve:
            logging.error("Folder name is invalid {} ".format(ve))
            return "Please provide a valid file name."
        except paramiko.AuthenticationException as PAE:
            logging.error("Authentication failed {}.".format(PAE))
        except paramiko.SSHException as ssh_ex:
            logging.error("SSH connection failed:{}".format(ssh_ex))
        except paramiko.socket.error as sock_ex:
            logging.error("Socket error:{}".format(sock_ex))
        except paramiko.ChannelException as channel_exception:
            logging.error(f"Error executing command on SSH channel: {str(channel_exception)}")
        except Exception as e:
            logging.error("An error occurred:{}".format(e))
        finally:
            ssh.close
    
#Download files to the remote server in the folder created before 
class DownloadFilesfromURL(Command):
    def __init__(self):
        super().__init__(command_keyword= "download_files",
                        card = INPUT_CARD1,
                        delete_previous_message = False
                        )
    def execute(self, message, attachment_actions, activity):
        un_cisco = cisco_username
        pw_cisco = cisco_pw
        URL_name = attachment_actions.inputs['url_R']
        try:
            pattern = r"RC\d+"
            match = re.search(pattern, URL_name)
            if match:
                global rc_number
                rc_number = match.group()
                rc_number = rc_number.lower()
            stripped_url = URL_name.split(".com")[0] + ".com"
            session = requests.Session()
            session.auth = (un_cisco, pw_cisco)
            response = session.get(URL_name, stream=True)
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                links = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    href = stripped_url + href
                    if href and not href.endswith('/'):  # Exclude directories
                        links.append(href)
                c = len(links)
                logging.info("Total links to download are {}".format(c))
                for link in links :
                    response = requests.head(link, auth=(un_cisco, pw_cisco))
                    file_name = link.split("RC1")[1][1:]
                    if response.status_code == requests.codes.ok:
                        content_length = response.headers.get('Content-Length')
                        actual_length = int(content_length)
                        logging.info("The actual length of the file {} is {}".format(file_name,actual_length))
                            
                    try:
                        ssh=paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(hostname=hostname1,username=username1,password=password)
                        command_open_directory = 'cd {} && nohup curl  -u Build:h323sipt120 -O {}'.format(Folder_NAME,link)
                        stdin,stdout,stderr = ssh.exec_command(command_open_directory)
                        output = stdout.read().decode('utf-8')
                        logging.info(output)
                        error = stderr.read().decode()
                        if error:
                            logging.error(f"Error: {error.strip()}")
                        else:
                            logging.info(f"Command executed successfully: {command_open_directory}")
                        command_to_check_size_after_download =  "cd {} && stat -c%s {}".format(Folder_NAME,file_name)
                        stdin,stdout,stderr = ssh.exec_command(command_to_check_size_after_download)
                        downloaded_size = stdout.read().decode('utf-8')
                        error = stderr.read().decode()
                        if error:
                            logging.error(f"Error: {error.strip()}")
                        else:
                            logging.info(f"Command executed successfully: {command_to_check_size_after_download}")
                        logging.info("The downloaded size is {}".format(downloaded_size))
                        downloaded_size = int(downloaded_size)
                        if actual_length == downloaded_size :
                            logging.info("{} file  downloaded completely".format(file_name))
                        else: 
                            logging.info("{} file couldn't download completely".format(file_name))
                        ssh.close()
                    except paramiko.AuthenticationException:
                        logging.error("Authentication failed.")
                    except paramiko.SSHException as ssh_ex:
                        logging.error("SSH connection failed:", ssh_ex)
                    except paramiko.socket.error as sock_ex:
                        logging.error("Socket error:", sock_ex)
                    except Exception as e:
                        logging.error("An error occurred:", e)
                    finally:
                        ssh.close()
                try:
                    ssh=paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=hostname1,username=username1,password=password)
                    comm_to_count_downloaded_files = "cd {} && ls | wc -l".format(Folder_NAME)
                    stdin,stdout,stderr = ssh.exec_command(comm_to_count_downloaded_files)
                    total= stdout.read().decode('utf-8') 
                    logging.info("Total {} files downloaded from the links".format(total))
                    error = stderr.read().decode()
                    if error:
                        logging.error(f"Error: {error.strip()}")
                    else:
                        logging.info(f"Command executed successfully: {comm_to_count_downloaded_files}")
                except paramiko.AuthenticationException:
                        logging.error("Authentication failed.")
                except paramiko.SSHException as ssh_ex:
                    logging.error("SSH connection failed:", ssh_ex)
                except paramiko.socket.error as sock_ex:
                    logging.error("Socket error:", sock_ex)
                except Exception as e:
                    logging.error("An error occurred:", e)
                finally:
                    ssh.close()
            elif response.status_code == 404:
                logging.error("Couldn't load the url")
        except URLError as url_error:
            logging.exception(f"URL Error: {url_error.reason}")
        except ValueError:
            logging.exception("Invalid URL format. Please provide a valid URL.")
        except re.error as re_ex:
            logging.exception("Regular expression error:{}".format(re_ex))
        except requests.exceptions.HTTPError as http_ex:
            logging.exception("HTTP error occurred:{}" .format(http_ex))
        except requests.exceptions.RequestException as req_ex:
            logging.exception("Request exception occurred:{}".format (req_ex))
        except Exception as e:
            logging.exception("An error occurred:{}".format (e))
                    

        
#Executing the release command -->> script run
class exec_comman_release(Command):
    def __init__(self):
        super().__init__(command_keyword = "exec",
                        card = INPUT_CARD1,
                        delete_previous_message = False)
    def execute(self, message, attachment_actions, activity):
        try:
            ssh=paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname1,username=username1,password=password)
            command_to_exec = "python release-engineering/finalreleaseprep.py -s . -p _{} -l 5".format(rc_number)
            command_open_directory_exec_comm = "cd {} && {}".format(Folder_NAME,command_to_exec)
            stdin, stdout,stderr = ssh.exec_command(command_open_directory_exec_comm)
            output = stdout.read().decode('utf-8')
            logging.info(output)
            error = stderr.read().decode()
            if error:
                raise Exception(f"Error: {error.strip()}")
            else:
                logging.info(f"Command executed successfully: {command_open_directory_exec_comm}")
        except paramiko.AuthenticationException as PAE:
            logging.error("Authentication failed {}.".format(PAE))
        except paramiko.SSHException as ssh_ex:
            logging.error("SSH connection failed:{}".format(ssh_ex))
        except paramiko.socket.error as sock_ex:
            logging.error("Socket error:{}".format(sock_ex))
        except paramiko.ChannelException as channel_exception:
            logging.error(f"Error executing command on SSH channel: {str(channel_exception)}")
        except Exception as e:
            logging.error("An error occurred:{}".format(e))
        finally :
            ssh.close()

# Pushing all the files to final and listing them
class Push_to_final_and_list(Command):
    def __init__(self):
        super().__init__(command_keyword = "pushfilestofinal&list",
                        card = INPUT_CARD1,
                        delete_previous_message = False
                        )
    def execute(self, message, attachment_actions, activity):
        try:
            ssh=paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname1,username=username1,password=password)
            command_open_list = "cd {} && cd Final && ls".format(Folder_NAME)
            stdin,stdout,stderr = ssh.exec_command (command_open_list)
            output = stdout.read().decode('utf-8')
            logging.info("The following are the files preset in Final folder {}".format(output))
            error = stderr.read().decode()
            if error:
                raise Exception(f"Error: {error.strip()}")
            else:
                logging.info(f"Command executed successfully: {command_open_list}")
        except paramiko.AuthenticationException as PAE:
            logging.error("Authentication failed {}.".format(PAE))
        except paramiko.SSHException as ssh_ex:
            logging.error("SSH connection failed:{}".format(ssh_ex))
        except paramiko.socket.error as sock_ex:
            logging.error("Socket error:{}".format(sock_ex))
        except paramiko.ChannelException as channel_exception:
            logging.error(f"Error executing command on SSH channel: {str(channel_exception)}")
        except Exception as e:
            logging.error("An error occurred:{}".format(e))
        finally:
            ssh.close()

        

class changesigntounsign(Command):
    def __init__(self, ):
        super().__init__(command_keyword= "unsign2sign",
                        card = INPUT_CARD2, 
                        delete_previous_message = False,
                        help_message = "Phase - 2 Release")
    def execute(self, message, attachment_actions, activity):
        return "Hi"
    

class totalfilestofinal(Command):
    def __init__(self, ):
        super().__init__(command_keyword= "pushtotaltofinal",
                        card = INPUT_CARD2, 
                        delete_previous_message = False)
    def execute(self, message, attachment_actions, activity):
        return "Hi"
    

class Finaltocorona(Command):
    def __init__(self, ):
        super().__init__(command_keyword= "pushtocorona",
                        card = INPUT_CARD2,
                        delete_previous_message = False)
    def execute(self, message, attachment_actions, activity):
        return "Hi"

        


        











