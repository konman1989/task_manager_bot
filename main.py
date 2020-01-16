# import logging
# import telebot
import requests
from telebot import TeleBot
import templates.users

# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)

bot = TeleBot('926931469:AAH7VzaTMd-2wJ_AQClwyA9o42kXcC2r0Ck')


# TODO identify user by id (another row in db?)
# TODO adding pieces of text in one message
# TODO try/except clauses

# USERS
@bot.message_handler(commands=['start', 'help'])
def send_options(message):
    bot.send_message(message.chat.id, '/options to be added')
    # print(message.text)


@bot.message_handler(commands=['users'])
def get_users(message):
    req = requests.get('http://127.0.0.1:5000/users')
    bot.send_message(message.chat.id, req.text)


@bot.message_handler(commands=['user'])
def get_user(message):
    id_ = message.text.split(' ')[1]
    req = requests.get(f'http://127.0.0.1:5000/users/{id_}')
    bot.send_message(message.chat.id, req.text)


@bot.message_handler(commands=['user_add'])
def add_user(message):
    user = message.text.split(' ')

    if len(user) > 3:
        bot.send_message(message,
                         'Information is incorrect. Please enter username'
                         ' and email')
        return

    req = requests.post('http://127.0.0.1:5000/users',
                        json={'username': user[1], 'email': user[2]})

    if req.status_code == 201:
        bot.send_message(message.chat.id,
                         f"User {user[1]} has been added to the DB")
        return
    bot.send_message(message.chat.id,
                     f"Adding user failed with status code: {req.status_code}, "
                     f"message: {req.text}")


@bot.message_handler(commands=['user_update'])
def update_user(message):
    """Needs updating. Only works if id, username and email were provided in
    proper order"""

    user = message.text.split(' ')
    req = requests.patch(f'http://127.0.0.1:5000/users/{user[1]}',
                         json={'username': user[2], 'email': user[3]})

    if req.status_code == 204:
        bot.send_message(message.chat.id,
                         f"User {user[1]} has been updated")
        return
    bot.send_message(message.chat.id,
                     f"Updating user failed with status code: {req.status_code},"
                     f" message: {req.text}")


@bot.message_handler(commands=['user_delete'])
def delete_user(message):
    id_ = message.text.split(' ')[1]
    req = requests.delete(f'http://127.0.0.1:5000/users/{id_}')

    if req.status_code == 200:
        bot.send_message(message.chat.id,
                         f"User {id_} has been deleted")
        return
    bot.send_message(message.chat.id,
                     f"Deleting user failed with status code: {req.status_code},"
                     f" message: {req.text}")


