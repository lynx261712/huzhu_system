from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from extensions import db
from models import Skill, LostItem, User
from utils import save_uploaded_file

bp = Blueprint('skills', __name__)


#获取技能列表
@bp.route('/skills', methods=['GET'])
def get_skills():
    try:
        keyword = request.args.get('q')
        #只显示status=0未接单，已接单的不显示在广场上
        query = Skill.query.filter_by(status=0)

        if keyword:
            #支持搜标题和报酬
            query = query.filter(Skill.title.contains(keyword) | Skill.cost.contains(keyword))

        #如果数据多了要做分页，现在先全部返回
        skills = query.order_by(Skill.create_time.desc()).all()

        data = []
        for s in skills:
            author_name = s.author.username if s.author else "未知用户"
            data.append({
                "id": s.id, "title": s.title, "cost": s.cost, "type": s.type,
                "image": s.image, "status": s.status,
                "user": author_name, "user_id": s.user_id
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        print(f"Error in get_skills: {e}")  #方便排错
        return jsonify({"code": 500, "msg": str(e)}), 500


#发布技能/需求
@bp.route('/skills', methods=['POST'])
def create_skill():
    try:
        #print("DEBUG: 收到发布请求...")
        title = request.form.get('title')
        cost = request.form.get('cost')
        #1提供技能, 2求助
        type_val = request.form.get('type', 1, type=int)
        user_id = request.form.get('user_id', type=int)

        if not title or not user_id:
            return jsonify({"code": 400, "msg": "标题或用户ID不能为空"}), 400

        image_file = request.files.get('image')
        #调用utils的通用上传函数
        image_url = save_uploaded_file(image_file)

        new_skill = Skill(
            title=title,
            cost=cost,
            type=type_val,
            image=image_url,
            user_id=user_id
        )
        db.session.add(new_skill)
        db.session.commit()

        print(f"DEBUG: 用户 {user_id} 发布成功: {title}")
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


#接单接口
@bp.route('/order/accept', methods=['POST'])
def accept_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')  #区分是skill还是lost
        user_id = data.get('user_id')

        print(f"DEBUG: 用户 {user_id} 正在尝试接单 {item_id} ({category})")

        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item:
            return jsonify({"code": 404, "msg": "订单不存在"}), 404

        #检查 防止并发抢单
        #如果status已经被别人改成1了 拦住
        if item.status != 0:
            return jsonify({"code": 400, "msg": "手慢了，该单已被抢或已完成"}), 400

        #防止自己接自己的单刷分
        if str(item.user_id) == str(user_id):
            return jsonify({"code": 400, "msg": "不能接自己的单"}), 400

        #更新状态 0 -> 1进行中
        item.status = 1
        item.helper_id = user_id
        db.session.commit()

        return jsonify({"code": 200, "msg": "接单成功"})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500


#确认完成  积分结算
@bp.route('/order/finish', methods=['POST'])
def finish_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')

        if category == 'skill':
            item = Skill.query.get(item_id)
        else:
            item = LostItem.query.get(item_id)

        if not item: return jsonify({"code": 404, "msg": "未找到订单"}), 404

        #防止重复结算
        if item.status != 1:
            return jsonify({"code": 400, "msg": "订单状态不正确(必须是进行中才能完成)"}), 400

        #积分结算逻辑
        #谁出力，谁得5分
        reward_points = 5
        target_user = None

        publisher = User.query.get(item.user_id)  #发布者
        helper = User.query.get(item.helper_id)  #接单者

        if category == 'skill':
            if item.type == 1:
                #技能贴（提供服务） 给发布者加分
                target_user = publisher
            else:
                #求助贴（需要帮忙） 给接单者加分
                target_user = helper

        elif category == 'lost':
            if item.type == 1:
                #招领贴（捡到东西） 给发布者加分
                target_user = publisher
            else:
                #失物贴（丢了东西） 给接单者加分
                target_user = helper

        if target_user:
            print(f"DEBUG: 结算完成，给用户 {target_user.username} 增加 {reward_points} 积分")
            target_user.points += reward_points

        #更新状态：1 -> 2已完成
        item.status = 2
        db.session.commit()

        msg = f"订单已完成，{target_user.username if target_user else '用户'} 积分+5"
        return jsonify({"code": 200, "msg": msg})
    except Exception as e:
        print(f"Finish order error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


#评价接口
@bp.route('/order/review', methods=['POST'])
def review_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')
        action = data.get('action')  #reward好评  complaint差评
        current_uid = data.get('current_user_id')

        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item: return jsonify({"code": 404, "msg": "未找到"}), 404

        target_user = None
        #判断当前是谁在操作评价
        is_poster = (str(current_uid) == str(item.user_id))

        if is_poster:
            #发布者评价接单者
            if item.poster_review != 0: return jsonify({"code": 400, "msg": "您已评价过"}), 400
            item.poster_review = 1 if action == 'reward' else 2
            if item.helper_id:
                target_user = User.query.get(item.helper_id)

        elif str(current_uid) == str(item.helper_id):
            #接单者评价发布者
            if item.helper_review != 0: return jsonify({"code": 400, "msg": "您已评价过"}), 400
            item.helper_review = 1 if action == 'reward' else 2
            target_user = User.query.get(item.user_id)

        else:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        #评价影响积分+2-2
        if target_user:
            change = 2 if action == 'reward' else -2
            target_user.points += change
            db.session.commit()
            print(f"DEBUG: 评价生效，对方积分变化: {change}")
            return jsonify({"code": 200, "msg": f"评价成功，对方积分 {'+2' if change > 0 else '-2'}"})

        db.session.commit()
        return jsonify({"code": 200, "msg": "评价成功"})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500


#获取我相关的记录
@bp.route('/user/helps/<int:user_id>', methods=['GET'])
def get_my_helps(user_id):
    try:
        #查出：
        #我是接单人 helper_id == me
        #或者 我是发布人user_id == me 且 订单已经开始流转了status!= 0
        skill_filter = or_(
            Skill.helper_id == user_id,
            and_(Skill.user_id == user_id, Skill.status != 0)
        )
        lost_filter = or_(
            LostItem.helper_id == user_id,
            and_(LostItem.user_id == user_id, LostItem.status != 0)
        )

        my_skills = Skill.query.filter(skill_filter).all()
        my_losts = LostItem.query.filter(lost_filter).all()

        data = []

        #封装数据，方便前端统一展示
        def pack_item(obj, cat):
            is_poster = (str(obj.user_id) == str(user_id))

            #如果我是发布者，对方就是接单人
            if is_poster:
                target_id = obj.helper_id
                helper_user = User.query.get(target_id) if target_id else None
                target_name = helper_user.username if helper_user else "未知接单人"
                my_review = obj.poster_review
            else:
                target_id = obj.user_id
                target_name = obj.author.username if obj.author else "未知发布者"
                my_review = obj.helper_review

            if obj.create_time:
                time_str = obj.create_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "未知时间"

            return {
                "id": obj.id,
                "category": cat,
                "title": obj.title,
                "image": obj.image,
                "status": obj.status,
                "create_time": time_str,
                "is_poster": is_poster,
                "target_id": target_id,
                "target_name": target_name,
                "my_review": my_review
            }

        for s in my_skills: data.append(pack_item(s, "skill"))
        for l in my_losts: data.append(pack_item(l, "lost"))

        #按时间倒序，最新的在前面
        data.sort(key=lambda x: x['create_time'], reverse=True)
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        print(f"Get helps error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


#搜索热词
@bp.route('/tags', methods=['GET'])
def get_hot_tags():
    try:
        #取最近发布的几个标题作为热词
        skill_titles = db.session.query(Skill.title) \
            .filter_by(status=0) \
            .order_by(Skill.create_time.desc()) \
            .limit(4).all()

        lost_titles = db.session.query(LostItem.title) \
            .filter_by(status=0) \
            .order_by(LostItem.create_time.desc()) \
            .limit(4).all()

        tags = []
        seen_titles = set()  #去重用

        for t in skill_titles:
            if t[0] and t[0] not in seen_titles:
                tags.append({"text": t[0], "cat": "skill"})
                seen_titles.add(t[0])

        for t in lost_titles:
            if t[0] and t[0] not in seen_titles:
                tags.append({"text": t[0], "cat": "lost"})
                seen_titles.add(t[0])

        #如果数据库是空的，为了不让界面空着，给几个默认值
        if not tags:
            tags = [
                {"text": "Python辅导", "cat": "skill"},
                {"text": "捡到雨伞", "cat": "lost"}
            ]

        return jsonify({"code": 200, "data": tags[:8]})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500