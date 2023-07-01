import os
import time
import paho.mqtt.client as mqtt
import pystray
from PIL import Image
import logging
import configparser
import webbrowser
import PySimpleGUI as sg
import psutil

# 指定要检查的进程名字或关键词
process_name = "AudioCtrl.exe"

# 获取当前运行的进程列表
processes = psutil.process_iter()

# 检查指定的进程是否已经在运行
for process in processes:
    if process.name() == process_name:
        print("程序已经在运行中")
        exit(0)

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


def show_gui():
    global mqtt_client_id
    global mqtt_topic
    sg.theme('DarkAmber')   # 设置当前主题
    # 界面布局，将会按照列表顺序从上往下依次排列，二级列表中，从左往右依此排列
    layout = [  [sg.Text('请填写配置信息，如果您不明白，请点击下方的帮助')],
                [sg.Text('私钥'), sg.InputText(mqtt_client_id)],
                [sg.Text('主题'), sg.InputText(mqtt_topic)],
                [sg.Button('确定'), sg.Button('帮助')]]
    
    # 创造窗口
    window = sg.Window('配置', layout, icon=icon_path)
    # 事件循环并获取输入值
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):   # 如果用户关闭窗口或点击`Cancel`
            break
        if event == "帮助":
            webbrowser.open("https://github.com/paomaostudio/AudioCtrl")
        if any(value == '' for value in values.values()):
            sg.popup_error("Error:请填写有效信息")
        elif event == "确定":
            config.set('MQTT', 'client_id', values[0])
            config.set('MQTT', 'topic', values[1])
            with open(config_file, 'w', encoding='utf-8') as file:
                config.write(file)
            mqtt_client_id, mqtt_topic = values[0], values[1]
            connect_mqtt()
            break
        print(values)
        info("用户输入"+str(values))
    window.close()


def info(info):
    logging.info(info)


if mqtt_client_id == "" or mqtt_topic == "":
    info("脚本本地配置文件不存在")
    show_gui()


def show_log(icon, item):
    os.startfile("ac.log")
    info("打开日志文件")


def cancel_poweroff(icon, item):
    os.system("shutdown /a")  # 取消关机
    info("取消关机命令")


def exit(icon, item):
    icon.stop()


def create_tray_app():
    image = Image.open(icon_path)
    menu = (
        pystray.MenuItem("设置", show_gui),
        pystray.MenuItem("取消关机", cancel_poweroff),
        pystray.MenuItem("日志", show_log),
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
        time.sleep(1)
        tray_app.notify("连接失败", "请手动修改配置文件，并重新打开软件")
        os._exit(0)


# 收到消息回调函数
def on_message(client, userdata, msg):
    info(msg.topic+" "+str(msg.payload.decode('utf-8')))
    if msg.payload.decode('utf-8') == "off":
        tray_app.notify("关机提醒", "您的计算机将在1分钟后关机,右键托盘图标可以取消关机")
        info("准备关机...")
        os.system("shutdown /s /t 60")  # 关机命令
    elif msg.payload.decode('utf-8') == "on":
        tray_app.notify("自定义脚本", "您已执行自定义脚本")
        info("执行自定义脚本")
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


def run_script():
    connect_mqtt()

if __name__ == "__main__":
    # 创建托盘应用程序
    tray_app = create_tray_app()
    # 启动托盘应用程序
    info("开始运行")
    tray_app.run(run_script())
