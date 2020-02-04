# import logging
import re
import requests
from time import sleep
from telebot import TeleBot, types

import handlers
from utils import build_keyboard, build_inline_keyboard, check_command

# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)

bot = TeleBot('926931469:AAH7VzaTMd-2wJ_AQClwyA9o42kXcC2r0Ck')

# TODO try/except clauses
#
#
COMMANDS = ['Main Menu', 'Dashboards', 'My Tasks', 'My Comments',
            '<< Back to Main Menu']


def command_checker(message):
    """Check if user presses a menu button inside any next_step loop
    and calls function the button corresponds to"""

    commands = {'Main Menu': main_menu,
                'Dashboards': get_dashboards,
                'My Tasks': get_tasks,
                'My Comments': get_user_comments,
                '<< Back to Main Menu': main_menu
                }

    commands[message.text](message)


@bot.message_handler(commands=['start', 'help'])
def send_options(message):
    text = 'Welcome to Task Manager Bot. You can create a new dashboard or ' \
           'join existing one. Inside dashboard you can create tasks, ' \
           'add users and comments. To proceed you need to create an ' \
           'account below:'

    bot.send_message(message.chat.id, text,
                     reply_markup=build_keyboard('Create Account'))


@bot.message_handler(func=lambda x: x.text == 'Create Account')
def create_account(message):
    msg = bot.send_message(message.chat.id, 'OK. Send me your name:',
                           reply_markup=build_keyboard('<< Back to Main Menu'))

    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    if message.text == '<< Back to Main Menu':
        bot.send_message(message.chat.id, 'OK. Tell me when you are ready.',
                         reply_markup=build_keyboard('Create Account'))
        return
    user = {'username': message.text, 'chat_id': message.chat.id, }
    msg = bot.send_message(message.chat.id, f'Thank you, {user["username"]}.'
                                            f' Send me your email:')

    bot.register_next_step_handler(msg, process_email_step, user)


def process_email_step(message, user):
    if message.text == '<< Back to Main Menu':
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

    user['email'] = message.text
    bot.send_message(message.chat.id,
                     'Thank you, creating your account...')
    create_user(message, user)


def create_user(message, user):
    req = requests.post('http://127.0.0.1:5000/users',
                        json=user)
    sleep(1.0)
    if req.status_code == 201:
        bot.send_message(
            message.chat.id,
            "Your account has been created. You can create a new dashboard or "
            "join existing one.",
            reply_markup=build_keyboard('Create Dashboard', 'Join Dashboard')
        )
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed with status code: {req.status_code},"
                     f" message: {req.text}")


