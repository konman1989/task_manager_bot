import requests


def get_user_dashboards(chat_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards')
    return req.json()


def get_dashboard(chat_id, d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/users/{chat_id}/dashboards/{d_id}')
    return req.json()


def get_dashboard_users(chat_id, d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d_id}/users')
    return req.json()


def get_dashboard_tasks(chat_id, d_id):
    req = requests.get(
        f'http://127.0.0.1:5000/dashboards/{d_id}/tasks')
    return req.json()


def get_user(user_id):
    req = requests.get(f'http://127.0.0.1:5000/users/{user_id}')
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


def get_comment(comment_id):
    req = requests.get(f'http://127.0.0.1:5000/comments/{comment_id}')
    return req.json()


def get_user_stats(chat_id, query_parameter):
    req = requests.get(f'http://127.0.0.1:5000/users/{chat_id}'
                       f'/data?query={query_parameter}')
    return req.json()


