import pytest
import sys
import os

#获取当前文件目录
current_dir = os.path.dirname(os.path.abspath(__file__))
#指向backend
backend_path = os.path.join(os.path.dirname(current_dir), 'backend')
#加入系统路径
sys.path.insert(0, backend_path)

from app import create_app
from extensions import db
from models import User, Skill


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        #基础测试用户
        u1 = User(username="admin", password="123", contact="110", points=10)
        u2 = User(username="helper", password="123", contact="120", points=10)
        db.session.add_all([u1, u2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    #模拟浏览器，发请求
    return app.test_client()