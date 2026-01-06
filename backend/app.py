import os
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from extensions import db
from routes import auth, skills, lost_items, messages
from models import ChatSession, User, LostItem, Skill


def create_app(test_config=None):
    app = Flask(__name__, static_folder='static')
    app.json.ensure_ascii = False
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    #判断是否是测试模式
    if test_config:
        app.config.update(test_config)
    else:
        #否则用默认MySQL连接
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/campus_market?charset=utf8mb4'

    db.init_app(app)

    #注册原有蓝图
    app.register_blueprint(auth.bp, url_prefix='/api')
    app.register_blueprint(skills.bp, url_prefix='/api')
    app.register_blueprint(lost_items.bp, url_prefix='/api')
    app.register_blueprint(messages.bp, url_prefix='/api')


    inquiry_bp = Blueprint('inquiry', __name__)

    #详情页点击联系 创建或获取会话
    @inquiry_bp.route('/chat/start', methods=['POST'])
    def start_inquiry():
        data = request.json
        task_id = data.get('task_id')
        task_type = data.get('task_type')
        visitor_id = data.get('visitor_id')

        if not all([task_id, task_type, visitor_id]):
            return jsonify({'error': '缺少参数'}), 400

        #获取任务信息 确定发布者
        publisher_id = None
        if task_type == 'lost':
            item = LostItem.query.get(task_id)
            if item: publisher_id = item.user_id
        elif task_type == 'skill':
            item = Skill.query.get(task_id)
            if item: publisher_id = item.user_id

        if not publisher_id:
            return jsonify({'error': '任务不存在'}), 404

        if int(visitor_id) == int(publisher_id):
            return jsonify({'error': '不能联系自己发布的任务'}), 400

        #查找有没有旧会话
        filters = {
            'user_a_id': visitor_id,
            'user_b_id': publisher_id
        }
        if task_type == 'lost':
            filters['lost_item_id'] = task_id
        else:
            filters['skill_id'] = task_id

        session = ChatSession.query.filter_by(**filters).first()

        #不存在 创建
        if not session:
            session = ChatSession(
                user_a_id=visitor_id,
                user_b_id=publisher_id,
                lost_item_id=task_id if task_type == 'lost' else None,
                skill_id=task_id if task_type == 'skill' else None
            )
            db.session.add(session)
            db.session.commit()

        return jsonify({'session_id': session.id, 'publisher_id': publisher_id})

    #发布者点查看咨询 获取咨询者列表
    @inquiry_bp.route('/task/inquiries', methods=['GET'])
    def get_task_inquiries():
        task_id = request.args.get('task_id')
        task_type = request.args.get('task_type')

        if not task_id or not task_type:
            return jsonify([]), 400

        #查询该任务所有会话
        if task_type == 'lost':
            sessions = ChatSession.query.filter_by(lost_item_id=task_id).all()
        else:
            sessions = ChatSession.query.filter_by(skill_id=task_id).all()

        result = []
        for s in sessions:
            inquirer = s.user_a  #咨询者永远是user_a
            result.append({
                'session_id': s.id,
                'user_id': inquirer.id,
                'username': inquirer.username,
                'avatar': inquirer.avatar,
                'create_time': s.create_time.strftime('%Y-%m-%d %H:%M')
            })

        return jsonify(result)

    #辅助接口 获取用户所有发布任务的咨询数量
    @inquiry_bp.route('/user/task_inquiry_counts', methods=['GET'])
    def get_inquiry_counts():
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({}), 400

        #统计skill的咨询
        skill_counts = {}
        user_skills = Skill.query.filter_by(user_id=user_id).all()
        for sk in user_skills:
            count = ChatSession.query.filter_by(skill_id=sk.id).count()
            skill_counts[sk.id] = count

        #统计LostItem的咨询
        lost_counts = {}
        user_losts = LostItem.query.filter_by(user_id=user_id).all()
        for li in user_losts:
            count = ChatSession.query.filter_by(lost_item_id=li.id).count()
            lost_counts[li.id] = count

        return jsonify({
            'skill_counts': skill_counts,
            'lost_counts': lost_counts
        })

    #注册新蓝图
    app.register_blueprint(inquiry_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Campus Market API is running!"

    return app


if __name__ == '__main__':
    app = create_app()
    print("后端启动: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)