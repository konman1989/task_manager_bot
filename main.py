# import logging
import os
import re
from time import sleep
from telebot import TeleBot, types

import handlers
from emails import email_notification
from utils import build_keyboard, build_inline_keyboard

BOT_KEY = os.getenv('TASK_MANAGER_BOT_TOKEN')
bot = TeleBot(BOT_KEY)

# TODO try/except clauses
# TODO Work on logic upon creating a new user and adding their to dashboards

EMOJI = {
    'dashboard': '\U0001F5C2',
    'task': '\U0001F4CB',
    'user': '\U0001F465',
    'back': '\u21A9',
    'add': '\U0001F195',
    'main': '\u25B6',
    'comment': '\U0001F4DD',
    'delete': '\U0000274C',
    'yes': '\U00002705',
    'update': '\U0000270F',
    'account': '\U0001F464',
    'stats': '\U0001F4CA',
    'email': '\U0001F4E7',
    'TO DO': '\U0001F534',
    'IN PROCESS': '\U0001F7E1',
    'DONE': '\U0001F7E2'
}

COMMANDS = [
    f'{EMOJI["main"]} Main Menu',
    f'{EMOJI["dashboard"]} Dashboards',
    f'{EMOJI["task"]} My Tasks',
    f'{EMOJI["comment"]} My Comments',
    f'{EMOJI["back"]} Back to Main Menu',
    f'{EMOJI["email"]} Send Email'
]


@bot.message_handler(commands=['start', 'help'])
def send_options(message):
    user = handlers.get_user(message.chat.id)
    if user != 'Not found':
        text = "This is a Task Manager Bot. You can create your own dashboards" \
               " or join other user's ones. Inside dashboard you can create " \
               "tasks, add users and comments."

        bot.send_message(message.chat.id, text)
        sleep(1.0)
        main_menu(message)
        return

    text = 'Welcome to Task Manager Bot. You can create a new dashboard or ' \
           'join existing one. Inside dashboard you can create tasks, ' \
           'add users and comments. To proceed you need to create an ' \
           'account below:'

    bot.send_message(message.chat.id, text,
                     reply_markup=build_keyboard(
                         f'{EMOJI["add"]} Create Account'))


@bot.message_handler(func=lambda x: x.text == f'{EMOJI["add"]} Create Account')
def create_account(message):
    user = handlers.get_user(message.chat.id)
    if user != 'Not found':
        bot.send_message(message.chat.id, 'You already have an account.')
        sleep(1.0)
        main_menu(message)
        return
    msg = bot.send_message(message.chat.id, 'OK. Send me your name:',
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu'))

    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    if message.text == f'{EMOJI["back"]} Back to Main Menu':
        bot.send_message(message.chat.id, 'OK. Tell me when you are ready.',
                         reply_markup=build_keyboard('Create Account'))
        return
    user = {'username': message.text, 'chat_id': message.chat.id, }
    msg = bot.send_message(message.chat.id, f'Thank you, {user["username"]}.'
                                            f' Send me your email:')

    bot.register_next_step_handler(msg, process_email_step, user)


def process_email_step(message, user):
    if message.text == f'{EMOJI["back"]} Back to Main Menu':
        bot.send_message(message.chat.id, 'OK. Tell me when you are ready.',
                         reply_markup=build_keyboard('Create Account'))
        return
    pattern = re.compile(r'^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$')
    result = re.match(pattern, message.text)
    if not result:
        msg = bot.send_message(
            message.chat.id,
            'Email seems to be invalid. Please type email in format '
            'name@domen.com, no spaces allowed.')
        bot.register_next_step_handler(msg, process_email_step, user)
        return

    user['email'] = message.text.lower()
    bot.send_message(message.chat.id,
                     'Thank you, creating your account...')
    create_user(message, user)


def create_user(message, user):
    req = handlers.create_user(user)
    sleep(1.0)
    if req == 201:
        bot.send_message(
            message.chat.id,
            "Your account has been created. You can create a new dashboard or "
            "join existing one. To join a dashboard, you need to pass the "
            "dashboard admin your email and they will add you.",
            reply_markup=build_keyboard(f'{EMOJI["add"]} Create Dashboard')
        )
        return
    bot.send_message(message.chat.id,
                     f"Creating account failed. Please try again.")


@bot.message_handler(func=lambda x: x.text == f'{EMOJI["account"]} My Account')
def get_account_details(message):
    user = handlers.get_user(message.chat.id)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            f'{EMOJI["update"]} Update Name',
            callback_data=f'update_user_username'),
        types.InlineKeyboardButton(
            f'{EMOJI["update"]} Update Email',
            callback_data=f'update_user_email'),
        types.InlineKeyboardButton(
            f'{EMOJI["delete"]} Delete Account',
            callback_data=f'delete_account_{user["chat_id"]}')
    )
    bot.send_message(message.chat.id,
                     text=f"*Here is your account details:*\n\n"
                          f"*Name:* {user['username']}\n"
                          f"*Email:* {user['email']}\n",
                     reply_markup=keyboard,
                     parse_mode='Markdown')


