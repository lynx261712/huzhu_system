from flask import Blueprint, jsonify, request
from extensions import db
from models import Skill, LostItem, User

bp = Blueprint('skills', __name__)


#查询 发布
@bp.route('/skills', methods=['GET'])
def get_skills():
    """获取技能大厅列表 只看未接单的 status=0"""
    try:
        keyword = request.args.get('q')
        query = Skill.query.filter_by(status=0)

        if keyword:
            query = query.filter(Skill.title.contains(keyword) | Skill.cost.contains(keyword))

        skills = query.order_by(Skill.create_time.desc()).all()

        data = []
        for s in skills:
            author_name = s.author.username if s.author else "未知用户"
            data.append({
                "id": s.id,
                "title": s.title,
                "cost": s.cost,
                "type": s.type,
                "image": s.image,
                "status": s.status,
                "user": author_name,
                "user_id": s.user_id  #返回发布者ID，防止自己接自己的单
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route('/skills', methods=['POST'])
def create_skill():
    """发布技能/需求"""
    try:
        data = request.get_json()
        new_skill = Skill(
            title=data['title'],
            cost=data['cost'],
            type=int(data.get('type', 1)),
            image="https://picsum.photos/200/200",
            user_id=data.get('user_id', 1)
        )
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


#交易  接单-完成-评价
@bp.route('/order/accept', methods=['POST'])
def accept_order():
    """接单接口"""
    data = request.get_json()
    item_id = data.get('id')
    category = data.get('category')  # 'skill' 或 'lost'
    helper_id = data.get('user_id')

    #根据类型查找对应表
    item = Skill.query.get(item_id) if category == 'skill' else LostItem.query.get(item_id)

    if not item: return jsonify({"code": 404, "msg": "物品不存在"}), 404
    if item.status != 0: return jsonify({"code": 400, "msg": "手慢了，已被抢单"}), 400
    if str(item.user_id) == str(helper_id): return jsonify({"code": 400, "msg": "不能接自己的单"}), 400

  
    item.status = 1  #1进行中
    item.helper_id = helper_id
    db.session.commit()
    return jsonify({"code": 200, "msg": "接单成功！请在'我的帮助'中查看"})


@bp.route('/order/finish', methods=['POST'])
def finish_order():
    """
    完成订单接口 结算积分
    丢失了Lost type=0-> 接单人Helper+3
    捡到了Lost type=1-> 发布人Publisher+3
    我能提供Skill type=1-> 发布人Publisher+5
    需要帮助Skill type=2-> 接单人Helper+5
    """
    data = request.get_json()
    item_id = data.get('id')
    category = data.get('category')

    item = Skill.query.get(item_id) if category == 'skill' else LostItem.query.get(item_id)

    if not item: return jsonify({"code": 404, "msg": "订单不存在"}), 404
    if item.status == 2: return jsonify({"code": 400, "msg": "订单已完成，请勿重复操作"}), 400

    publisher = User.query.get(item.user_id)
    helper = User.query.get(item.helper_id)

    if not publisher or not helper: return jsonify({"code": 500, "msg": "用户数据异常"}), 500

    msg_detail = ""

    #积分结算
    try:
        if category == 'lost' and item.type == 0:
            helper.points += 3
            msg_detail = "感谢帮助，接单人积分+3"

        elif category == 'lost' and item.type == 1:
            publisher.points += 3
            msg_detail = "拾金不昧，发布人积分+3"

        elif category == 'skill' and item.type == 1:
            publisher.points += 5
            msg_detail = "服务完成，发布人积分+5"

        elif category == 'skill' and item.type == 2:
            helper.points += 5
            msg_detail = "互助成功，接单人积分+5"

        item.status = 2
        db.session.commit()
        return jsonify({"code": 200, "msg": f"互助完成！{msg_detail}"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"结算失败: {str(e)}"}), 500


@bp.route('/order/review', methods=['POST'])
def review_order():
    """
    评价接口 打赏/投诉
    Helper在我的帮助评价Publisher
    """
    data = request.get_json()
    action = data.get('action') 

    item = Skill.query.get(data['id']) if data['category'] == 'skill' else LostItem.query.get(data['id'])
    if not item: return jsonify({"code": 404, "msg": "订单不存在"}), 404

    target_user = User.query.get(item.user_id)

    if not target_user: return jsonify({"code": 500, "msg": "用户异常"}), 500
    if item.review_status != 0: return jsonify({"code": 400, "msg": "已评价过"}), 400

    msg = ""
    try:
        if action == 'reward':
            target_user.points += 2
            item.review_status = 1  
            msg = "好评成功！对方积分+2"
        elif action == 'complain':
            target_user.points -= 2
            if target_user.points < 0: target_user.points = 0  #积分不为负
            item.review_status = 2  
            msg = "投诉成功！对方积分-2"

        db.session.commit()
        return jsonify({"code": 200, "msg": msg})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


#用户相关查询
@bp.route('/user/helps/<int:user_id>', methods=['GET'])
def get_my_helps(user_id):
    try:
        skills = Skill.query.filter_by(helper_id=user_id).all()
        losts = LostItem.query.filter_by(helper_id=user_id).all()

        data = []
        for s in skills:
            data.append({
                "id": s.id, "category": "skill", "title": s.title,
                "status": s.status, "image": s.image,
                "review": s.review_status, "info": s.cost
            })
        for l in losts:
            data.append({
                "id": l.id, "category": "lost", "title": l.title,
                "status": l.status, "image": l.image,
                "review": l.review_status, "info": l.location
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500