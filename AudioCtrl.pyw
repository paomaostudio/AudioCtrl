import os
import sys
import time
import paho.mqtt.client as mqtt
import pystray
from PIL import Image
import logging
import configparser
import webbrowser
import psutil
import win32com.client

# 初始化各种文件路径
help_url = "https://gitee.com/z779750025/AudioCtrl/blob/main/README.md"
script_dir = (os.path.dirname(os.path.realpath(sys.argv[0])))  # 当前脚本工作路径
os.chdir(script_dir)
exe_path = os.path.join(script_dir, "AudioCtrl.exe")
icon_path = os.path.join(script_dir, "icon.png")
config = configparser.RawConfigParser()
config_file = os.path.join(script_dir, 'config.ini')
# 初始化快捷方式路径
shell = win32com.client.Dispatch("WScript.Shell")
startup_folder = shell.SpecialFolders("Startup")
shortcut_path = os.path.join(startup_folder, "AudioCtrl" + ".lnk")
shortcut = shell.CreateShortcut(shortcut_path)
shortcut.TargetPath = exe_path
# 读取配置文件
with open(config_file, 'r', encoding='utf-8-sig') as file:
    config.read_string(file.read())
mqtt_client_id = config.get('MQTT', 'client_id')
mqtt_topic = config.get('MQTT', 'topic')
# 配置日志记录
logging.basicConfig(filename='ac.log', level=logging.INFO, encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s')


def info(info):
    print(info)
    logging.info(info)


def create_startup_entry():
    info("添加开机启动项")
    shortcut.Save()


def toggle_startup_entry():
    # 切换安装和删除开机启动项
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        notify_startup(False)
        info("删除开机启动项")
    else:
        notify_startup(True)
        create_startup_entry()


def check_initialization():
    flag_file = "initialized.flag"
    if os.path.exists(flag_file):
        info("已经执行过初始化操作了")
        # 已经初始化过了，不需要再执行
        return True
    else:
        create_startup_entry()
        info("创建Flag文件，初始化")
        # 创建标志文件
        with open(flag_file, 'w') as f:
            f.write("Initialized")
        return False


def check_config_file():
    if mqtt_client_id == "" or mqtt_topic == "":
        info("脚本本地配置文件不存在")
        os.startfile("config.ini")
        tray_app.notify("初次设置", "请填写修改配置文件，并重新打开软件")
        time.sleep(3)
        tray_app.stop()


def setting():
    os.startfile("config.ini")
    tray_app.stop()


def show_log(icon, item):
    os.startfile("ac.log")
    info("打开日志文件")


def notify_startup(key):
    if key:
        tray_app.notify("提醒", "设置开机启动")
    else:
        tray_app.notify("提醒", "取消开机启动")


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
    webbrowser.open(help_url)


def create_tray_app():
    image = Image.open(icon_path)
    menu = (
        pystray.MenuItem("切换开机启动", toggle_startup_entry),
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
        # 初始化，初次链接成功创建开机启动
        check_initialization()
        client.subscribe(mqtt_topic)
    else:
        info("连接失败 %s" % (rc))
        os.startfile("config.ini")
        tray_app.notify("连接失败", "请手动修改配置文件，并重新打开软件")
        time.sleep(5)
        tray_app.stop()


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
    icon.visible = True
    check_config_file()
    connect_mqtt()


if __name__ == "__main__":
    # 创建托盘应用程序
    tray_app = create_tray_app()
    # 启动托盘应用程序
    info("开始运行")
    tray_app.run(run_script)
