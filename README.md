# GFW-BOT
Cloudflare Woker 机器人！ 不需要服务器，只需创建纯粹的 Xray 链接，所有这些都可以在 PythonAnywhere 上顺利运行。 通往互联网自由的捷径！ ✨"

![1](https://github.com/2ri4eUI/CFW-BOT/assets/139592104/a2ff80e6-3c33-4443-9ee5-85b445e4a9f6)

# version 0.02 | 新内容 ?
- 它可以为每个可以使用IP-API值的用户创建唯一的订阅工作链接
- 只需更改 IP_API 值即可更新订阅
- cloudflare 网站错误已解决
  
## 目录
- [关于 ?](#关于-)
  - [特征](#特征)
  - [条件](#条件)
  - [容器上部署](#容器上部署)
  - [VPS上安装步骤](#VPS上安装步骤)
  - [如何使用机器人](#如何使用机器人)
- [笔记](#笔记)
- [免责声明](#免责声明)

# 关于?
这个 Python Telegram 机器人由 Cloudflare 的 Workers 提供支持，使生成 Xray 链接变得轻而易举！ 无需复杂的服务器设置，只需按照以下简单步骤即可开始：
## Features
- **Easy Setup**: No server configurations required. With Cloudflare's Workers, deploying the bot is a breeze.
- **Persistent Storage**: Utilizes SQLite for database management, ensuring that your user data and generated links are securely stored.
- **User Management**: Create and manage multiple users with ease. Each user has access to their generated links at all times.
- **Efficient Deployment**: Leveraging Wrangler, the bot's worker script can be easily deployed on Cloudflare, ensuring reliability and scalability.

## Prerequisites
- One domain registered on Cloudflare
- Access to Cloudflare account
- Telegram Bot token (available from Telegram's BotFather)
- Cloudflare API key (generate one from Cloudflare dashboard)
- Account ID of your Cloudflare account
- User ID of the Telegram account you want to use the bot on (for authentication)

## LAZY INSTALL
1. Register for a free account on [PythonAnywhere](https://www.pythonanywhere.com).
2. Obtain the required API keys:
   - Telegram Bot token from BotFather
   - Cloudflare API key from Cloudflare dashboard (make sure to select "Edit Cloudflare Workers template" and grant necessary permissions, all of them should have EDIT permission)
   - Telegram UserID you can obtain it from here https://t.me/useridinfobot or any similar bot you know
   - Cloudflare Account id, you can find it from right side of overview page or worker page in cloudflare
4. in your Dashboard section Select Files and and Click on "Open Bash Console Here"
5.  Clone this repository:
 ```bash
 git clone https://github.com/自己用户名/项目名称.git
```
6. Navigate to the project directory:

 ```bash
 cd GFW-BOT
 ```
7. Make `requirement.sh` executable:
 ```bash
 chmod +x requirement.sh
 ```

8. Run `dos2unix.py`:
"If you encounter errors running requirement.sh on PythonAnywhere , simply close the console (using `exit` command) , go to file manager and open it and  save it (use `ctrl+s` ) without changing any thing. thats it! now you can run it"
another solution is converting it using dos2unix 
since PythonAnyWhere does not support that you can use this simple python code 'dos2unix.py'
you can run this to solve the issue:
 ```bash
 python3 dos2unix.py
 ```
9. Run `requirement.sh`:
 ```bash
 ./requirement.sh
 ```
10. Run `install.py` and provide the required API tokens when prompted:
 ```bash
 python3 install.py
 ```
11. Start the bot:
 ```bash
 python3 gfw.py
 ```
## ADVANCED INSTALL

1. install requirements:
 ```bash
 pip install telebot
 pip install pytelegrambotapi --upgrade
 pip install qrcode[pil]
 pip install requests
 pip install python-dotenv
 ```
2. install NVM
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
```
3. set nvm settings
``` bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads NVM
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads NVM bash completion
```
4. start nvm and install wrangler
```bash
nvm install 16.17.0
nvm use 16.17.0
npm install wrangler@latest
npx wrangler --version
```
5. set .env file variables


| Variable             | Description                                            |
|----------------------|--------------------------------------------------------|
| CLOUDFLARE_API_TOKEN | Cloudflare API token with Worker edit permission       |
| BOT_TOKEN            | Telegram bot token obtained from BotFather             |
| ACCOUNT_ID           | Cloudflare account ID                                  |
| ADMIN_USER_ID        | Numeric Telegram user ID for admin authentication      |
| IP_API               | use this as refrence https://raw.githubusercontent.com/2ri4eUI/CFW_Worker_Sub/main/ips.txt|

6.remember to set cloudflare account id in workertemp.txt 


## How To Use the Bot
Once the bot is running, simply send the necessary commands to generate Xray links right from your Telegram app!
Creating a new user is a straightforward process. Follow these steps to get started:
**Obtain Cloudflare IP or Domain:**
   - Use platforms like [fofa.info](https://fofa.info) to find Cloudflare IP addresses or domains.
   - Example search query for fofa.info:
 ```bash
 
 server=="cloudflare" && port=="443" && country=="NL" && city=="Amsterdam"
 ```
   - Choose based on your preferences and network speed.

## Note
This bot is designed to be lightweight and inexpensive to run, making it accessible for everyone. Enjoy creating Xray links hassle-free!