@bot.message_handler(func=lambda x: x.text == 'Dashboards')
def get_dashboards(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    d_board = [d.get('name') for d in dashboards]
    d_board_hidden = [d.get('id') for d in dashboards]

    keyboard = build_inline_keyboard(d_board, d_board_hidden,
                                     'dashboard_detailed')

    keyboard.add(
        types.InlineKeyboardButton('Create Dashboard',
                                   callback_data='create_dashboard'),
        types.InlineKeyboardButton('<< Back to Main Menu',
                                   callback_data='main'))
    bot.send_message(message.chat.id, 'Getting your dashboards...',
                     reply_markup=build_keyboard('Create Dashboard',
                                                 'Create Task',
                                                 'Add User to Dashboard',
                                                 'Main Menu'))
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
    if message.text == 'Yes':
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


@bot.message_handler(func=lambda x: x.text == 'Create Dashboard')
def initiate_dashboard_creation(message):
    msg = bot.send_message(message.chat.id, 'OK. Send me your dashboard name:',
                           reply_markup=build_keyboard('<< Back to Main Menu'))

    bot.register_next_step_handler(msg, process_dashboard_name_step)


def process_dashboard_name_step(message):
    if message.text == '<< Back to Main Menu':
        bot.send_message(message.chat.id, 'OK. Tell me when you are ready.',
                         reply_markup=build_keyboard('Create Dashboard',
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


def create_dashboard(message, d):
    req = requests.post(
        f'http://127.0.0.1:5000/users/{message.chat.id}/dashboards', json=d)

    sleep(1.0)
    if req.status_code == 201:
        bot.send_message(
            message.chat.id,
            f"Dashboard {d['dashboard_name']} has been created. You can "
            f"create a new task or add users to your dashboard now.",
            reply_markup=build_keyboard(
                'Create Task', 'Add User', 'Dashboards',
                '<< Back to Main Menu'))
        return
    bot.send_message(message.chat.id,
                     f"Creating dashboard failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(func=lambda x: x.text == 'Add User to Dashboard')
def initiate_adding_user(message):
    dashboards = handlers.get_user_dashboards_as_admin(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the dashboard to add new user to:",
                           reply_markup=build_keyboard(*user_dashboards,
                                                       '<< Back to Main Menu'))

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
                           reply_markup=build_keyboard('<< Back to Main Menu'))

    bot.register_next_step_handler(msg, process_user_email_step, d_id[0])


def process_user_email_step(message, dashboard):
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
            f"Please try again:",
            reply_markup=build_keyboard('<< Back to Main Menu'))
        bot.register_next_step_handler(msg, process_user_email_step, dashboard)
        return
    bot.send_message(message.chat.id,
                     'OK. User found. Adding user to dashboard...')
    add_user_to_dashboard(message, user['chat_id'], dashboard)


def add_user_to_dashboard(message, user_id, dashboard):
    req = handlers.add_user_to_dashboard(message.chat.id, user_id, dashboard)
    sleep(1.0)
    if req == 201:
        bot.send_message(message.chat.id, "User has been added.",
                         reply_markup=build_keyboard('<< Back to Main Menu'))
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed with status code. Please try again")


@bot.message_handler(func=lambda x: x.text == 'My Tasks')
def get_tasks(message):
    """TODO add dashboard id to task_detailed"""
    tasks = handlers.get_user_stats(message.chat.id, 'tasks')
    tasks_hidden = ['_'.join([str(t.get('id')), str(t.get('task_name')),
                              str(t.get('dashboard_id'))])
                    for t in tasks]
    tasks = [t.get('task_name') for t in tasks]

    keyboard = build_inline_keyboard(tasks, tasks_hidden,
                                     f'task_detailed')

    keyboard.add(types.InlineKeyboardButton('<< Back to Main Menu',
                                            callback_data='main'))
    bot.send_message(message.chat.id, 'Getting your tasks...',
                     reply_markup=build_keyboard('Create Task',
                                                 'Add User to Task',
                                                 'Post Comment',
                                                 'Main Menu', ))
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
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{message.chat.id}/'
        f'dashboards/{task_data["d_board_id"]}/tasks/{task_data["task_id"]}',
        json={task_data['update_instance']: message.text})
    sleep(1.0)
    if req.status_code == 204:
        bot.send_message(message.chat.id,
                         f"Task has been successfully updated")
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Updating task was unsuccessful. Please try again.")
    main_menu(message)


def delete_task(message, d_id):
    if message.text == 'Yes':
        req = handlers.delete_dashboard(message.chat.id, d_id)
        if req == 200:
            bot.send_message(message.chat.id, 'Dashboard has been deleted.')
            main_menu(message)
            return
        bot.send_message(message.chat.id,
                         'Deleting dashboard was unsuccessful. '
                         'Please try again')

        main_menu(message)
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
                          '<< Back to Main Menu']
        msg = bot.send_message(message.chat.id, 'OK. Send me a new status:',
                               reply_markup=build_keyboard(*status_buttons))
        task_data['update_instance'] = 'status'
        bot.register_next_step_handler(msg, update_task, task_data,
                                       status_buttons)


@bot.message_handler(func=lambda x: x.text == 'Create Task')
def initiate_task_creation(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           'OK. Choose dashboard new task will belong to:',
                           reply_markup=build_keyboard(*user_dashboards,
                                                       '<< Back to Main Menu'))

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
                           reply_markup=build_keyboard('<< Back to Main Menu'))
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
                           reply_markup=build_keyboard('<< Back to Main Menu'))
    bot.register_next_step_handler(msg, process_task_description_step, task)


def process_task_description_step(message, task):
    if message.text in COMMANDS:
        command_checker(message)
        return
    task['text'] = message.text
    bot.send_message(message.chat.id, 'OK. Creating your task...')
    create_task(message, task)


def create_task(message, task):
    req = requests.post(
        f"http://127.0.0.1:5000/users/{message.chat.id}/dashboards/"
        f"{task['dashboard_id']}/tasks", json={'task_name': task['task_name'],
                                               'text': task['text']})
    sleep(1.0)
    if req.status_code == 201:
        bot.send_message(
            message.chat.id,
            f"Task {task['task_name']} has been created. You can "
            f"change task status, add comments or users to your task.",
            reply_markup=build_keyboard(
                '<< Back to Main Menu'))
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Creating task failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(func=lambda x: x.text == 'Add User to Task')
def initiate_adding_user_to_task(message):
    dashboards = handlers.get_user_dashboards(message.chat.id)
    user_dashboards = [d.get('name') for d in dashboards]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the dashboard first:",
                           reply_markup=build_keyboard(*user_dashboards,
                                                       '<< Back to Main Menu'))

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
    dashboard_tasks = handlers.get_dashboard_tasks(message.chat.id, d_id[0])
    tasks = [t.get('task_name') for t in dashboard_tasks]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the task to add user to:",
                           reply_markup=build_keyboard(*tasks,
                                                       '<< Back to Main Menu'))

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
    dashboard_users = handlers.get_dashboard_users(message.chat.id, d_id)
    users = [u.get('username') for u in dashboard_users]
    msg = bot.send_message(message.chat.id,
                           "OK. Send me a user to add to task:",
                           reply_markup=build_keyboard(*users,
                                                       '<< Back to Main Menu'))
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
                         reply_markup=build_keyboard('<< Back to Main Menu'))
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed with status code. Please try again")


