import sys
import requests

class Signal:
    def __init__(self, Messenger):
        try:
            self.parent = Messenger

            self.url    = f"http://homeassistant.local:{self.parent.signal_port}"
            
            self.number = self.parent.signal_numbers[0]

            self.headers = {
                'Content-Type': 'application/json',
            }
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
            self.up     = False

    def available(self):
        try:
            response = requests.get(f'{self.url}/v1/about', headers=self.headers)

            if response.ok:
                self.up     = True
                self.parent.logger.info("Signal Api is Up and Running")
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
            self.parent.logger.warning(f"Signal is not available") 
            self.up     = False

    def is_registered(self, number):
        try:
            response = requests.get(f'{self.url}/v1/search/{self.number}?numbers={number}', headers=self.headers)

            if response.ok:
                return response.json()[0]['registered']

            return False
        except KeyError:
            #Phonenumber is not valid
            return False
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
            return False

    def send_message(self, number, msg):
        if self.parent.debug:
            self.parent.logger.debug(f"I would have sent '{msg}' via signal to {number} if debug was disabled")
            return True
        
        try:
            data    = {
                "number": self.number,
                'message': f"{msg}",
                'recipients': [number],
            }
            response    = requests.post(f'{self.url}/v2/send', json=data, headers=self.headers)

            if response.ok:
                self.parent.logger.info(f'Send Signal Message Succesfully. Timestamp { response.json()["timestamp"] }') 
                return response.json()['timestamp']

            # Something went wrong and was ment for a group
            if number[0][0] != '+':
                error       = response.json()["error"]

                response    = requests.get(f'{self.url}/v1/groups/{self.number}', headers=self.headers)

                groups  = ''
                if response.ok:
                    for group in response.json():
                        groups +=   f"Name: {group['name']} Id: {group['id']}\n"
                self.parent.logger.error(f'Send Signal message failed. Error is {error} Do you have the right group id?\nGroup ids:{groups}')
            else:
                self.parent.logger.error(f'Send Signal message failed. Error is {response.json()["error"]} ')

            return False
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
            