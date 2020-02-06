import requests


def create_user(user):
    req = requests.post('http://127.0.0.1:5000/users',
                        json=user)
    return req.status_code


def get_user(user_id):
    req = requests.get(f'http://127.0.0.1:5000/users/{user_id}')
    return req.json()


def get_user_dashboards(chat_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/data?query=dashboards')
    return req.json()


def get_user_stats(chat_id, query_parameter):
    req = requests.get(f'http://127.0.0.1:5000/users/{chat_id}'
                       f'/data?query={query_parameter}')
    return req.json()


def get_user_by_email(query_parameter):
    req = requests.get(f'http://127.0.0.1:5000/users?email={query_parameter}')
    return req.json()


def get_user_dashboards_as_admin(chat_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards')
    return req.json()


def update_user(chat_id, data):
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{chat_id}',
        json=data
    )
    return req.status_code


def delete_user(chat_id):
    req = requests.delete(
        f'http://127.0.0.1:5000/users/{chat_id}',
    )
    return req.status_code


def create_dashboard(chat_id, data):
    req = requests.post(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards', json=data)
    return req.status_code


def get_dashboard(chat_id, d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards/{d_id}')
    return req.json()


def get_dashboard_users(d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d_id}/users')
    return req.json()


def get_dashboard_tasks(d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d_id}/tasks')
    return req.json()


def get_dashboard_stats(d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d_id}/data')
    return req.json()


def delete_dashboard(chat_id, d_id):
    req = requests.delete(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards/{d_id}')
    return req.status_code


def update_dashboard(chat_id, d_id, d_name):
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards/{d_id}',
        json={'dashboard_name': d_name})
    return req.status_code


def add_user_to_dashboard(admin_id, user, d_board_id):
    req = requests.post(
        f'http://127.0.0.1:5000/users/{admin_id}/dashboards/{d_board_id}',
        json={"team": user})
    return req.status_code


def create_task(chat_id, task):
    req = requests.post(
        f"http://127.0.0.1:5000/users/{chat_id}/dashboards/"
        f"{task['dashboard_id']}/tasks", json={'task_name': task['task_name'],
                                               'text': task['text']})
    return req.status_code


def get_task(chat_id, d_id, t_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards/{d_id}/tasks/{t_id}')
    return req.json()


def get_task_users(t_id):
    req = requests.get(
        f'http://127.0.0.1:5000/tasks/{t_id}/users')
    return req.json()


def get_task_all_comments(task_id):
    req = requests.get(f'http://127.0.0.1:5000/tasks/{task_id}/comments')
    return req.json()


def add_user_to_task(initiator_id, user_id, dashboard_id, task_id):
    req = requests.post(
        f'http://127.0.0.1:5000/users/{initiator_id}/dashboards'
        f'/{dashboard_id}/tasks/{task_id}', json={"team": user_id})
    return req.status_code


def update_task(chat_id, task_data, text):
    req = requests.patch(
        f'http://127.0.0.1:5000/users/{chat_id}/'
        f'dashboards/{task_data["d_board_id"]}/tasks/{task_data["task_id"]}',
        json={task_data['update_instance']: text})

    return req.status_code


def delete_task(chat_id, task_data):
    req = requests.delete(
        f'http://127.0.0.1:5000/users/{chat_id}/'
        f'dashboards/{task_data["d_board_id"]}/tasks/{task_data["task_id"]}')
    return req.status_code


def get_comment(comment_id):
    req = requests.get(f'http://127.0.0.1:5000/comments/{comment_id}')
    return req.json()


def post_comment(comment_data):
    req = requests.post(
        f'http://127.0.0.1:5000/users/{comment_data["chat_id"]}/dashboards'
        f'/{comment_data["d_board_id"]}/tasks/{comment_data["task_id"]}/comments',
        json={'title': comment_data['title'],
              'text': comment_data['text']})
    return req.status_code


def get_user_comments(chat_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/data?query=comments')
    return req.json()



