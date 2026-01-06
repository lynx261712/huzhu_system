import flet as ft
from view.login import LoginView
from view.profile import ProfileView
from view.detail import DetailView
from view.home import HomeView
from view.my_help import MyHelpView
from view.my_posts import MyPostsView
from view.chat import ChatView


def main(page: ft.Page):
    #页面基础设置
    page.title = "校园互助平台"
    page.theme = ft.Theme(font_family="Microsoft YaHei")

    #模拟手机屏幕尺寸
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#f0f2f5"
    page.padding = 0

    #全局
    #存登录后的用户信息
    current_user = {"id": None, "name": None}

    #全局提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    #页面容器
    body = ft.Container(expand=True)

    #回调函数----
    #登录成功后执行
    def login_success(user_data):
        #保存用户状态
        current_user['id'] = user_data['user_id']
        current_user['name'] = user_data['username']
        show_msg(f"欢迎 {current_user['name']}", "green")
        #跳转到个人中心 Tab索引为2
        switch_tab(2)

    def logout(e):
        #清空状态
        current_user['id'] = None
        current_user['name'] = None
        show_msg("已退出登录", "green")
        switch_tab(2)

    #渲染聊天页面 辅助函数
    def render_chat(partner_id, partner_name, back_callback):
        body.content = ChatView(
            current_user=current_user,
            partner_id=partner_id,
            partner_name=partner_name,
            on_back=back_callback,
            show_msg=show_msg
        )
        page.update()

    #导航跳转逻辑
    #详情页跳转
    def go_detail(item, category):
        def chat_callback(pid, pname):
            #聊完点返回，回到首页
            render_chat(pid, pname, lambda e: switch_tab(0))

        body.content = DetailView(
            item,
            category,
            lambda e: switch_tab(0),  #详情页点返回，去首页
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
            lambda e: switch_tab(2),  #点返回，去个人中心
            show_msg,
            on_nav_to_chat=chat_callback
        )
        page.update()

    def go_my_posts(e):
        # [修改] 定义跳转聊天的回调，聊完返回 MyPosts
        def chat_callback(pid, pname):
            render_chat(pid, pname, lambda e: go_my_posts(None))

        body.content = MyPostsView(
            current_user['id'],
            lambda e: switch_tab(2),
            show_msg,
            chat_callback # [修改] 传入这个参数修复报错
        )
        page.update()

    #路由控制器
    #点底部按钮切换页面
    def switch_tab(e):
        #兼容处理 e可能是点击事件对象，可能是直接传的int索引
        idx = e if isinstance(e, int) else e.control.data
        print(f"DEBUG: 用户点击了 Tab {idx}，准备切换页面...")

        #改变底部按钮颜色 高亮选中项
        for i, btn in enumerate(nav_bar.content.controls):
            btn.icon_color = "blue" if i == idx else "grey"

        #路由分发
        if idx == 0:
            #首页
            body.content = home_view.get_main_view()
        elif idx == 1:
            #发布页
            body.content = home_view.get_post_view(on_success_nav=switch_tab)
        elif idx == 2:
            #个人中心 要判断是否登录
            if current_user['id']:
                body.content = ProfileView(
                    user_id=current_user['id'],
                    on_logout=logout,
                    show_msg=show_msg,
                    on_nav_to_help=go_my_help,
                    on_nav_to_my_posts=go_my_posts
                )
            else:
                #没登录就显示登录页
                body.content = LoginView(login_success, show_msg)

        page.update()


    home_view = HomeView(page, show_msg, go_detail, lambda: current_user)

    #底部导航栏
    nav_bar = ft.Container(
        bgcolor="white", padding=10, border=ft.border.only(top=ft.BorderSide(1, "#e0e0e0")),
        content=ft.Row([
            ft.IconButton(ft.Icons.HOME, tooltip="首页", data=0, on_click=switch_tab),
            ft.IconButton(ft.Icons.ADD_CIRCLE, icon_size=40, tooltip="发布", data=1, on_click=switch_tab),
            ft.IconButton(ft.Icons.PERSON, tooltip="我的", data=2, on_click=switch_tab)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    #组装页面
    page.add(body, nav_bar)

    #默认打开首页
    switch_tab(0)


if __name__ == "__main__":
    ft.app(target=main)