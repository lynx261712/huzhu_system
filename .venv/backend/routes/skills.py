from flask import Blueprint, jsonify, request
from extensions import db   
from models import Skill  

bp = Blueprint('skills', __name__)

@bp.route('/skills', methods=['GET'])
def get_skills():
    try:
        keyword = request.args.get('q')
        query = Skill.query
        if keyword:
            query = query.filter(Skill.title.contains(keyword) | Skill.cost.contains(keyword))
        skills = query.order_by(Skill.create_time.desc()).all()
        data = []
        for s in skills:
            author_name = s.author.username if s.author else "未知用户"
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": s.id, "title": s.title, "cost": s.cost, "type": s.type,
                "image": s.image, "status": s.status, "user": author_name, "avatar": author_avatar
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

@bp.route('/skills', methods=['POST'])
def create_skill():
    try:
        data = request.get_json()
        new_skill = Skill(
            title=data['title'], cost=data['cost'], type=int(data.get('type', 1)),
            image=data.get('image', "https://picsum.photos/200/200"),
            user_id=data.get('user_id', 1)
        )
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route('/skills/complete', methods=['POST'])
def complete_transaction():
    data = request.get_json()
    skill_id = data.get('skill_id')
    current_user_id = data.get('user_id')  #需求发起者

    try:
        #开启事务
        with db.session.begin_nested():
            skill = Skill.query.get(skill_id)
            if not skill:
                return jsonify({"code": 404, "msg": "记录不存在"}), 404

            if skill.status == 2:
                return jsonify({"code": 400, "msg": "该订单已完成，请勿重复操作"}), 400

            try:
                cost_val = int(skill.cost.replace("积分", "").strip())
            except:
                cost_val = 0  

            user = User.query.get(current_user_id)


            if skill.type == 2 and cost_val > 0:
                if user.points < cost_val:
                    return jsonify({"code": 400, "msg": "您的积分不足，无法结算"}), 400

                user.points -= cost_val

            if skill.type == 1:
                user.points += 2

            skill.status = 2

            db.session.add(user)
            db.session.add(skill)

        db.session.commit()
        return jsonify({"code": 200, "msg": "交易完成，积分已更新"})

    except Exception as e:
        db.session.rollback()  #报错回滚
        return jsonify({"code": 500, "msg": f"交易失败: {str(e)}"}), 500