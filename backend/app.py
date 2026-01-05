import os
from flask import Flask
from flask_cors import CORS
from extensions import db
from routes import auth, skills, lost_items, messages
#
def create_app(test_config=None):
    # 1. 明确指定 static 文件夹为当前目录下的 'static'
    app = Flask(__name__, static_folder='static')
    app.json.ensure_ascii = False
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 2. 【关键修改】判断是否是测试模式
    if test_config:
        # 如果传入了测试配置，就用测试的配置 (比如连接 SQLite)
        app.config.update(test_config)
    else:
        # 否则，使用默认的 MySQL 连接
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/campus_market?charset=utf8mb4'

    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth.bp, url_prefix='/api')
    app.register_blueprint(skills.bp, url_prefix='/api')
    app.register_blueprint(lost_items.bp, url_prefix='/api')
    app.register_blueprint(messages.bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Campus Market API is running!"

    return app

if __name__ == '__main__':
    app = create_app()
    print("后端启动: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)