def update_user(message, data):
    if message.text in COMMANDS:
        command_checker(message)
        return
    if data == 'email':
        pattern = re.compile(r'^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$')
        result = re.match(pattern, message.text)
        if not result:
            msg = bot.send_message(
                message.chat.id,
                'Email seems to be invalid. Please type email in format '
                'name@domen.com, no spaces allowed.')
            bot.register_next_step_handler(msg, update_user, data)
            return
        update_data = {data: message.text.lower()}
    else:
        update_data = {data: message.text}

    req = handlers.update_user(message.chat.id, update_data)

    if req == 204:
        bot.send_message(message.chat.id, f'Your account has been updated.')
        get_account_details(message)
        return
    bot.send_message(message.chat.id,
                     'Updating account was unsuccessful. '
                     'Please try again.')
    get_account_details(message)


def delete_account(message, chat_id):
    if message.text in COMMANDS:
        command_checker(message)
        return
    if message.text == f'{EMOJI["yes"]} Yes':
        req = handlers.delete_user(chat_id)
        if req == 200:
            bot.send_message(message.chat.id, 'Account has been deleted.',
                             reply_markup=build_keyboard('Create Account'))

            return
        bot.send_message(message.chat.id,
                         'Deleting account was unsuccessful. '
                         'Please try again.',
                         reply_markup=build_keyboard(
                             f'{EMOJI["account"]} My Account'))

        return
    get_account_details(message)


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["dashboard"]} Dashboards')
def get_dashboards(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    d_board = [d.get('name') for d in dashboards]
    d_board_hidden = [d.get('id') for d in dashboards]

    keyboard = build_inline_keyboard(d_board, d_board_hidden,
                                     'dashboard_detailed')

    keyboard.add(
        types.InlineKeyboardButton(f'{EMOJI["add"]} Create Dashboard',
                                   callback_data='create_dashboard'),
        types.InlineKeyboardButton(f'{EMOJI["back"]} Back to Main Menu',
                                   callback_data='main'))
    bot.send_message(message.chat.id, 'Getting your dashboards...',
                     reply_markup=build_keyboard(
                         f'{EMOJI["add"]} Create Task',
                         f'{EMOJI["add"]} Add User to Dashboard',
                         f'{EMOJI["main"]}️ Main Menu')
                     )
    bot.send_message(message.chat.id, 'Your dashboards:',
                     reply_markup=keyboard)


def update_dashboard(message, chat_id, d_id):
    if message.text in COMMANDS:
        command_checker(message)
        return
    req = handlers.update_dashboard(chat_id, d_id, message.text)
    if req == 204:
        bot.send_message(message.chat.id, f'Dashboard name has been changed to'
                                          f' {message.text}.')
        main_menu(message)
        return
    else:
        bot.send_message(message.chat.id,
                         'Updating dashboard was unsuccessful. '
                         'Please note, only dashboard admins can update or '
                         'delete dashboards.')
        main_menu(message)


def delete_dashboard(message, chat_id, d_id):
    if message.text == f'{EMOJI["yes"]} Yes':
        req = handlers.delete_dashboard(chat_id, d_id)
        if req == 200:
            bot.send_message(message.chat.id, 'Dashboard has been deleted.')
            main_menu(message)
            return
        bot.send_message(message.chat.id,
                         'Deleting dashboard was unsuccessful. '
                         'Please note, only dashboard admins can delete or '
                         'update dashboards.')

        main_menu(message)
        return
    main_menu(message)


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["add"]} Create Dashboard')
def initiate_dashboard_creation(message):
    msg = bot.send_message(message.chat.id, 'OK. Send me your dashboard name:',
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu'))

    bot.register_next_step_handler(msg, process_dashboard_name_step)


def process_dashboard_name_step(message):
    if message.text == f'{EMOJI["back"]} Back to Main Menu':
        bot.send_message(message.chat.id, 'OK. Tell me when you are ready.',
                         reply_markup=build_keyboard(
                             f'{EMOJI["add"]} Create Dashboard',
                             'Join Dashboard'))
        return
    if message.text in COMMANDS:
        command_checker(message)
        return

    dashboard = {'dashboard_name': message.text}
    bot.send_message(
        message.chat.id,
        f'OK. Creating {dashboard["dashboard_name"]} dashboard...')

    create_dashboard(message, dashboard)


def create_dashboard(message, data):
    req = handlers.create_dashboard(message.chat.id, data)

    sleep(1.0)
    if req == 201:
        bot.send_message(
            message.chat.id,
            f"Dashboard {data['dashboard_name']} has been created. You can "
            f"create a new task or add users to your dashboard now.",
            reply_markup=build_keyboard(
                f'{EMOJI["add"]} Create Task',
                f'{EMOJI["add"]} Add User',
                f'{EMOJI["dashboard"]} Dashboards',
                f'{EMOJI["back"]} Back to Main Menu'))
        return
    bot.send_message(message.chat.id,
                     f"Creating dashboard failed. Please try again.")


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["add"]} Add User to Dashboard'
                   or x.text == f'{EMOJI["add"]} Add User')
