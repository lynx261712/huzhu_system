import flet as ft


def create_skill_card(item, on_click):
    #1提供, 2需求
    is_supply = (item.get('type', 1) == 1)

    if is_supply:
        tag_text = "我能提供"
        tag_color = "blue"
    else:
        tag_text = "急需帮助"
        tag_color = "orange"

    return ft.Container(
        bgcolor="white",
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black")),
        content=ft.Column([
            #图片
            ft.Image(
                src=item['image'],
                width=float("inf"),
                height=110,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.only(top_left=10, top_right=10)
            ),
            #文字内容
            ft.Container(
                padding=8,
                content=ft.Column([
                    #标签
                    ft.Container(
                        content=ft.Text(tag_text, size=10, color="white", weight="bold"),
                        bgcolor=tag_color,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4
                    ),
                    #标题
                    ft.Text(
                        item['title'],
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        size=14,
                        weight="bold"
                    ),
                    #代价/悬赏
                    ft.Text(
                        item['cost'],  
                        size=12,
                        color="red",
                        weight="bold"
                    ),
                ], spacing=5)
            )
        ], spacing=0),
        data=item,
        on_click=on_click
    )


def create_lost_card(item, on_click):
    #0丢了, 1捡了
    is_found = (item.get('type', 0) == 1)

    if is_found:
        tag_text = "✨ 捡到了"
        tag_color = "green"
    else:
        tag_text = "🆘 丢东西"
        tag_color = "red"

    return ft.Container(
        bgcolor="white",
        border_radius=10,
        padding=10,
        shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black")),
        content=ft.Row([
            ft.Image(
                src=item['image'],
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,
                border_radius=8
            ),
            ft.Container(
                expand=True,
                content=ft.Column([
                    #顶部标签和时间
                    ft.Row([
                        ft.Container(
                            content=ft.Text(tag_text, size=11, color="white"),
                            bgcolor=tag_color,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4
                        ),
                        ft.Text(item['time'], size=10, color="grey")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    #标题
                    ft.Text(
                        item['title'],
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        size=16,
                        weight="bold"
                    ),

                    #描述
                    ft.Text(
                        item['desc'],
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        size=12,
                        color="grey"
                    ),

                    #地点
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, size=12, color="blue"),
                        ft.Text(item['location'], size=12, color="blue")
                    ])
                ], spacing=3, alignment=ft.MainAxisAlignment.START)
            )
        ]),
        data=item,
        on_click=on_click
    )