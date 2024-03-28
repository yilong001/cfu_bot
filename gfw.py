import telebot
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import uuid
import time
import sqlite3
import requests
import qrcode
from telebot import types
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
ip_api = os.getenv('IP_API')
bot_token = os.getenv('BOT_TOKEN')
account_id = os.getenv('ACCOUNT_ID')
api_token = os.getenv('CLOUDFLARE_API_TOKEN')
admin_user_id = os.getenv('ADMIN_USER_ID')
bot = telebot.TeleBot(bot_token)
user_states = {}
users_directory = 'users'
index_js_path = 'index.js'
subs_js_path = 'subworker.js'
db_path = 'gfw.db'
INPUT_NEW_API = 0

@bot.message_handler(commands=['start'])
def authorize(message):

    if str(message.from_user.id) == str(admin_user_id):
        print(f"Admin User ID: {admin_user_id}")
        print(f"User ID: {message.from_user.id}")

        send_welcome(message)
    else:
        unauthorized_message = "❌ 越权存取！ 您没有权限使用此命令."
        bot.send_message(message.chat.id, unauthorized_message)


def send_welcome(message):
    menu_markup = InlineKeyboardMarkup()
    add_user_button = InlineKeyboardButton("➕ 添加用户", callback_data="add_user")
    user_panel_button = InlineKeyboardButton("🔰 用户面板", callback_data="user_panel")
    subscriptions_button = InlineKeyboardButton("📋 优选域名或IP订阅", callback_data="subscriptions") 
    menu_markup.add(add_user_button, user_panel_button)  
    menu_markup.add(subscriptions_button)  
    welcome_message = "欢迎来到 G-F-W 机器人！\n ✌️ 挺身而出，为自由而战 ✌️ !\n "
    
    bot.send_message(message.chat.id, welcome_message, reply_markup=menu_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'subscriptions')