def initiate_adding_user(message):
    dashboards = handlers.get_user_dashboards_as_admin(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the dashboard to add new user to:",
                           reply_markup=build_keyboard(
                               *user_dashboards,
                               f'{EMOJI["back"]} Back to Main Menu')
                           )

    bot.register_next_step_handler(msg, locate_user_dashboard_step, dashboards)


def locate_user_dashboard_step(message, dashboards):
    if message.text in COMMANDS:
        command_checker(message)
        return
    d_id = [d.get('id') for d in dashboards if
            d.get('name') == message.text]
    if not d_id:
        msg = bot.send_message(message.chat.id,
                               'Dashboard does not exist. Choose a dashboard '
                               'from the list below:')
        bot.register_next_step_handler(msg, locate_user_dashboard_step,
                                       dashboards)
        return
    msg = bot.send_message(message.chat.id, "OK. Send me user's email:",
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu')
                           )

    bot.register_next_step_handler(msg, process_user_email_step, d_id[0])


def process_user_email_step(message, dashboard, email=None):
    if message.text == f'{EMOJI["email"]} Send Email':
        user = handlers.get_user(message.chat.id).get('username')
        link = 'https://t.me/BestTaskManagerBot'
        content = f"{user} was trying to add you to their dashboard in Best " \
                  f"Task Manager Bot but noticed that you are not registered " \
                  f"yet. If you still want to join you can click following " \
                  f"link:\n\n{link}\n\n--\nBest Task Manager Bot"

        email_notification(user, email, content)

        bot.send_message(message.chat.id,
                         f'OK. Sending an email to {email}...')
        sleep(1.0)
        bot.send_message(message.chat.id,
                         'Email has been sent.')
        main_menu(message)
        return

    if message.text in COMMANDS:
        command_checker(message)
        return

    pattern = re.compile(r'^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$')
    result = re.match(pattern, message.text)
    if not result:
        msg = bot.send_message(
            message.chat.id,
            'Email seems to be invalid. Please type email in format '
            'name@domen.com, no spaces allowed.')
        bot.register_next_step_handler(msg, process_user_email_step, dashboard)
        return

    email = message.text
    bot.send_message(message.chat.id,
                     'Thank you, checking if user is registered...')
    user = handlers.get_user_by_email(email)
    sleep(1.0)
    if user == 'Not found':
        msg = bot.send_message(
            message.chat.id,
            f"User with email {email} is not registered or email is wrong. "
            f"If this is a correct email, we can send an email on your behalf "
            f"to join Best Telegram Manager Bot. To confirm, press the button "
            f"below:",
            reply_markup=build_keyboard(
                f'{EMOJI["email"]} Send Email',
                f'{EMOJI["back"]} Back to Main Menu')
        )
        bot.register_next_step_handler(msg, process_user_email_step, dashboard,
                                       email)
        return
    bot.send_message(message.chat.id,
                     'OK. User found. Adding user to dashboard...')
    add_user_to_dashboard(message, user['chat_id'], dashboard)


def add_user_to_dashboard(message, user_id, dashboard):
    req = handlers.add_user_to_dashboard(message.chat.id, user_id, dashboard)
    sleep(1.0)
    if req == 201:
        bot.send_message(message.chat.id, "User has been added.",
                         reply_markup=build_keyboard(
                             f'{EMOJI["back"]} Back to Main Menu')
                         )
        # sending notification to the added user
        bot.send_message(user_id,
                         "You have been added to a new dashboard",
                         reply_markup=build_keyboard(
                             f'{EMOJI["dashboard"]} Dashboards',
                             f'{EMOJI["task"]} My Tasks',
                             f'{EMOJI["comment"]} My Comments',
                             f'{EMOJI["account"]} My Account')
                         )
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed. Please try again")


@bot.message_handler(func=lambda x: x.text == f'{EMOJI["task"]} My Tasks')
def get_tasks(message):
    """TODO add dashboard id to task_detailed"""
    tasks = handlers.get_user_stats(message.chat.id, 'tasks')
    tasks_hidden = [
        '_'.join([str(t.get('dashboard_id')), str(t.get('task_name')),
                  str(t.get('id'))])
        for t in tasks]

    tasks = [t.get('task_name') for t in tasks]

    keyboard = build_inline_keyboard(tasks, tasks_hidden,
                                     f'task_detailed')

    keyboard.add(
        types.InlineKeyboardButton(f'{EMOJI["back"]} Back to Main Menu',
                                   callback_data='main')
    )
    bot.send_message(message.chat.id, 'Getting your tasks...',
                     reply_markup=build_keyboard(
                         f'{EMOJI["add"]} Create Task',
                         f'{EMOJI["add"]} Add User to Task',
                         f'{EMOJI["main"]}️ Main Menu'))
    bot.send_message(message.chat.id, 'Your tasks:',
                     reply_markup=keyboard)


