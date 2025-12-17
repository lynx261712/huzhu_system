import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, User, LostItem, Skill

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#技能列表
@app.route('/api/skills', methods=['GET'])
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
            #随机头像
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": s.id, "title": s.title, "cost": s.cost, "type": s.type,
                "image": s.image, "status": s.status, "user": author_name, "avatar": author_avatar
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

#失物列表
@app.route('/api/lost-items', methods=['GET'])
def get_lost_items():
    try:
        item_type = request.args.get('type', type=int)
        keyword = request.args.get('q')
        query = LostItem.query
        if item_type is not None: query = query.filter_by(type=item_type)
        if keyword:
            query = query.filter(LostItem.title.contains(keyword) | LostItem.desc.contains(keyword) | LostItem.location.contains(keyword))
        items = query.order_by(LostItem.create_time.desc()).all()
        data = []
        for item in items:
            author_name = item.author.username if item.author else "未知用户"
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": item.id, "title": item.title, "desc": item.desc, "location": item.location,
                "type": item.type, "image": item.image, "time": item.create_time.strftime("%Y-%m-%d"),
                "user": author_name, "avatar": author_avatar
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

#发布技能
@app.route('/api/skills', methods=['POST'])
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

#发布失物
@app.route('/api/lost-items', methods=['POST'])
def create_lost_item():
    try:
        data = request.get_json()
        new_item = LostItem(
            title=data.get('title'), desc=data.get('desc'), location=data.get('location'),
            type=int(data.get('type', 0)),
            image=data.get('image', "https://picsum.photos/200/200"),
            user_id=data.get('user_id', 1)
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

#获取详情
@app.route('/api/interact', methods=['POST'])
def interact():
    try:
        data = request.get_json()
        item = Skill.query.get(data.get('item_id')) if data.get('category') == 'skill' else LostItem.query.get(data.get('item_id'))
        if not item: return jsonify({"code": 404, "msg": "未找到"}), 404
        contact = item.author.contact if item.author else "未留联系方式"
        return jsonify({"code": 200, "data": {"contact": contact}})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

#用户认证
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"code": 400, "msg": "用户名已存在"}), 400
    new_user = User(username=data['username'], password=data['password'], contact=data['contact'])
    db.session.add(new_user); db.session.commit()
    return jsonify({"code": 200, "msg": "注册成功"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user: return jsonify({"code": 200, "data": {"user_id": user.id, "username": user.username}})
    return jsonify({"code": 401, "msg": "账号或密码错误"}), 401

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    user = User.query.get(user_id)
    if not user: return jsonify({"code": 404, "msg": "用户不存在"}), 404
    skills_count = Skill.query.filter_by(user_id=user.id).count()
    lost_count = LostItem.query.filter_by(user_id=user.id).count()
    return jsonify({
        "code": 200,
        "data": {
            "id": user.id, "username": user.username, "contact": user.contact, "points": user.points,
            "avatar": f"https://ui-avatars.com/api/?name={user.username}&background=random",
            "stats": {"posts": skills_count + lost_count, "skills": skills_count, "lost": lost_count}
        }
    })

@app.route('/api/user/update', methods=['POST'])
def update_user():
    data = request.get_json()
    user = User.query.get(data['user_id'])
    if data.get('username'): user.username = data['username']
    if data.get('contact'): user.contact = data['contact']
    db.session.commit()
    return jsonify({"code": 200, "msg": "修改成功"})

#我的发布 删除
@app.route('/api/user/posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    skills = Skill.query.filter_by(user_id=user_id).all()
    losts = LostItem.query.filter_by(user_id=user_id).all()
    data = []
    for s in skills:
        data.append({"id": s.id, "category": "skill", "title": s.title, "tag": "提供" if s.type==1 else "求助", "color": "blue" if s.type==1 else "orange", "image": s.image, "info": s.cost, "create_time": s.create_time.strftime("%m-%d")})
    for l in losts:
        data.append({"id": l.id, "category": "lost", "title": l.title, "tag": "捡到" if l.type==1 else "丢失", "color": "green" if l.type==1 else "red", "image": l.image, "info": l.location, "create_time": l.create_time.strftime("%m-%d")})
    data.sort(key=lambda x: x['create_time'], reverse=True)
    return jsonify({"code": 200, "data": data})

@app.route('/api/delete', methods=['POST'])
def delete_post():
    data = request.get_json()
    item = Skill.query.get(data['id']) if data['category'] == 'skill' else LostItem.query.get(data['id'])
    if item: db.session.delete(item); db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功"})

if __name__ == '__main__':
    print("后端启动: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)