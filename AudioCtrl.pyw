import os
import time
import paho.mqtt.client as mqtt
import pystray
from PIL import Image
from pystray import MenuItem
import logging
import configparser
import webbrowser
import PySimpleGUI as sg

# 初始化各种文件路径
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "icon.png")
config = configparser.ConfigParser()
config_file = os.path.join(script_dir, 'config.ini')

with open(config_file, 'r', encoding='utf-8') as file:
    config.read_string(file.read())
mqtt_client_id = config.get('MQTT', 'client_id')
mqtt_topic = config.get('MQTT', 'topic')


def show_gui(client_id, topic):
    sg.theme('DarkAmber')   # 设置当前主题
    # 界面布局，将会按照列表顺序从上往下依次排列，二级列表中，从左往右依此排列
    layout = [  [sg.Text('请填写配置信息，如果您不明白，请点击下方的帮助')],
                [sg.Text('私钥'), sg.InputText(client_id)],
                [sg.Text('主题'), sg.InputText(topic)],
                [sg.Button('确定'), sg.Button('帮助')] ]
    
    # 创造窗口
    window = sg.Window('Window Title', layout)
    # 事件循环并获取输入值
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):   # 如果用户关闭窗口或点击`Cancel`
            break
        print('You entered ', values[0])
    
    window.close()

# 配置日志记录
logging.basicConfig(filename='ac.log', level=logging.INFO, encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s')

# 在脚本中记录日志

def info(info):
    logging.info(info)




if mqtt_client_id == "":
    url = "https://cloud.bemfa.com/"
    print(url)
    webbrowser.open(url)
    os._exit(0)



def on_tray_click(icon, item):
    os.startfile("ac.log")
    info("打开日志文件")


def cancel_poweroff(icon, item):
    os.system("shutdown /a")  # 取消关机
    info("取消关机命令")


def notify_shutdown():
    tray_app.notify("关机提醒", "您的计算机将在1分钟后关机,右键托盘图标可以取消关机")
    info("准备关机...")

def notify_custom_script():
    tray_app.notify("自定义脚本", "您已执行自定义脚本")
    info("执行自定义脚本")

def exit(icon, item):
    icon.stop()


def create_tray_app():
    image = Image.open(icon_path)
    menu = (
        pystray.MenuItem("设置", show_gui),
        pystray.MenuItem("取消关机", cancel_poweroff),
        pystray.MenuItem("日志", on_tray_click),
        pystray.MenuItem("退出", exit),
    )
    return pystray.Icon("tray_app", image, "Tray App", menu)


# 连接成功回调函数
def on_connect(client, userdata, flags, rc):
    info("Connected with result code "+str(rc))
    client.subscribe(mqtt_topic)


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

def run_script():
    # mqtt设置
    client = mqtt.Client(client_id=mqtt_client_id, protocol=mqtt.MQTTv31)  # MQTTv31对应mqtt 3.1版本
    client.on_connect = on_connect
    client.on_message = on_message

    # 连接mqtt服务器
    client.connect("bemfa.com", 9501, 60)

    # 循环监听
    client.loop_start()

if __name__ == "__main__":
    # 创建托盘应用程序
    tray_app = create_tray_app()
    # 启动托盘应用程序
    info("开始运行")
    tray_app.run(run_script())