def update_task(message, task_data, status_buttons=None):
    """TO DO change task admins. Should have additional admin button"""

    if task_data['update_instance'] == 'status' \
            and message.text not in status_buttons:
        msg = bot.send_message(message.chat.id,
                               'Wrong input. Please choose from the following '
                               'options:')
        bot.register_next_step_handler(msg, update_task, task_data,
                                       status_buttons)
        return
    if message.text in COMMANDS:
        command_checker(message)
        return
    bot.send_message(message.chat.id, 'Updating your task...')

    req = handlers.update_task(message.chat.id, task_data, message.text)
    sleep(1.0)
    if req == 204:
        bot.send_message(message.chat.id,
                         f"Task has been successfully updated")
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Updating task was unsuccessful. Please try again.")
    main_menu(message)


def delete_task(message, task_data):
    if message.text == f'{EMOJI["yes"]} Yes':
        req = handlers.delete_task(message.chat.id, task_data)
        if req == 200:
            bot.send_message(message.chat.id, 'Task has been deleted.')
            main_menu(message)
            return
        bot.send_message(message.chat.id,
                         'Deleting task was unsuccessful. '
                         'Please try again')

    main_menu(message)


def process_task_details_step(message, task_data, buttons):
    if message.text not in buttons:
        msg = bot.send_message(message.chat.id,
                               'Wrong input. Please choose from the following '
                               'options:')
        bot.register_next_step_handler(msg, process_task_details_step,
                                       task_data, buttons)
        return
    if message.text in COMMANDS:
        command_checker(message)
        return
    if message.text == 'Name':
        msg = bot.send_message(message.chat.id, 'OK. Send me a new name:')
        task_data['update_instance'] = 'task_name'
        bot.register_next_step_handler(msg, update_task, task_data)

    if message.text == 'Description':
        msg = bot.send_message(message.chat.id,
                               'OK. Send me a new description:')
        task_data['update_instance'] = 'text'
        bot.register_next_step_handler(msg, update_task, task_data)

    if message.text == 'Current Status':
        status_buttons = ['TO DO', 'IN PROCESS', 'DONE',
                          f'{EMOJI["back"]} Back to Main Menu']
        msg = bot.send_message(message.chat.id, 'OK. Send me a new status:',
                               reply_markup=build_keyboard(*status_buttons))
        task_data['update_instance'] = 'status'
        bot.register_next_step_handler(msg, update_task, task_data,
                                       status_buttons)


@bot.message_handler(func=lambda x: x.text == f'{EMOJI["add"]} Create Task')
def initiate_task_creation(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           'OK. Choose dashboard new task will belong to:',
                           reply_markup=build_keyboard(
                               *user_dashboards,
                               f'{EMOJI["back"]} Back to Main Menu'))

    bot.register_next_step_handler(msg, locate_dashboard_step, dashboards)


def locate_dashboard_step(message, dashboards):
    if message.text in COMMANDS:
        command_checker(message)
        return
    d_id = [d.get('id') for d in dashboards if d.get('name') == message.text]
    if not d_id:
        msg = bot.send_message(message.chat.id,
                               'Dashboard does not exist. Choose a dashboard '
                               'from the list below:')
        bot.register_next_step_handler(msg, locate_dashboard_step, dashboards)
        return
    msg = bot.send_message(message.chat.id, 'OK. Send me your task name:',
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu')
                           )
    task = {'dashboard_id': d_id[0]}
    bot.register_next_step_handler(msg, process_task_name_step, task)


def process_task_name_step(message, task):
    if message.text in COMMANDS:
        command_checker(message)
        return
    task['task_name'] = message.text
    msg = bot.send_message(message.chat.id,
                           'OK. Send me your task description. You can include'
                           ' specific information about the task, instructions'
                           ' and other details:',
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu')
                           )
    bot.register_next_step_handler(msg, process_task_description_step, task)


def process_task_description_step(message, task):
    if message.text in COMMANDS:
        command_checker(message)
        return
    task['text'] = message.text
    bot.send_message(message.chat.id, 'OK. Creating your task...')
    create_task(message, task)


def create_task(message, task):
    req = handlers.create_task(message.chat.id, task)
    sleep(1.0)

    if req == 201:
        bot.send_message(
            message.chat.id,
            f"Task {task['task_name']} has been created. You can "
            f"change task status, add comments or users to your task.",
            reply_markup=build_keyboard(
                f'{EMOJI["back"]} Back to Main Menu'))
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Creating task failed. Please try again.")


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["add"]} Add User to Task')
def initiate_adding_user_to_task(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the dashboard first:",
                           reply_markup=build_keyboard(
                               *user_dashboards,
                               f'{EMOJI["back"]} Back to Main Menu')
                           )

    bot.register_next_step_handler(msg, locate_user_task_step, dashboards)