@bot.message_handler(func=lambda x: x.text == 'Post Comment')
def initiate_posting_comment(message, comment_data):
    if message.text in COMMANDS:
        command_checker(message)
        return

    comment_data['title'] = message.text
    msg = bot.send_message(message.chat.id,
                           "OK. Send me the comment text:",
                           reply_markup=build_keyboard('<< Back to Main Menu'))

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
                             '<< Back to Main Menu'))
        main_menu(message)
        return
    bot.send_message(message.chat.id,
                     f"Posting comment was unsuccessful. Please try again.")


@bot.message_handler(func=lambda x: x.text == 'My Comments')
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
    func=lambda x: x.text == 'Main Menu' or x.text == '<< Back to Main Menu')
def main_menu(message):
    bot.send_message(message.chat.id,
                     "You can navigate following sections:\n"
                     " - Dashboards\n"
                     " - Tasks\n"
                     " - Users\n"
                     " - Your account",
                     reply_markup=build_keyboard('Dashboards',
                                                 'My Tasks',
                                                 'My Comments',
                                                 'My Account'))


@bot.callback_query_handler(func=lambda call: True)
def process_callback_requests(call):

    """Try changing message.chat.id to call.chat.id"""
    if call.data == 'main':
        main_menu(call.message)

    elif call.data == 'Create Dashboard' or 'create_dashboard' in call.data:
        initiate_dashboard_creation(call.message)

    elif 'update_dashboard' in call.data:
        d_board = call.data.split('_')
        msg = bot.send_message(call.message.chat.id,
                               f'OK. Give me a new name for dashboard'
                               f' {d_board[-2]}:',
                               reply_markup=build_keyboard(
                                   '<< Back to Main Menu'))
        bot.register_next_step_handler(msg, update_dashboard,
                                       call.message.chat.id, d_board[-1])

    elif 'delete_dashboard' in call.data:
        d_board = call.data.split('_')
        msg = bot.send_message(call.message.chat.id,
                               f'Are you sure you want to delete dashboard'
                               f' {d_board[-2]}?',
                               reply_markup=build_keyboard('Yes', 'No'))
        bot.register_next_step_handler(msg, delete_dashboard,
                                       call.message.chat.id, d_board[-1])

    elif call.data == 'dashboard_main':
        dashboards = handlers.get_user_dashboards(call.message.chat.id)
        d_board = [d.get('name') for d in dashboards]
        d_board_hidden = [d.get('id') for d in dashboards]

        keyboard = build_inline_keyboard(d_board, d_board_hidden,
                                         'dashboard_detailed')

        keyboard.add(
            types.InlineKeyboardButton('Create Dashboard',
                                       callback_data='create_dashboard'),
            types.InlineKeyboardButton('<< Back to Main Menu',
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
            'Dashboard Tasks',
            callback_data=f'dashboard_tasks_{d_board_id}'),
            types.InlineKeyboardButton(
                'Dashboard Users',
                callback_data=f'dashboard_users_{d_board_id}')
        )
        keyboard.add(types.InlineKeyboardButton(
            'Update Dashboard Name',
            callback_data=f'update_dashboard_{d_board_name}_{d_board_id}'),
            types.InlineKeyboardButton(
                'Delete Dashboard',
                callback_data=f'delete_dashboard_{d_board_name}_{d_board_id}')
        )
        keyboard.add(types.InlineKeyboardButton(
                '<< Back to Dashboards', callback_data='dashboard_main'))
        bot.edit_message_text(text=f'{d_board_name}\ntasks and users:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif 'dashboard_users' in call.data:
        d_board_id = call.data.split('_')[-1]

        users = handlers.get_dashboard_users(call.message.chat.id,
                                             d_board_id)
        users_hidden = [u.get('chat_id') for u in users]
        users = [u.get('username') for u in users]

        keyboard = build_inline_keyboard(users, users_hidden,
                                         'user_detailed')
        keyboard.add(
            types.InlineKeyboardButton(
                'Add User',
                callback_data=f'add_user_dashboard_{d_board_id}'),
            types.InlineKeyboardButton(
                '<< Back to Dashboards', callback_data='dashboard_main')
        )
        bot.edit_message_text(text=f'Dashboard users:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif 'add_user_dashboard' in call.data:
        d_board_id = call.data[-1]

        msg = bot.send_message(call.message.chat.id,
                               "OK. Send me user's email:",
                               reply_markup=build_keyboard(
                                   '<< Back to Main Menu'))

        bot.register_next_step_handler(msg, process_user_email_step,
                                       d_board_id)

    elif 'dashboard_tasks' in call.data:
        d_board_id = call.data.split('_')[-1]

        tasks = handlers.get_dashboard_tasks(call.message.chat.id,
                                             d_board_id)
        task = [t.get('task_name') for t in tasks]
        task_hidden = [t.get('id') for t in tasks]

        keyboard = build_inline_keyboard(task, task_hidden,
                                         f'task_detailed_{d_board_id}')
        keyboard.add(
            types.InlineKeyboardButton(
                'Create Task',
                callback_data=f'create_task_{d_board_id}'),
            types.InlineKeyboardButton(
                '<< Back to Dashboards',
                callback_data='dashboard_main'))

        bot.edit_message_text(text=f'Dashboard tasks:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif 'user_detailed' in call.data:
        user = call.data.split('_')[-1]
        user = handlers.get_user(user)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            '<< Back to Dashboards',
            callback_data='dashboard_main'))

        bot.edit_message_text(
            text=f"*Here is user details:*\n\n"
                 f"*Name:* {user['username']}\n"
                 f"*Email:* {user['email']}\n",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown')

    elif 'task_detailed' in call.data:
        d_board_id = call.data.split('_')[-3]
        task_id = call.data.split('_')[-1]

        task = handlers.get_task(call.message.chat.id, d_board_id, task_id)

        keyboard = types.InlineKeyboardMarkup(2)
        keyboard.add(
            types.InlineKeyboardButton(
                'Task Users',
                callback_data=f'task_users_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                'Task Comments',
                callback_data=f'task_comments_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                'Update Task',
                callback_data=f'update_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                'Delete Task',
                callback_data=f'delete_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                '<< Back to Dashboard',
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
                'Add User',
                callback_data=f'add_user_task_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                '<< Back to Dashboards',
                callback_data='dashboard_main'))
        bot.edit_message_text(text=f'Task users:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

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
            reply_markup=build_keyboard('<< Back to Main Menu'))

        bot.register_next_step_handler(msg, process_task_name_step, task)

    elif 'update_task' in call.data:
        task_data = {'d_board_id': call.data.split('_')[-2],
                     'task_id': call.data.split('_')[-1]}
        buttons = ['Name', 'Current Status', 'Description',
                   '<< Back to Main Menu']
        msg = bot.send_message(call.message.chat.id,
                               'OK. Choose the details you want to update:',
                               reply_markup=build_keyboard(*buttons))
        bot.register_next_step_handler(msg, process_task_details_step,
                                       task_data, buttons)

    elif 'delete_task' in call.data:

        """TODO ARCHIVE?"""
        task_data = {'d_board_id': call.data.split('_')[-2],
                     'task_id': call.data.split('_')[-1]}
        buttons = ['Name', 'Current Status', 'Description',
                   '<< Back to Main Menu']
        msg = bot.send_message(call.message.chat.id,
                               'OK. Choose the details you want to update:',
                               reply_markup=build_keyboard(*buttons))
        bot.register_next_step_handler(msg, process_task_details_step,
                                       task_data, buttons)

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
                'Post Comment',
                callback_data=f'post_comment_{d_board_id}_{task_id}'),
            types.InlineKeyboardButton(
                '<< Back to Dashboards',
                callback_data='dashboard_main'))
        bot.edit_message_text(text=f'Task comments:',
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif 'comments_detailed' in call.data:
        comment_id = call.data.split('_')[-1]
        comment = handlers.get_comment(comment_id)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            '<< Back to Dashboards',
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
            reply_markup=build_keyboard('<< Back to Main Menu'))

        bot.register_next_step_handler(msg, initiate_posting_comment,
                                       comment_data)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def unknown(message):
    """Under construction. Should be below all the functions"""
    bot.send_message(message.chat.id,
                     "Sorry, I didn't understand that command.")


if __name__ == '__main__':
    bot.polling(none_stop=True)
