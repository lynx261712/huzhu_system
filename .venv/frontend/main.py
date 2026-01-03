import flet as ft
from view.login import LoginView
from view.profile import ProfileView
from view.detail import DetailView
from view.home import HomeView
from view.my_help import MyHelpView
from view.my_posts import MyPostsView
from view.chat import ChatView 


def main(page: ft.Page):
    #页面基础
    page.title = "校园互助平台"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#f0f2f5"
    page.padding = 0

    current_user = {"id": None, "name": None}

    #全局提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    body = ft.Container(expand=True)


    def login_success(user_data):
        current_user['id'] = user_data['user_id']
        current_user['name'] = user_data['username']
        show_msg(f"欢迎 {current_user['name']}", "green")
        switch_tab(2)

    def logout(e):
        current_user['id'] = None
        current_user['name'] = None
        show_msg("已退出登录", "green")
        switch_tab(2)

    def render_chat(partner_id, partner_name, back_callback):
        body.content = ChatView(
            current_user=current_user,
            partner_id=partner_id,
            partner_name=partner_name,
            on_back=back_callback,
            show_msg=show_msg
        )
        page.update()

    #详情页跳转
    def go_detail(item, category):
        def chat_callback(pid, pname):
            render_chat(pid, pname, lambda e: switch_tab(0))

        body.content = DetailView(
            item,
            category,
            lambda e: switch_tab(0),
            show_msg,
            current_user,
            chat_callback 
        )
        page.update()

    def go_my_help(e):
        def chat_callback(pid, pname):
            render_chat(pid, pname, lambda e: go_my_help(None))

        body.content = MyHelpView(
            current_user['id'],
            lambda e: switch_tab(2), 
            show_msg,
            on_nav_to_chat=chat_callback
        )
        page.update()

    #我的发布跳转
    def go_my_posts(e):
        body.content = MyPostsView(
            current_user['id'],
            lambda e: switch_tab(2),
            show_msg
        )
        page.update()

    def switch_tab(e):
        idx = e if isinstance(e, int) else e.control.data

        for i, btn in enumerate(nav_bar.content.controls):
            btn.icon_color = "blue" if i == idx else "grey"

        if idx == 0:
            body.content = home_view.get_main_view()
        elif idx == 1:
            body.content = home_view.get_post_view(on_success_nav=switch_tab)
        elif idx == 2:
            if current_user['id']:
                body.content = ProfileView(
                    user_id=current_user['id'],
                    on_logout=logout,
                    show_msg=show_msg,
                    on_nav_to_help=go_my_help,  
                    on_nav_to_my_posts=go_my_posts 
                )
            else:
                body.content = LoginView(login_success, show_msg)

        page.update()

    home_view = HomeView(page, show_msg, go_detail, lambda: current_user)

    nav_bar = ft.Container(
        bgcolor="white", padding=10, border=ft.border.only(top=ft.BorderSide(1, "#e0e0e0")),
        content=ft.Row([
            ft.IconButton(ft.Icons.HOME, tooltip="首页", data=0, on_click=switch_tab),
            ft.IconButton(ft.Icons.ADD_CIRCLE, icon_size=40, tooltip="发布", data=1, on_click=switch_tab),
            ft.IconButton(ft.Icons.PERSON, tooltip="我的", data=2, on_click=switch_tab)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    page.add(body, nav_bar)
    switch_tab(0)


if __name__ == "__main__":
    ft.app(target=main)