def locate_user_task_step(message, dashboards):
    if message.text in COMMANDS:
        command_checker(message)
        return
    d_id = [d.get('id') for d in dashboards if
            d.get('name') == message.text]
    if not d_id:
        msg = bot.send_message(message.chat.id,
                               'Dashboard does not exist. Choose a dashboard '
                               'from the list below:')
        bot.register_next_step_handler(msg, locate_user_task_step,
                                       dashboards)
        return
    dashboard_tasks = handlers.get_dashboard_tasks(d_id[0])
    tasks = [t.get('task_name') for t in dashboard_tasks]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the task to add user to:",
                           reply_markup=build_keyboard(
                               *tasks,
                               f'{EMOJI["back"]} Back to Main Menu')
                           )

    bot.register_next_step_handler(msg, locate_task_users_step, d_id[0],
                                   dashboard_tasks)


def locate_task_users_step(message, d_id, tasks=None, task=None):
    if message.text in COMMANDS:
        command_checker(message)
        return
    if task is None:
        task = [t for t in tasks if t.get('task_name') == message.text][0]
        if not task:
            msg = bot.send_message(message.chat.id,
                                   'Task does not exist. Choose a task from '
                                   'the list below:')
            bot.register_next_step_handler(msg, locate_task_users_step, tasks,
                                           d_id)
            return
    dashboard_users = handlers.get_dashboard_users(d_id)
    users = [u.get('username') for u in dashboard_users]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me a user to add to task:",
                           reply_markup=build_keyboard(
                               *users,
                               f'{EMOJI["back"]} Back to Main Menu')
                           )
    bot.register_next_step_handler(msg, process_adding_user_step, task,
                                   dashboard_users)


def process_adding_user_step(message, task, users):
    if message.text in COMMANDS:
        command_checker(message)
        return
    user_id = [u.get('chat_id') for u in users if
               u.get('username') == message.text]

    if not user_id:
        msg = bot.send_message(message.chat.id,
                               'User does not exist. Choose a task from the '
                               'list below:')
        bot.register_next_step_handler(msg, process_adding_user_step, task,
                                       users)
        return
    bot.send_message(message.chat.id,
                     'OK. Adding user to task...')

    add_user_to_task(message, user_id, task['dashboard_id'], task['id'])


def add_user_to_task(message, user_id, task_id, dashboard_id):
    req = handlers.add_user_to_task(message.chat.id, user_id, task_id,
                                    dashboard_id)
    sleep(1.0)

    if req == 201:
        bot.send_message(message.chat.id, "User has been added.",
                         reply_markup=build_keyboard(
                             f'{EMOJI["back"]} Back to Main Menu')
                         )
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed with status code. Please try again")


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["comment"]} Post Comment')
def initiate_posting_comment(message, comment_data):
    if message.text in COMMANDS:
        command_checker(message)
        return

    comment_data['title'] = message.text
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the comment text:",
                           reply_markup=build_keyboard(
                               f'{EMOJI["back"]} Back to Main Menu')
                           )

    bot.register_next_step_handler(msg, process_comment_text_step,
                                   comment_data)


def process_comment_text_step(message, comment_data):
    if message.text in COMMANDS:
        command_checker(message)
        return

    comment_data['text'] = message.text
    comment_data['chat_id'] = message.chat.id
    bot.send_message(message.chat.id, 'OK. Posting your comment...')

    post_comment(message, comment_data)


def post_comment(message, comment_data):
    req = handlers.post_comment(comment_data)
    sleep(1.0)

    if req == 201:
        bot.send_message(message.chat.id, "Comment has been posted.",
                         reply_markup=build_keyboard(
                             f'{EMOJI["back"]} Back to Main Menu')
                         )
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Posting comment was unsuccessful. Please try again.")


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["comment"]} My Comments')
def get_user_comments(message):
    # TODO add pagination
    comments = handlers.get_user_comments(message.chat.id)
    sleep(1.0)

    for c in comments:
        bot.send_message(message.chat.id,
                         text=f"*Title*: {c.get('title')}\n"
                              f"*Comment*: {c.get('comment')}\n"
                              f"*Task*: {c.get('task')}\n"
                              f"*Posted*: {c.get('created_at')}",
                         parse_mode='Markdown')


@bot.message_handler(
    func=lambda x: x.text == f'{EMOJI["main"]}️ Main Menu' or
                   x.text == f'{EMOJI["back"]} Back to Main Menu')
def main_menu(message):
    bot.send_message(message.chat.id,
                     "You can navigate following sections:\n"
                     " - Dashboards\n"
                     " - Tasks\n"
                     " - Users\n"
                     " - Your account",
                     reply_markup=build_keyboard(
                         f'{EMOJI["dashboard"]} Dashboards',
                         f'{EMOJI["task"]} My Tasks',
                         f'{EMOJI["comment"]} My Comments',
                         f'{EMOJI["account"]} My Account'))