def subscriptions(call):
    load_dotenv()
    ip_api = os.getenv('IP_API')
    bot.delete_message(call.message.chat.id, call.message.message_id)
    message_text = f"优选域名: {ip_api}"

    keyboard = [
        [InlineKeyboardButton("更改优选域名IP或者优选域名", callback_data="change_ip_api"),
         InlineKeyboardButton("不改变", callback_data="keep_ip_api")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(call.message.chat.id, message_text, reply_markup=reply_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'change_ip_api')
def subscriptions(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_states[call.from_user.id] = 'waiting_for_api'
    message_text = "Please provide the new value for IP_API."

    bot.send_message(call.message.chat.id, message_text)

@bot.callback_query_handler(func=lambda call: call.data == 'keep_ip_api')
def keep_ip_api(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)
    
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_api')
def handle_new_api_value(message):
    new_api_value = message.text.strip()
    os.environ['IP_API'] = new_api_value
    user_states[message.from_user.id] = None
    bot.send_message(message.chat.id, f"IP_API has been updated to: {new_api_value}")
    send_welcome(message)
    

@bot.callback_query_handler(func=lambda call: call.data == 'return')
def return_to_start(call):
    send_welcome(call.message)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_panel'))
def user_panel_cfw(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT name FROM user')
    rows = cursor.fetchall()

    keyboard = InlineKeyboardMarkup()
    
    for row in rows:
        name = row[0]
        callback_data = f"user:{name}"  
        button = InlineKeyboardButton("👤|" + name, callback_data=callback_data)
        keyboard.add(button)

    return_button = InlineKeyboardButton("🔙 返回", callback_data="return")
    keyboard.add( return_button)
    connection.close()

    bot.send_message(call.message.chat.id, "选择一个用户:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('user:'))
def user_info_callback(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_name = call.data.split(':')[1]

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM user WHERE name = ?', (user_name,))
    row = cursor.fetchone()

    if row and None in row:
        cursor.execute('DELETE FROM user WHERE name = ?', (user_name,))
        connection.commit()
        keyboard = InlineKeyboardMarkup()
        return_button = InlineKeyboardButton("🔙 返回", callback_data="user_panel")
        keyboard.add(return_button)
        bot.send_message(call.message.chat.id, f"❌ ℹ️ 已删除 '{user_name}', 它无效❌", reply_markup=keyboard)
        connection.close()
        return

    connection.close()

    if row:
        uuid, subdomain, ip = row[1], row[2], row[3]

        vless_link = create_vless_config(subdomain, uuid, user_name)
        nontls_config = create_nontls_config(subdomain, uuid, user_name)
        sub_link = f"https://sub{subdomain}/{user_name}"
        message_text = f"<b>🔰用户信息🔰</b>\n\n"
        message_text += f"👤 <b>名称:</b> {user_name}\n"
        message_text += f"🔑 <b>UUID:</b> {uuid}\n"
        message_text += f"🌐 <b>IP或域名:</b> {ip}\n"
        message_text += f"📡 <b>子域名:</b> {subdomain}\n\n"
        message_text += f"🔗开tls: <code>{vless_link}</code>\n\n"
        message_text += f"🔗未开tls: <code>{nontls_config}</code>\n\n"
        message_text += f"📋订阅地址: <code>{sub_link}</code>"

        keyboard = InlineKeyboardMarkup()
        delete_button = InlineKeyboardButton("🗑️ 删除", callback_data=f"delete:{user_name}")
        qr_button = InlineKeyboardButton("🔲 二维码", callback_data=f"qr:{user_name}")
        return_button = InlineKeyboardButton("🔙 返回", callback_data="user_panel")
        keyboard.add(delete_button, qr_button, return_button)

        bot.send_message(call.message.chat.id, message_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        bot.send_message(call.message.chat.id, "❌ 未找到用户.❌")


def delete_worker(account_id, api_token, worker_name):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        print(f"Worker '{worker_name}' deleted successfully from Cloudflare.")
    else:
        print(f"Error: Failed to delete worker '{worker_name}' (Status code: {response.status_code})")

@bot.callback_query_handler(func=lambda call: call.data.startswith('qr:'))
def qr_vless(call):

    user_name = call.data.split(':')[1]

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM user WHERE name = ?', (user_name,))
    row = cursor.fetchone()

    connection.close()

    uuid = row[1]
    subdomain = row[2]

    vless_link = create_vless_config(subdomain, uuid, user_name)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(vless_link)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")

    img_bytes = BytesIO()
    qr_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    bot.send_photo(call.message.chat.id, img_bytes, caption="🤳 扫描我！ 🤳")

    del img_bytes
@bot.callback_query_handler(func=lambda call: call.data.startswith('delete:'))
def delete_user(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_name = call.data.split(':')[1]

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    delete_worker(account_id, api_token, user_name)

    cursor.execute('DELETE FROM user WHERE name = ?', (user_name,))
    connection.commit()

    connection.close()

    menu_markup = InlineKeyboardMarkup()
    add_user_button = InlineKeyboardButton("➕ 添加用户", callback_data="add_user")
    user_panel_button = InlineKeyboardButton("🔰 用户面板", callback_data="user_panel")
    menu_markup.add(add_user_button, user_panel_button)
    bot.send_message(call.message.chat.id, f"✅ Worker 用户名'{user_name}' 删除成功.✅", reply_markup=menu_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_user'))
def add_user_cfw(call):

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_button = types.KeyboardButton("Cancel")
    keyboard.add(cancel_button)
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_states[call.from_user.id] = 'waiting_for_filename'
    
    bot.send_message(call.message.chat.id, "请输入您的新用户的姓名. ", reply_markup=keyboard)


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_filename')
def handle_filename(message):
    if message.text.strip().lower() == '返回':
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌进程已取消.❌")
        send_welcome(message)
        return

    new_file_name = message.text.strip() + ".js"
    new_file_name_without_extension = new_file_name.replace('.js', '')
    new_subfile_name = new_file_name_without_extension + "_sub.js"
    if not os.path.exists(users_directory):
        os.makedirs(users_directory)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM user WHERE name = ?', (new_file_name_without_extension,))
    existing_user = cursor.fetchone()
    connection.close()
    
    if existing_user:
        bot.send_message(message.chat.id, "使用此名称的用户已存在。 请输入不同的用户名称.")
    else:
        new_file_path = os.path.join(users_directory, new_file_name)
        new_subsfile_path = os.path.join(users_directory, new_subfile_name)
        create_duplicate_file(index_js_path, new_file_path)
        create_duplicate_file(subs_js_path, new_subsfile_path)
        bot.send_message(message.chat.id, f"用户名 '{new_file_name}' 创建成功.✅")
        
        user_uuid = generate_uuid()
        replace_uuid_in_file(user_uuid, new_file_path)
        replace_uuid_in_sub_file(user_uuid, new_subsfile_path)
        replace_path_in_subfile(new_file_name_without_extension, new_subsfile_path)
        bot.send_message(message.chat.id, f"新用户的uuid ➡️ {user_uuid}")
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO user (name, uuid) VALUES (?, ?)', (new_file_name_without_extension, user_uuid))
        connection.commit()
        connection.close()
        user_states[message.from_user.id] = {'state': 'waiting_for_proxy', 'file_name':  new_file_name, 'uuid': user_uuid}
        bot.send_message(message.chat.id, "请输入新的 CloudFlare IP 或 CloudFlare 域名:")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_proxy')
def handle_proxy(message):
    if message.text.strip().lower() == '返回':
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌进程已取消.❌")
        send_welcome(message)
        return

    new_proxy_ip = message.text.strip()
    
    new_file_name = user_states[message.from_user.id]['file_name']
    
    new_file_path = os.path.join(users_directory, new_file_name)
    
    replace_proxy_ip_in_file(new_proxy_ip, new_file_path)
    bot.send_message(message.chat.id, f"添加了新的代理设置 ➡️ {new_proxy_ip}")

    new_txt_file_name = new_file_name.replace('.js', '.txt')
    create_duplicate_file('workertemp.txt', os.path.join(users_directory, new_txt_file_name))
    new_txt_subfile_name = new_file_name.replace('.js', '_sub.txt')
    create_duplicate_file('workertemp.txt', os.path.join(users_directory, new_txt_subfile_name))
    bot.send_message(message.chat.id, f"已成功存储到 'workertemp.txt' 目录中记录 '{new_txt_file_name}' in '用户' 保存成功.")
    new_file_name_without_extension = new_file_name.replace('.js', '')
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('UPDATE user SET ip = ? WHERE name = ?', (new_proxy_ip, new_file_name_without_extension))
    connection.commit()
    connection.close()
    user_states[message.from_user.id]['state'] = 'waiting_for_subdomain_or_worker_name'
    bot.send_message(message.chat.id, "请输入您worker的新子域: \n ℹ️ 实例: subdomain.yourdomain.com \n\n ℹ️ℹ️ 不要输入您没有的域名 !")    

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_for_subdomain_or_worker_name')
def handle_subdomain_and_worker_name(message):
    if message.text.strip().lower() == '返回':
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌进程已取消.❌")
        send_welcome(message)
        return

    new_subdomain = message.text.strip()
    
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM user WHERE subdomain = ?', (new_subdomain,))
    existing_user = cursor.fetchone()
    connection.close()

    if existing_user:
        bot.send_message(message.chat.id, f"❌子域 '{new_subdomain}' 已经存在。 请输入不同的子域.❌")
        
    else:
        new_file_name = user_states[message.from_user.id]['file_name']
        new_file_name_without_extension = new_file_name.replace('.js', '')

        user_uuid = user_states[message.from_user.id]['uuid']
        new_file_path = os.path.join(users_directory, new_file_name)
    
        new_txt_file_name = new_file_name.replace('.js', '.txt')
        new_txt_file_path = os.path.join(users_directory, new_txt_file_name)
        new_txt_subfile_name = new_file_name.replace('.js', '_sub.txt')
        new_txt_subfile_path = os.path.join(users_directory, new_txt_subfile_name)
        new_subfile_name = new_file_name_without_extension + "_sub.js"
        new_subsfile_path = os.path.join(users_directory, new_subfile_name)
        replace_subdomain_in_file(new_subdomain, new_txt_file_path)
        
        replace_subdomain_in_subfile(new_subdomain, new_subsfile_path)
        replace_ip_api(ip_api, new_subsfile_path)
        subworker_name = f"subworker{new_file_name_without_extension}"
        replace_name_in_file(new_txt_file_name, new_txt_file_path)
        replace_name_in_file(subworker_name, new_txt_subfile_path)

        subworker_host = f"sub{new_subdomain}"
        replace_subworker_host(subworker_host, new_file_path)
        replace_subdomain_in_file(subworker_host, new_txt_subfile_path)
        bot.send_message(message.chat.id, f"🌐正在创建您的新用户配置...🌐\n ⌛ 等待〜30秒-1分钟 ⌛")
        
        update_wrangler_toml(new_txt_file_path)
        sent_message = bot.send_message(message.chat.id, "⌛")
        wait_message_id = sent_message.message_id

        
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute('UPDATE user SET subdomain = ? WHERE name = ?', (new_subdomain, new_file_name_without_extension))
        connection.commit()
        connection.close()
        
        new_js_file_path = os.path.join(users_directory, new_file_name)
        
        deployment_status = run_nvm_use_and_wrangler_deploy(new_js_file_path)

        
        if deployment_status:
            bot.delete_message(message.chat.id, wait_message_id)
            bot.send_message(message.chat.id, "✅✅ Workers 节点及订阅部署成功!✅✅")
            update_wrangler_toml(new_txt_subfile_path)
            run_nvm_use_and_wrangler_deploy(new_subsfile_path)
            vless_config = create_vless_config(new_subdomain, user_uuid, new_file_name)
            nontls_config = create_nontls_config(new_subdomain, user_uuid, new_file_name)
            sub_link = f"https://{subworker_host}/{new_file_name_without_extension}"
            non_tls_config_html = f"<code>{nontls_config}</code>"
            vless_config_html = f"<code>{vless_config}</code>"
            message_text = f"开Tls: {vless_config_html}\n\n 未开Tls: {non_tls_config_html}\n\n Sub 地址: {sub_link}"
            menu_markup = InlineKeyboardMarkup()
            add_user_button = InlineKeyboardButton("➕ 添加用户", callback_data="add_user")
            user_panel_button = InlineKeyboardButton("🔰 用户面板", callback_data="user_panel")
            menu_markup.add(add_user_button, user_panel_button)
            bot.send_message(message.chat.id, message_text, reply_markup=menu_markup, parse_mode="HTML")
            del user_states[message.from_user.id]

        else:
            bot.delete_message(message.chat.id, wait_message_id)
            menu_markup = InlineKeyboardMarkup()
            add_user_button = InlineKeyboardButton("➕ 添加用户", callback_data="add_user")
            user_panel_button = InlineKeyboardButton("🔰 用户面板", callback_data="user_panel")
            menu_markup.add(add_user_button, user_panel_button)
            bot.send_message(message.chat.id, "❌部署失败。 请检查日志.❌", reply_markup=menu_markup)

def create_vless_config(new_subdomain, user_uuid, new_file_name):
    if new_file_name.endswith('.js'):
        new_file_name = new_file_name[:-3]

    vless_config = f"vless://{user_uuid}@cfip.xxxxxxxx.tk:443?encryption=none&security=tls&sni={new_subdomain}&fp=randomized&type=ws&host={new_subdomain}&path=%2F%3Fed%3D2048#{new_file_name}"
    return vless_config

def create_nontls_config(new_subdomain, user_uuid, new_file_name):
    if new_file_name.endswith('.js'):
        new_file_name = new_file_name[:-3]

    nontls_config = f"vless://{user_uuid}@cfip.xxxxxxxx.tk:80?encryption=none&security=&sni={new_subdomain}&fp=randomized&type=ws&host={new_subdomain}&path=%2F%3Fed%3D2048#{new_file_name}"
    return nontls_config

def run_nvm_use_and_wrangler_deploy(new_file_path):
    nvm_source_command = 'source ~/.nvm/nvm.sh && '

    subprocess.run(['bash', '-c', f'{nvm_source_command} nvm use 16.17.0'], check=True)

    result = subprocess.run(['bash', '-c', f'{nvm_source_command} npx wrangler deploy {new_file_path}'], capture_output=True, text=True, check=False)

    print(result.stdout)

    return "Current Deployment ID:" in result.stdout


def update_wrangler_toml(new_txt_file_path):
    wrangler_toml_path = 'wrangler.toml'
    with open(new_txt_file_path, 'r') as file:
        new_txt_content = file.read()

    with open(wrangler_toml_path, 'w') as file:
        file.write(new_txt_content)


def replace_name_in_file(name, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    name_without_extension = name.replace('.txt', '')  
    modified_contents = file_contents.replace('name = "nameofworker"', f'name = "{name_without_extension}"')
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_path_in_subfile(path, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("let mytoken= 'username';", f"let mytoken= '{path}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_ip_api(ip_api, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("let addressesapi = ['addressapi'];", f"let addressesapi = ['{ip_api}'];")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_subdomain_in_subfile(subdomain, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("host = env.HOST || 'usersubdomain';", f"host = env.HOST || '{subdomain}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_subdomain_in_file(subdomain, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace('pattern = "subdomain"', f'pattern = "{subdomain}"')
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def create_duplicate_file(original_file, new_file):
    with open(original_file, 'r') as file:
        original_contents = file.read()
    with open(new_file, 'w') as new_file:
        new_file.write(original_contents)

def generate_uuid():
    user_uuid = uuid.uuid4()
    return str(user_uuid)

def replace_uuid_in_sub_file(uuid, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("uuid = env.UUID || 'uuid';", f"uuid = env.UUID || '{uuid}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)
        
def replace_subworker_host(workerhost, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("let sub = 'subworkerhost';", f"let sub = '{workerhost}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_uuid_in_file(uuid, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("let userID = 'uuid';", f"let userID = '{uuid}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

def replace_proxy_ip_in_file(proxy_ip, file_path):
    with open(file_path, 'r') as file:
        file_contents = file.read()
    modified_contents = file_contents.replace("let proxyIP = 'newproxy';", f"let proxyIP = '{proxy_ip}';")
    with open(file_path, 'w') as file:
        file.write(modified_contents)

# def start_bot():
#     bot.polling(none_stop=False)
#     #         except KeyboardInterrupt:
# #             print("\n机器人已被停止.")
# #             break
        
def start_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except KeyboardInterrupt:
            print("\n机器人已被停止.")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("✅ GFW 机器人启动 ✅\n ✌️ 奋起为自由而战 ✌️")
    start_bot()
