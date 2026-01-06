from models import Skill, User
from extensions import db


def test_full_order_flow(client, app):
    """
    1. 用户1发布技能
    2. 用户2接单
    3. 确认完成
    4. 检查用户1积分是否增加
    """

    #发布技能
    print("\n步骤1: 用户admin发布技能...")
    resp_create = client.post('/api/skills', data={
        "title": "测试修电脑",
        "cost": "10积分",
        "type": 1,  #1我能提供
        "user_id": 1
    })
    assert resp_create.status_code == 200

    #验证数据库里是否生成订单
    with app.app_context():
        skill = Skill.query.filter_by(title="测试修电脑").first()
        skill_id = skill.id
        assert skill.status == 0  #初始状态
        print(f"  -> 订单创建成功，ID: {skill_id}")

    #接单
    print("步骤2: 用户helper接单...")
    resp_accept = client.post('/api/order/accept', json={
        "id": skill_id,
        "category": "skill",
        "user_id": 2
    })
    assert resp_accept.status_code == 200
    print("  -> 接单成功")

    #确认完成
    print("步骤3: 确认订单完成...")
    resp_finish = client.post('/api/order/finish', json={
        "id": skill_id,
        "category": "skill"
    })
    assert resp_finish.status_code == 200
    print("  -> 订单已完成")

    #验证积分结算
    print("步骤4: 验证积分结算...")
    with app.app_context():
        user1 = User.query.get(1)
        #初始10分+奖励5分=15
        assert user1.points == 15
        print(f"  -> 测试通过！用户admin的积分正确变更为: {user1.points}")