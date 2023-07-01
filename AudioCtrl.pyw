import os
import time
import paho.mqtt.client as mqtt
import pystray
from PIL import Image
import logging
import configparser
import webbrowser
import psutil

# 指定要检查的进程名字或关键词
process_name = "AudioCtrl.exe"

# 获取当前运行的进程列表
processes = psutil.process_iter()

# 初始化各种文件路径
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "icon.png")
config = configparser.RawConfigParser()
config_file = os.path.join(script_dir, 'config.ini')
# 配置日志记录
logging.basicConfig(filename='ac.log', level=logging.INFO, encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s')

with open(config_file, 'r', encoding='utf-8') as file:
    config.read_string(file.read())
mqtt_client_id = config.get('MQTT', 'client_id')
mqtt_topic = config.get('MQTT', 'topic')


def info(info):
    logging.info(info)


# 检查指定的进程是否已经在运行
for process in processes:
    if process.name() == process_name:
        info("程序已经在运行中")
        os._exit(0)


def check_config_file():
    
    if mqtt_client_id == "" or mqtt_topic == "":
        info("脚本本地配置文件不存在")
        os.startfile("config.ini")
        tray_app.notify("初次设置", "请填写修改配置文件，并重新打开软件")
        time.sleep(3)
        tray_app.stop()
        #os._exit(0)


def setting():
    os.startfile("config.ini")
    tray_app.stop()
    #os._exit(0)


def show_log(icon, item):
    os.startfile("ac.log")
    info("打开日志文件")


def notify_shutdown():
    tray_app.notify("关机提醒", "您的计算机将在1分钟后关机,右键托盘图标可以取消关机")
    info("准备关机...")


def notify_custom_script():
    tray_app.notify("自定义脚本", "您已执行自定义脚本")
    info("执行自定义脚本")


def cancel_poweroff(icon, item):
    os.system("shutdown /a")  # 取消关机
    info("取消关机命令")


def exit(icon, item):
    icon.stop()


def help():
    webbrowser("https://github.com/paomaostudio/AudioCtrl")


def create_tray_app():
    image = Image.open(icon_path)
    menu = (
        pystray.MenuItem("配置", setting),
        pystray.MenuItem("取消关机", cancel_poweroff),
        pystray.MenuItem("日志", show_log),
        pystray.MenuItem("帮助", help),
        pystray.MenuItem("退出", exit),
    )
    return pystray.Icon("AudioCtrl", image, "AudioCtrl", menu)


# 连接成功回调函数
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        info("连接成功")
        client.subscribe(mqtt_topic)
    else:
        info("连接失败 %s" % (rc))
        os.startfile("config.ini")
        tray_app.notify("连接失败", "请手动修改配置文件，并重新打开软件")
        time.sleep(3)
        tray_app.stop()
        os._exit(0)


# 收到消息回调函数
def on_message(client, userdata, msg):
    info(msg.topic+" "+str(msg.payload.decode('utf-8')))
    if msg.payload.decode('utf-8') == "off":
        notify_shutdown()
        os.system("shutdown /s /t 60")  # 关机命令
    elif msg.payload.decode('utf-8') == "on":
        notify_custom_script()
        some_function()


def some_function():
    # 您可以在这里定义一个自己的功能，当mqtt话题收到on指令的时候会执行
    os.system("start cmd /c run.bat")  # 默认会执行脚本同目录的run.bat文件


def connect_mqtt():
    client = mqtt.Client(client_id=mqtt_client_id, protocol=mqtt.MQTTv31)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("bemfa.com", 9501, 60)
    client.loop_start()


def run_script(icon):
    print(icon)
    icon.visible = True
    check_config_file()
    connect_mqtt()


if __name__ == "__main__":
    # 创建托盘应用程序
    tray_app = create_tray_app()
    # 启动托盘应用程序
    info("开始运行")
    tray_app.run(run_script)