@bot.callback_query_handler(func=lambda call: True)
def process_callback_requests(call):
    if call.data == 'main':
        main_menu(call.message)

    elif call.data == f'{EMOJI["add"]} Create Dashboard' or 'create_dashboard' \
            in call.data:
        initiate_dashboard_creation(call.message)

    elif call.data == 'dashboard_main':
        dashboards = handlers.get_user_dashboards(call.message.chat.id)
        d_board = [d.get('name') for d in dashboards]
        d_board_hidden = [d.get('id') for d in dashboards]

        keyboard = build_inline_keyboard(d_board, d_board_hidden,
                                         'dashboard_detailed')

        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["add"]} Create Dashboard',
                callback_data='create_dashboard'),
            types.InlineKeyboardButton(f'{EMOJI["back"]} Back to Main Menu',
                                       callback_data='main'))

        bot.edit_message_text(text='Your dashboards:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif 'dashboard_detailed' in call.data:
        d_board_id = call.data.split('_')[-1]
        d_board_name = call.data.split('_')[-2]

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(types.InlineKeyboardButton(
            f'{EMOJI["task"]} Tasks',
            callback_data=f'dashboard_tasks_{d_board_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["user"]} Users',
                callback_data=f'dashboard_users_{d_board_id}')
        )
        keyboard.add(types.InlineKeyboardButton(
            f'{EMOJI["update"]} Update Dashboard',
            callback_data=f'update_dashboard_{d_board_name}_{d_board_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["delete"]} Delete Dashboard',
                callback_data=f'delete_dashboard_{d_board_name}_{d_board_id}')
        )
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["stats"]} Statistics',
                callback_data=f'dashboard_stats_{d_board_name}_{d_board_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main'))

        bot.edit_message_text(text=f'*{d_board_name} details:*',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard,
                              parse_mode='Markdown')

    elif 'dashboard_stats' in call.data:
        d_board_id = call.data.split('_')[-1]
        d_board_name = call.data.split('_')[-2]
        req = handlers.get_dashboard_stats(d_board_id)

        if not req.get('status'):
            bot.send_message(call.message.chat.id,
                             f'Dashboard {d_board_name} has no tasks yet.')
            return

        to_do = [i for i in req.get('status') if i == 'TO DO']
        in_process = [i for i in req.get('status') if i == 'IN PROCESS']
        done = [i for i in req.get('status') if i == 'DONE']

        done_len = len(done) / len(req.get('status'))
        to_do_len = (len(to_do) + len(in_process)) / len(req.get('status'))
        done_tasks_percent = round(done_len * 100)
        done_len = round(done_len * 16)
        to_do_len = round(to_do_len * 16)

        progress_bar = "".join(['✓' for _ in range(0, done_len)]) + "".join(
            ['×' for _ in range(0, to_do_len)])

        text = f"*Dashboard {d_board_name} statistics:*\n\n" \
               f"{EMOJI['TO DO']} *TO DO*: {len(to_do)} tasks\n" \
               f"{EMOJI['IN PROCESS']} *IN PROCESS*: {len(in_process)} tasks\n" \
               f"{EMOJI['DONE']} *DONE*: {len(done)} tasks\n\n" \
               f"*Completed tasks:* {done_tasks_percent} %\n" \
               f"{progress_bar}\n"

        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

    elif 'dashboard_users' in call.data:
        d_board_id = call.data.split('_')[-1]

        users = handlers.get_dashboard_users(d_board_id)
        users_hidden = [u.get('chat_id') for u in users]
        users = [u.get('username') for u in users]

        keyboard = build_inline_keyboard(users, users_hidden,
                                         f'user_detailed_{d_board_id}')
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["add"]} Add User',
                callback_data=f'add_user_dashboard_{d_board_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main')
        )
        bot.edit_message_text(text=f'*Dashboard users:*',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard,
                              parse_mode='Markdown')

    elif 'add_user_dashboard' in call.data:
        d_board_id = call.data[-1]

        msg = bot.send_message(call.message.chat.id,
                               "OK. Send me user's email:",
                               reply_markup=build_keyboard(
                                   f'{EMOJI["back"]} Back to Main Menu')
                               )

        bot.register_next_step_handler(msg, process_user_email_step,
                                       d_board_id)

    elif 'dashboard_tasks' in call.data:
        d_board_id = call.data.split('_')[-1]

        tasks = handlers.get_dashboard_tasks(d_board_id)
        task = [t.get('task_name') for t in tasks]
        task_hidden = [t.get('id') for t in tasks]

        keyboard = build_inline_keyboard(task, task_hidden,
                                         f'task_detailed_{d_board_id}')
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["add"]} Create Task',
                callback_data=f'create_task_{d_board_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main'))

        bot.edit_message_text(text=f'*Dashboard tasks:*',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard,
                              parse_mode='Markdown')

    elif 'update_dashboard' in call.data:
        d_board = call.data.split('_')
        msg = bot.send_message(call.message.chat.id,
                               f'OK. Give me a new name for dashboard'
                               f' {d_board[-2]}:',
                               reply_markup=build_keyboard(
                                   f'{EMOJI["back"]} Back to Main Menu')
                               )
        bot.register_next_step_handler(msg, update_dashboard,
                                       call.message.chat.id, d_board[-1])

    elif 'delete_dashboard' in call.data:
        d_board = call.data.split('_')
        msg = bot.send_message(call.message.chat.id,
                               f'Are you sure you want to delete dashboard'
                               f' {d_board[-2]}?',
                               reply_markup=build_keyboard(
                                   f'{EMOJI["yes"]} Yes',
                                   f'{EMOJI["delete"]} No')
                               )
        bot.register_next_step_handler(msg, delete_dashboard,
                                       call.message.chat.id, d_board[-1])

    elif 'user_detailed' in call.data:
        user = call.data.split('_')[-1]
        d_board_id = call.data.split('_')[-3]

        user = handlers.get_user(user)
        user_id = user.get('chat_id')

        keyboard = types.InlineKeyboardMarkup()
        d_board = handlers.get_dashboard(d_board_id)
        d_board_name = d_board.get("name")
        # adding a delete user button
        if d_board.get('admin_id') != user_id \
                and d_board.get('admin_id') == call.message.chat.id:
            keyboard.add(
                types.InlineKeyboardButton(
                    f'{EMOJI["delete"]} Remove User',
                    callback_data=f'remove_user_d_{d_board_name}_{d_board_id}_'
                                  f'{user_id}'),
                types.InlineKeyboardButton(
                    f'{EMOJI["back"]} Back to Dashboards',
                    callback_data='dashboard_main'))

            bot.edit_message_text(
                text=f"*Here is user details:*\n\n"
                     f"*Name:* {user['username']}\n"
                     f"*Email:* {user['email']}\n",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown')
        else:
            keyboard.add(
                types.InlineKeyboardButton(
                    f'{EMOJI["back"]} Back to Dashboards',
                    callback_data='dashboard_main'))

            bot.edit_message_text(
                text=f"*Here is user details:*\n\n"
                     f"*Name:* {user['username']}\n"
                     f"*Email:* {user['email']}\n",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown')

    elif 'remove_user_d' in call.data:
        user_id = call.data.split('_')[-1]
        d_board = call.data.split('_')[-2]
        d_board_name = call.data.split('_')[-3]

        req = handlers.remove_user_from_dashboard(d_board, user_id)
        bot.send_message(call.message.chat.id,
                         "Removing user from dashboard...")
        sleep(0.1)
        if req == 200:
            bot.send_message(call.message.chat.id,
                             "User has been removed.")
            get_dashboards(call.message)
            # sending message to deleted user
            bot.send_message(user_id, f"You have been removed from dashboard "
                                      f"{d_board_name}.")
            return
        bot.send_message(call.message.chat.id,
                         'Removing user failed. Please try again')
        get_dashboards(call.message)

    elif 'task_detailed' in call.data:
        d_board_id = call.data.split('_')[-3]
        task_id = call.data.split('_')[-1]

        task = handlers.get_task(call.message.chat.id, d_board_id, task_id)

        keyboard = types.InlineKeyboardMarkup(2)
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["user"]} Users',
                callback_data=f'task_users_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["comment"]} Comments',
                callback_data=f'task_comments_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["update"]} Update Task',
                callback_data=f'update_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["delete"]} Delete Task',
                callback_data=f'delete_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main')
        )

        bot.edit_message_text(
            text=f"*Here is your task details:*\n\n"
                 f"*Name:* {task['task_name']}\n"
                 f"*Dashboard:* {task['dashboard']}\n"
                 f"*Admin:* {task['admin_name']}\n"
                 f"*Created at:* {task['created at']}\n"
                 f"*Current status:* {task['status']}\n"
                 f"*Description:* {task['text']}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    elif 'task_users' in call.data:
        data = call.data.split('_')
        d_board_id = data[-2]
        task_id = data[-1]

        users = handlers.get_task_users(task_id)

        users_hidden = [u.get('chat_id') for u in users]
        users = [u.get('username') for u in users]

        keyboard = build_inline_keyboard(users, users_hidden,
                                         'user_detailed')
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["add"]} Add User',
                callback_data=f'add_user_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main'))
        bot.edit_message_text(text=f'*Task users:*',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard,
                              parse_mode='Markdown')

    elif 'add_user_task' in call.data:
        task_id = call.data.split('_')[-1]
        d_board_id = call.data.split('_')[-2]
        task = handlers.get_task(call.message.chat.id, d_board_id, task_id)
        locate_task_users_step(call.message, d_board_id, tasks=None, task=task)

    elif 'create_task' in call.data:
        d_board_id = call.data.split('_')[-1]
        task = {'dashboard_id': d_board_id}
        msg = bot.send_message(
            call.message.chat.id,
            'OK. Send me your task name:',
            reply_markup=build_keyboard(f'{EMOJI["back"]} Back to Main Menu'
                                        ))

        bot.register_next_step_handler(msg, process_task_name_step, task)

    elif 'update_task' in call.data:
        task_data = {'d_board_id': call.data.split('_')[-2],
                     'task_id': call.data.split('_')[-1]}
        buttons = ['Name', 'Current Status', 'Description',
                   f'{EMOJI["back"]} Back to Main Menu']
        msg = bot.send_message(call.message.chat.id,
                               'OK. Choose the details you want to update:',
                               reply_markup=build_keyboard(*buttons))
        bot.register_next_step_handler(msg, process_task_details_step,
                                       task_data, buttons)

    elif 'delete_task' in call.data:
        task_data = {'d_board_id': call.data.split('_')[-2],
                     'task_id': call.data.split('_')[-1]}
        msg = bot.send_message(call.message.chat.id,
                               'Are you sure you want to delete this task?',
                               reply_markup=build_keyboard(
                                   f'{EMOJI["yes"]} Yes',
                                   f'{EMOJI["delete"]} No')
                               )
        bot.register_next_step_handler(msg, delete_task, task_data)

    elif 'task_comments' in call.data:
        data = call.data.split('_')
        task_id = data[-1]
        d_board_id = data[-2]
        comments = handlers.get_task_all_comments(task_id)
        comments_hidden = [c.get('id') for c in comments]
        comments = [c.get('title') for c in comments]

        keyboard = build_inline_keyboard(comments, comments_hidden,
                                         'comments_detailed')
        keyboard.row_width = 2
        keyboard.add(
            types.InlineKeyboardButton(
                f'{EMOJI["comment"]} Post Comment',
                callback_data=f'post_comment_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                f'{EMOJI["back"]} Back to Dashboards',
                callback_data='dashboard_main'))
        bot.edit_message_text(text=f'*Task comments:*',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard,
                              parse_mode='Markdown')

    elif 'comments_detailed' in call.data:
        comment_id = call.data.split('_')[-1]
        comment = handlers.get_comment(comment_id)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            f'{EMOJI["back"]} Back to Dashboards',
            callback_data='dashboard_main'))

        bot.edit_message_text(
            text=f"<b>Here is comment details:</b>\n\n"
                 f"<b>Task</b>: {comment['task']}\n"
                 f"<b>Title:</b> {comment['title']}\n"
                 f"<b>Author:</b> {comment['sender']}\n"
                 f"<b>Created at</b>: {comment['created_at']}\n"
                 f"<b>Comment:</b> {comment['comment']}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML')

    elif 'post_comment' in call.data:
        data = call.data.split('_')
        comment_data = {'d_board_id': data[-2], 'task_id': data[-1]}

        msg = bot.send_message(
            call.message.chat.id,
            'OK. Send me a comment title:',
            reply_markup=build_keyboard(f'{EMOJI["back"]} Back to Main Menu'))

        bot.register_next_step_handler(msg, initiate_posting_comment,
                                       comment_data)

    elif 'update_user' in call.data:
        data = call.data.split('_')[-1]

        if data == 'username':
            msg = bot.send_message(call.message.chat.id,
                                   "OK. Send me a new name:")
            bot.register_next_step_handler(msg, update_user, data)
        if data == 'email':
            msg = bot.send_message(call.message.chat.id,
                                   "OK. Send me a new email:")
            bot.register_next_step_handler(msg, update_user, data)

    elif 'delete_account' in call.data:
        chat_id = call.data.split('_')[-1]
        msg = bot.send_message(call.message.chat.id,
                               f'Are you sure you want to delete account?',
                               reply_markup=build_keyboard(
                                   f'{EMOJI["yes"]} Yes',
                                   f'{EMOJI["delete"]} No')
                               )
        bot.register_next_step_handler(msg, delete_account, chat_id)


def command_checker(message):
    """Checks if user presses a menu button inside any next_step loop
    and calls function the button corresponds to"""

    commands = {
        f'{EMOJI["main"]} Main Menu': main_menu,
        f'{EMOJI["dashboard"]} Dashboards': get_dashboards,
        f'{EMOJI["task"]} My Tasks': get_tasks,
        f'{EMOJI["comment"]} My Comments': get_user_comments,
        f'{EMOJI["back"]} Back to Main Menu': main_menu
    }

    commands[message.text](message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def unknown(message):
    """Under construction. Should be below all the functions"""
    bot.send_message(message.chat.id,
                     "Sorry, I didn't understand that command.")


if __name__ == '__main__':
    bot.polling(none_stop=True)
