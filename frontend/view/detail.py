import flet as ft
from api_client import APIClient


def DetailView(item, category, on_back, show_msg, current_user, on_nav_to_chat):
    detail_img = ft.Image(src=item['image'], width=float("inf"), height=200, fit=ft.ImageFit.COVER)

    #聊天/联系
    def go_chat(e):
        if not current_user['id']: return show_msg("请先登录")

        target_id = item.get('user_id')
        target_name = item.get('user', '未知用户')

        if str(target_id) == str(current_user['id']):
            return show_msg("不能和自己聊天")

        #创建会话关联
        try:
            #通知后端这个人要咨询这个任务
            APIClient.start_inquiry(
                task_id=item['id'],
                task_type=category,
                visitor_id=current_user['id']
            )
        except Exception as ex:
            print(f"会话创建警告: {ex}")
        #----------------------------

        on_nav_to_chat(target_id, target_name)

    #接单
    def do_accept(e):
        if not current_user['id']: return show_msg("请先登录")
        if str(current_user['id']) == str(item.get('user_id')): return show_msg("不能接自己的单")

        try:
            res = APIClient.accept_order(item['id'], category, current_user['id'])
            if res.status_code == 200:
                show_msg("接单成功！请在'我的帮助'中查看", "green")
                on_back(None)
            else:
                show_msg(res.json().get('msg', "接单失败"))
        except Exception as ex:
            show_msg(str(ex))

    #按钮
    action_row = ft.Row([
        ft.ElevatedButton("💬 联系", on_click=go_chat, expand=1),
        ft.ElevatedButton("🙋‍♂️ 接收", on_click=do_accept, expand=1, bgcolor="orange", color="white")
    ])


    if category == "skill":
        desc_text = item.get('desc') or "暂无详细描述"
        cost_text = item.get('cost') or "面议"
        content_val = f"详细描述: {desc_text}\n\n互助代价: {cost_text}"
    else:
        content_val = f"描述: {item.get('desc')}"

    meta_info = []
    if category == "skill":
        meta_info = [ft.Icon(ft.Icons.PERSON, size=16), ft.Text(item.get('user', '未知'))]
    else:
        meta_info = [ft.Icon(ft.Icons.LOCATION_ON, size=16), ft.Text(item.get('location', '未知'))]

    return ft.Column([
        ft.Stack([
            detail_img,
            ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda e: on_back(None), left=5, top=5)
        ]),
        ft.Container(padding=20, content=ft.Column([
            ft.Text(item['title'], size=22, weight="bold"),
            ft.Divider(),
            ft.Text(content_val, size=16),
            ft.Row(meta_info),
            ft.Container(height=20),
            action_row
        ]))
    ])