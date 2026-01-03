import flet as ft
from api_client import APIClient
import time
import threading


def ChatView(current_user, partner_id, partner_name, on_back, show_msg):
    chat_list = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)

    input_box = ft.TextField(hint_text="发送消息...", expand=True, border_radius=20, bgcolor="white",
                             content_padding=10)

    is_active = True

    def render_message(msg):
        is_me = msg['is_me']
        content = msg['content']
        msg_type = msg.get('type', 'text') 

        if msg_type == 'image' or content.startswith('image:'):
            content_widget = ft.Text("[图片]", color="blue")
        else:
            content_widget = ft.Text(content, color="white" if is_me else "black", size=16)

        return ft.Row(
            controls=[
                ft.Container(
                    content=content_widget,
                    bgcolor="blue" if is_me else "white",
                    padding=10,
                    border_radius=10,
                    border=None if is_me else ft.border.all(1, "#eee")
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START
        )

    def load_messages():
        try:
            res = APIClient.get_messages(current_user['id'], partner_id)
            if res.status_code == 200:
                msgs = res.json().get('data', [])
                chat_list.controls.clear()
                for m in msgs:
                    chat_list.controls.append(render_message(m))
                if chat_list.page: chat_list.update()
        except Exception as e:
            print(f"Chat load error: {e}")

    def send_text(e):
        txt = input_box.value
        if not txt: return
        try:
            res = APIClient.send_message(current_user['id'], partner_id, content=txt)
            if res.status_code == 200:
                input_box.value = ""
                input_box.focus()
                load_messages()  
            else:
                show_msg("发送失败")
        except Exception as ex:
            show_msg(str(ex))

    def poll_loop():
        while is_active:
            load_messages()
            time.sleep(3)

    def on_mount():
        if chat_list.page:
            t = threading.Thread(target=poll_loop, daemon=True)
            t.start()

    def safe_back(e):
        nonlocal is_active
        is_active = False
        on_back(e)

    wrapper = ft.Container(
        expand=True,
        bgcolor="#f0f2f5",
        content=ft.Column([
            ft.Container(
                bgcolor="white", padding=10,
                content=ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=safe_back),
                    ft.Text(f"与 {partner_name} 聊天中", size=18, weight="bold"),
                    ft.Container(expand=True)
                ])
            ),
            chat_list,
            ft.Container(
                bgcolor="white", padding=10,
                content=ft.Row([
                    input_box,
                    ft.IconButton(ft.Icons.SEND, icon_color="blue", on_click=send_text)
                ])
            )
        ])
    )

    wrapper.did_mount = on_mount
    return wrapper