@bot.message_handler(commands=['user_list'])
def user_stats(message):
    user = message.text.split(' ')
    req = requests.get(
        f'http://127.0.0.1:5000/users/{user[1]}/data?query={user[2]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return

    bot.send_message(message.chat.id,
                     f"Querying for {user[2]} has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


# -------------------------------------------------------------------------
# DASHBOARDS

@bot.message_handler(commands=['dashboards'])
def get_dashboards(message):
    req = requests.get('http://127.0.0.1:5000/dashboards')
    bot.send_message(message.chat.id, req.text)


@bot.message_handler(commands=['dashboard'])
def get_dashboard(message):
    id_ = message.text.split(' ')[1]
    req = requests.get(f'http://127.0.0.1:5000/dashboards/{id_}')
    bot.send_message(message.chat.id, req.text)


@bot.message_handler(commands=['dashboard_add'])
def add_dashboard(message):
    d = message.text.split(' ')

    if len(d) > 3:
        bot.send_message(message, 'Information is incorrect. Please enter your'
                                  ' dashboard name')
        return

    req = requests.post(f'http://127.0.0.1:5000/users/{d[1]}/dashboards',
                        json={'dashboard_name': f'{d[2]}'})

    if req.status_code == 201:
        bot.send_message(message.chat.id,
                         f"Dashboard {d[2]} has been created")
        return
    bot.send_message(message.chat.id,
                     f"Creating dashboard failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['dashboard_add_user'])
def add_user_to_dashboard(message):
    """Dashboard admin, dashboard, team member"""
    d = message.text.split(' ')

    if len(d) > 4:
        bot.send_message(message,
                         "Information is incorrect. Please enter user's"
                         " and dashboard id")
        return

    req = requests.post(
        f'http://127.0.0.1:5000/users/{d[1]}/dashboards/{d[2]}',
        json={'team': f'{d[3]}'})

    if req.status_code == 201:
        bot.send_message(message.chat.id,
                         f"User {d[3]} has been added to dashboard {d[2]}")
        return
    bot.send_message(message.chat.id,
                     f"Adding user to the dashboard failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['dashboard_list'])
def get_dashboards(message):
    d = message.text.split(' ')
    req = requests.get(f'http://127.0.0.1:5000/dashboards/{d[1]}/{d[2]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return
    bot.send_message(message.chat.id,
                     f"Querying for {d[2]} has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['dashboard_update'])
def update_dashboard(message):
    """Needs updating. Only works if user's, dashboard id and dashboard name
    were provided in proper order"""

    d = message.text.split(' ')
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{d[1]}/dashboards/{d[2]}',
        json={'dashboard_name': d[3]})

    if req.status_code == 204:
        bot.send_message(message.chat.id,
                         f"Dashboard {d[2]} has been updated")
        return
    bot.send_message(message.chat.id,
                     f"Updating dashboard failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['dashboard_delete'])
def delete_dashboard(message):
    d = message.text.split(' ')
    req = requests.delete(
        f'http://127.0.0.1:5000/users/{d[1]}/dashboards/{d[2]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id,
                         f"Dashboard {d[2]} has been deleted")
        return
    bot.send_message(message.chat.id,
                     f"Deleting dashboard failed with "
                     f"status code: {req.status_code}, message: {req.text}")


@bot.message_handler(commands=['dashboard_tasks_status'])
def dashboard_tasks_status(message):
    d = message.text.split(' ')
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d[1]}/tasks?status={d[2]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return

    bot.send_message(message.chat.id,
                     f"Querying for {d[2]} has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


# -------------------------------------------------------------------------
# TASKS


@bot.message_handler(commands=['task_list'])
def get_task_users_comments(message):
    task = message.text.split(' ')
    req = requests.get(f'http://127.0.0.1:5000/tasks/{task[1]}/{task[2]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return

    bot.send_message(message.chat.id,
                     f"Querying for {task[2]} has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['task_add'])
def add_task(message):
    d = message.text.split(' ')
    req = requests.post(
        f'http://127.0.0.1:5000/users/{d[1]}/dashboards/{d[2]}/tasks',
        json={'task_name': f'{d[3]}',
              'text': f'{d[4]}'}
    )

    if req.status_code == 201:
        bot.send_message(message.chat.id,
                         f"Task {d[3]} has been created")
        return
    bot.send_message(message.chat.id,
                     f"Creating task failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['task'])
def get_task(message):
    t = message.text.split(' ')
    req = requests.get(
        f'http://127.0.0.1:5000/users/{t[1]}/dashboards/{t[2]}/tasks/{t[3]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return

    bot.send_message(message.chat.id,
                     f"Querying for {t[3]} has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['task_add_user'])
def add_user_to_task(message):
    """User, dashboard, task, team member"""
    t = message.text.split(' ')

    req = requests.post(
        f'http://127.0.0.1:5000/users/{t[1]}/dashboards/{t[2]}/tasks/{t[3]}',
        json={'team': f'{t[4]}'})

    if req.status_code == 201:
        bot.send_message(message.chat.id,
                         f"User {t[4]} has been added to task {t[2]}")
        return
    bot.send_message(message.chat.id,
                     f"Adding user to the task failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['task_update'])
def update_task(message):
    """Needs updating. Only works if user's, task id and task name
    were provided in proper order. Works for updating status only"""

    t = message.text.split(' ')
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{t[1]}/dashboards/{t[2]}/tasks/{t[3]}',
        json={'status': f'{t[4]}'})

    if req.status_code == 204:
        bot.send_message(message.chat.id,
                         f"Task {t[3]} has been updated")
        return
    bot.send_message(message.chat.id,
                     f"Updating task failed with status code: "
                     f"{req.status_code}, message: {req.text}")

    """
    Rest api does not have this method. Consider move tasks to archive

@bot.message_handler(commands=['task_delete'])
def delete_task(message):

    t = message.text.split(' ')
    req = requests.delete(
        f'http://127.0.0.1:5000/users/{t[1]}/dashboards/{t[2]}/tasks/{t[3]}')

    if req.status_code == 200:
        bot.send_message(message.chat.id,
                         f"Task {t[3]} has been deleted")
        return
    bot.send_message(message.chat.id,
                     f"Deleting task failed with "
                     f"status code: {req.status_code}, message: {req.text}")

        """


# -------------------------------------------------------------------------
# COMMENTS


@bot.message_handler(commands=['comment_add'])
def add_comment(message):
    c = message.text.split(' ')
    req = requests.post(
        f'http://127.0.0.1:5000/users/{c[1]}/dashboards/{c[2]}/tasks/{c[3]}/comments',
        json={'text': f'{c[4]}'}
    )

    if req.status_code == 200:
        bot.send_message(message.chat.id,
                         f"Comment has been added to task {c[3]}")
        return
    bot.send_message(message.chat.id,
                     f"Commenting task failed with status code: "
                     f"{req.status_code}, message: {req.text}")


@bot.message_handler(commands=['comments_list'])
def get_task_comments(message):
    c = message.text.split(' ')
    req = requests.get(
        f'http://127.0.0.1:5000/users/{c[1]}/dashboards/{c[2]}/tasks/{c[3]}/comments')

    if req.status_code == 200:
        bot.send_message(message.chat.id, req.text)
        return

    bot.send_message(message.chat.id,
                     f"Querying for comments to has failed with status code: "
                     f"{req.status_code}, message: {req.text}")


if __name__ == '__main__':
    bot.polling()
