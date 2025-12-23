import os
from flask import Flask
from flask_cors import CORS
from extensions import db
from routes import auth, skills, lost_items

def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    CORS(app)

    #数据库
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(app)
    #注册
    app.register_blueprint(auth.bp, url_prefix='/api')
    app.register_blueprint(skills.bp, url_prefix='/api')
    app.register_blueprint(lost_items.bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    print("后端启动: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)