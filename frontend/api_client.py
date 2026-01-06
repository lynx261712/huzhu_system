import requests
import os

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
API_BASE_URL = "http://127.0.0.1:5000/api"

class APIClient:
    @staticmethod
    def login(username, password):
        return requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})

    @staticmethod
    def register(username, password, contact):
        return requests.post(f"{API_BASE_URL}/register", json={"username": username, "password": password, "contact": contact})

    @staticmethod
    def get_skills(keyword=None):
        return requests.get(f"{API_BASE_URL}/skills", params={"q": keyword})

    @staticmethod
    def get_lost_items(item_type=None, keyword=None, location=None):
        params = {}
        if keyword: params['keyword'] = keyword
        if location: params['location'] = location
        if item_type is not None: params['type'] = item_type
        return requests.get(f"{API_BASE_URL}/lost-items", params=params)

    @staticmethod
    def post_item(endpoint, form_data, file_path=None):
        url = f"{API_BASE_URL}/{endpoint}"
        print(f"DEBUG: 正在向 {url} 发送数据, 是否有文件: {bool(file_path)}")
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    files = {'image': (os.path.basename(file_path), f)}
                    return requests.post(url, data=form_data, files=files)
            except Exception as e:
                print(f"File upload error: {e}")
                return requests.post(url, data=form_data)
        else:
            return requests.post(url, data=form_data)

    @staticmethod
    def get_user_info(user_id):
        return requests.get(f"{API_BASE_URL}/user/{user_id}")

    @staticmethod
    def get_user_posts(user_id):
        return requests.get(f"{API_BASE_URL}/user/posts/{user_id}")

    @staticmethod
    def update_user(user_id, username=None, contact=None, avatar_path=None):
        url = f"{API_BASE_URL}/user/update"

        form_data = {"user_id": str(user_id)}
        if username: form_data['username'] = username
        if contact: form_data['contact'] = contact

        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, 'rb') as f:
                files = {'avatar': (os.path.basename(avatar_path), f)}
                return requests.post(url, data=form_data, files=files)
        else:
            return requests.post(url, data=form_data)

    @staticmethod
    def delete_item(item_id, category):
        return requests.post(f"{API_BASE_URL}/delete", json={"id": item_id, "category": category})

    @staticmethod
    def interact(item_id, category):
        return requests.post(f"{API_BASE_URL}/interact", json={"item_id": item_id, "category": category})

    @staticmethod
    def accept_order(item_id, category, user_id):
        return requests.post(f"{API_BASE_URL}/order/accept", json={"id": item_id, "category": category, "user_id": user_id})

    @staticmethod
    def finish_order(item_id, category):
        return requests.post(f"{API_BASE_URL}/order/finish", json={"id": item_id, "category": category})

    @staticmethod
    def review_order(item_id, category, action, current_user_id):
        return requests.post(f"{API_BASE_URL}/order/review", json={
            "id": item_id,
            "category": category,
            "action": action,
            "current_user_id": current_user_id
        })

    @staticmethod
    def get_my_helps(user_id):
        return requests.get(f"{API_BASE_URL}/user/helps/{user_id}")


    @staticmethod
    def get_messages(user_id, partner_id):
        return requests.get(f"{API_BASE_URL}/messages", params={"user_id": user_id, "partner_id": partner_id})


    @staticmethod
    def send_message(sender_id, receiver_id, content=None, image_path=None):
        url = f"{API_BASE_URL}/messages"
        form_data = {"sender_id": str(sender_id), "receiver_id": str(receiver_id)}

        if content:
            form_data['content'] = content

        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f)}
                return requests.post(url, data=form_data, files=files)
        else:
            return requests.post(url, data=form_data)

    @staticmethod
    def get_tags():
        return requests.get(f"{API_BASE_URL}/tags")


    @staticmethod
    def start_inquiry(task_id, task_type, visitor_id):
        """点击详情页联系时调用，创建会话"""
        url = f"{API_BASE_URL}/chat/start"
        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "visitor_id": visitor_id
        }
        return requests.post(url, json=payload)

    @staticmethod
    def get_task_inquiries(task_id, task_type):
        """点击发布管理卡片的咨询按钮时调用，获取咨询人列表"""
        url = f"{API_BASE_URL}/task/inquiries"
        params = {
            "task_id": task_id,
            "task_type": task_type
        }
        return requests.get(url, params=params)

    @staticmethod
    def get_inquiry_counts(user_id):
        """加载我的发布列表时调用，获取每个任务有多少人咨询"""
        url = f"{API_BASE_URL}/user/task_inquiry_counts"
        return requests.get(url, params={"user_id": user_id})