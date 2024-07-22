import network
import time
from umqtt.simple import MQTTClient

class WiFiConnector:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self):
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        max_wait = 10
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            print('Подключение...к сети Wi-Fi')
            time.sleep(3)

        if self.wlan.status() != 3:
            print('Не удалось подключиться к сети Wi-Fi')
        else:
            print('Подключено')
            status = self.wlan.ifconfig()
            print('ip = ' + status[0])

    def disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)
        print('Отключено от Wi-Fi')

    def is_connected(self):
        return self.wlan.isconnected()

class MQTTConnector:
    def __init__(self, broker, port, username, password, client_id):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client = MQTTClient(client_id, broker, port, username, password)

    def connect(self):
        self.client.connect()
        print('Подключено к MQTT брокеру')

    def disconnect(self):
        self.client.disconnect()
        print('Отключено от MQTT брокера')

    def subscribe(self, topics, callback):
        self.client.set_callback(callback)
        for topic in topics:
            self.client.subscribe(topic)
            print(f'Подписано на тему {topic}')

    def wait_for_message(self, wifi_connector):
        print('Ожидание сообщений...')
        while True:
            if not wifi_connector.is_connected():
                print('WiFi соединение потеряно')
                raise OSError('WiFi соединение потеряно')
            try:
                self.client.check_msg()
            except OSError as e:
                print(f'Ошибка MQTT: {e}')
                raise OSError('MQTT соединение потеряно')

# Словарь для хранения топиков и их соответствующих переменных
topics = {
    'home/heat_on/current-temperature/get': 'cur_temp',
    'home/heat_on/current-temperature_koll': 'cur_temp_koll',
    'home/esp-12f/current-temperature': 'temp_in',
    'home/pico/current_temperature': 'out_temp'
}

# Инициализация переменных для хранения значений топиков
variables = {v: None for v in topics.values()}

# Функция обратного вызова для обработки сообщений
def message_callback(topic, msg):
    global variables
    topic_str = topic.decode('utf-8')
    msg_str = msg.decode('utf-8')
    print(f'recive data in topic {topic_str}: {msg_str}')
    
    if topic_str in topics:
        variable_name = topics[topic_str]
        variables[variable_name] = float(msg_str)
        print(f'update data {variable_name}: {variables[variable_name]}')
    else:
        print(f'unknow topic: {topic_str}')

# Пример использования
wifi_ssid = 'aonline'
wifi_password = '1qaz2wsx3edc'
mqtt_broker = 'greenhouse.net.ua'
mqtt_port = 1883
mqtt_username = 'mqtt'
mqtt_password = 'qwerty'
mqtt_client_id = 'pico_client'

while True:
    wifi_connector = WiFiConnector(wifi_ssid, wifi_password)
    mqtt_connector = MQTTConnector(mqtt_broker, mqtt_port, mqtt_username, mqtt_password, mqtt_client_id)

    try:
        wifi_connector.connect()
        if wifi_connector.is_connected():
            mqtt_connector.connect()
            mqtt_connector.subscribe(list(topics.keys()), message_callback)
            mqtt_connector.wait_for_message(wifi_connector)
        else:
            print('WiFi не подключено. Повторная попытка через 5 секунд...')
            time.sleep(5)
    except Exception as e:
        print(f'Ошибка: {e}')
        time.sleep(5)
    finally:
        try:
            mqtt_connector.disconnect()
        except:
            pass
        wifi_connector.disconnect()

    # В цьому місці можна використовувати збережені значення з variables
    print(f'Используем сохраненные данные: {variables}')
    time.sleep(5)
