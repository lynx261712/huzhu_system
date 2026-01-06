import flet as ft
from api_client import APIClient


def MyPostsView(user_id, on_back, show_msg, on_nav_to_chat):
    posts_list = ft.ListView(expand=True, spacing=10, padding=10)

    #弹窗逻辑
    def show_inquiries_dialog(e):
        item_data = e.control.data
        task_id = item_data['id']
        task_type = item_data.get('category', 'skill')

        dlg_list = ft.Column(height=200, scroll=ft.ScrollMode.AUTO)
        dlg = ft.AlertDialog(
            title=ft.Text("咨询列表"),
            content=dlg_list,
            actions=[
                ft.TextButton("关闭", on_click=lambda e: setattr(dlg, 'open', False) or e.page.update())
            ]
        )

        if posts_list.page:
            posts_list.page.dialog = dlg
            dlg.open = True
            posts_list.page.update()

        try:
            res = APIClient.get_task_inquiries(task_id, task_type)

            if res.status_code == 200:
                inquirers = res.json()
                if not inquirers:
                    dlg_list.controls.append(ft.Text("暂无咨询记录"))
                else:
                    for user in inquirers:
                        dlg_list.controls.append(
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text(user['username']),
                                subtitle=ft.Text(f"时间: {user['create_time']}"),
                                trailing=ft.IconButton(
                                    ft.Icons.CHAT,
                                    icon_color="blue",
                                    on_click=lambda _, uid=user['user_id'], uname=user['username']: (
                                        setattr(dlg, 'open', False),
                                        posts_list.page.update(),
                                        on_nav_to_chat(uid, uname)
                                    )
                                )
                            )
                        )
            else:
                dlg_list.controls.append(ft.Text("获取失败"))
        except Exception as ex:
            dlg_list.controls.append(ft.Text(f"网络错误: {ex}"))

        if posts_list.page: posts_list.page.update()

    def finish_order(e):
        data = e.control.data
        try:
            res = APIClient.finish_order(data['id'], data['category'])
            if res.status_code == 200:
                show_msg("订单已确认完成", "green")
                load_data()
            else:
                show_msg("操作失败")
        except:
            show_msg("网络错误")

    def review_order(e):
        action = e.control.data['action']
        item_data = e.control.data['item']
        try:
            res = APIClient.review_order(item_data['id'], item_data['category'], action, user_id)
            if res.status_code == 200:
                show_msg(res.json().get('msg'), "green")
                load_data()
            else:
                show_msg(res.json().get('msg'))
        except:
            show_msg("网络错误")

    def delete_post(e):
        data = e.control.data
        APIClient.delete_item(data['id'], data['category'])
        load_data()

    def load_data():
        posts_list.controls.clear()
        try:
            res = APIClient.get_user_posts(user_id)
            items = res.json().get('data', [])

            counts_map = {}
            try:
                count_res = APIClient.get_inquiry_counts(user_id)
                if count_res.status_code == 200:
                    c_data = count_res.json()
                    for kid, v in c_data.get('skill_counts', {}).items():
                        counts_map[f"skill_{kid}"] = v
                    for kid, v in c_data.get('lost_counts', {}).items():
                        counts_map[f"lost_{kid}"] = v
            except Exception as ex:
                print(f"获取咨询数量失败: {ex}")

            for item in items:
                status = item.get('status', 0)

                cat = item.get('category', 'skill')
                tid = item['id']
                count_key = f"{cat}_{tid}"
                inquiry_count = counts_map.get(count_key, 0)

                inquiry_color = "blue" if inquiry_count > 0 else "grey"
                inquiry_btn = ft.TextButton(
                    text=f"咨询 ({inquiry_count})",
                    icon=ft.Icons.FORUM,
                    icon_color=inquiry_color,
                    disabled=(inquiry_count == 0),
                    data=item,
                    on_click=show_inquiries_dialog
                )

                if status == 0:
                    status_widget = ft.Container(content=ft.Text("等待接单", size=10, color="white"), bgcolor="grey",
                                                 padding=5, border_radius=4)
                    action_widget = ft.Column([
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", tooltip="删除", data=item,
                                      on_click=delete_post),
                        inquiry_btn
                    ], spacing=0, alignment="center")

                elif status == 1:
                    status_widget = ft.Container(content=ft.Text("进行中", size=10, color="white"), bgcolor="blue",
                                                 padding=5, border_radius=4)
                    action_widget = ft.Column([
                        ft.ElevatedButton("确认完成", height=30, style=ft.ButtonStyle(padding=5), data=item,
                                          on_click=finish_order),
                        inquiry_btn
                    ], spacing=5, alignment="center")

                else:
                    status_widget = ft.Container(content=ft.Text("已完成", size=10, color="white"), bgcolor="green",
                                                 padding=5, border_radius=4)
                    review_s = item.get('review', 0)
                    if review_s == 0:
                        review_row = ft.Row([
                            ft.IconButton(ft.Icons.THUMB_UP, icon_color="orange", tooltip="打赏",
                                          data={"action": "reward", "item": item}, on_click=review_order),
                            ft.IconButton(ft.Icons.THUMB_DOWN, icon_color="grey", tooltip="投诉",
                                          data={"action": "complain", "item": item}, on_click=review_order)
                        ], spacing=0)
                        action_widget = ft.Column([review_row, inquiry_btn])
                    else:
                        action_widget = ft.Column([
                            ft.Text("已评价", size=12, color="orange"),
                            inquiry_btn
                        ])

                posts_list.controls.append(ft.Container(
                    bgcolor="white", padding=10, border_radius=10,
                    content=ft.Row([
                        ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                        ft.Container(expand=True, content=ft.Column([
                            ft.Row([status_widget, ft.Text(item['create_time'], size=10, color="grey")],
                                   alignment="spaceBetween"),
                            ft.Text(item['title'], size=16, weight="bold", max_lines=1),
                        ], spacing=5)),
                        action_widget
                    ])
                ))
            if not items: posts_list.controls.append(ft.Text("暂无记录", text_align="center"))
        except Exception as e:
            print(f"MyPosts Load Error: {e}")
        if posts_list.page: posts_list.update()

    load_data()
    return ft.Column([
        ft.Container(padding=10, content=ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: on_back(None)),
                                                 ft.Text("我的发布管理", size=20, weight="bold")])),
        posts_list
    ])