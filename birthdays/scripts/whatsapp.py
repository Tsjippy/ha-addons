import requests
import sys
from time import sleep

class Whatsapp:
    def __init__(self, Messenger):
        try:
            self.parent         = Messenger
            self.chats          = {}
            
            for group in self.parent.whatsapp_groups:
                self.chats[group['group_name']]    = group['group_id']

            self.connected      = False
            self.api_running    = True

            self.whatsapp_server_url = f"http://homeassistant.local:{self.parent.whatsapp_port}/api/"
                
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def check_connected(self):
        try:
            status              = requests.get(f'{self.whatsapp_server_url}status').json()['status']
            self.api_running    = True
            self.parent.logger.info("Whatsapp Api is Up and Running")

            if status == 'CONNECTED':
                self.parent.logger.info(f"Connected to a Whatsapp Session!")

                self.connected  = True
            else:
                self.parent.logger.warning("Not connected to a Whatsapp Session!")
        except requests.exceptions.RequestException as e:
            self.api_running  = False

            self.parent.logger.error(f"The Whatsapp api is not running on {self.whatsapp_server_url}") 
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def make_request(self, url, post='', return_json=False):
        try:
            self.api_running  = True
            url     = f"{self.whatsapp_server_url}{url}"

            if post == '':
                result = requests.get(url)
            else:
                result = requests.post(url, json = post)

            if(result.status_code != 200):
                self.connected      = False
                self.check_connected()

                self.parent.logger.error(f"Command with url {url} and post {post} failed with status code {result.status_code} {result.text}")
                
                return False

            json    = result.json()

            if return_json:
                return json
            elif 'result' in json:
                return json['result']
            elif 'success' in json and json['success']:
                return json['success']
            elif 'isUser' in json:
                return json['isUser']
            else:
                self.parent.logger.debug(f"Json result is: {json} for request {url} {post}")
                return json
        except requests.exceptions.RequestException as e:
            self.api_running  = False

            self.parent.logger.error(f"The Whatsapp api is not running on {self.whatsapp_server_url}") 
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
    
    def get_chat_id(self, name):
        try:
            # Remove the plus sign if it exists
            chat_id  = name.replace('+', '')

            # Check if the chat_id is already a real chat id
            if not '@c.us' in chat_id and not '@g.us' in chat_id:
                # If chat_id is a phone number
                if chat_id.isnumeric():
                    chat_id += '@c.us'
                else:
                    # chat_id is most likely a name
                    if not chat_id in self.chats:
                        self.parent.logger.error(f"No chat id found for {chat_id}")
                        return False
                    
                    chat_id  = self.chats[chat_id]
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}") 

        return chat_id
    
    def is_registered(self, number):
        try:
            if number.startswith("+3115"):
                return False
        
            chat_id = self.get_chat_id(number)  

            if not chat_id:
                return False
        
            result  = self.make_request(f"contacts/{chat_id}")

            if type(result) is dict and 'error' in result:
                return False
        
            return result
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}") 
    
    def send_message(self, name, msg, contentType='string'):       
        try:
            chat_id     = self.get_chat_id(name)            
            
            url         = f'chats/{chat_id}/messages'

            if self.parent.debug:
                self.parent.logger.debug(f"I would have sent '{msg}' via whatsapp message to {name} ({chat_id}) if debug was disabled")
                return True
        
            post    = {
                'msg': f"{msg}"
            }

            return self.make_request(url, post)
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}") 
    
    def get_all_chats(self):
        try:
            result   = self.make_request('client/getChats', '', True)
            if(result and 'success' in result):
                for chat in result['chats']:
                    self.chats[chat['name']] = chat['id']['_serialized']
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
