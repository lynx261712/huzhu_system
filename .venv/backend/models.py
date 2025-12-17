from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


#用户表 积分
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)  
    password = db.Column(db.String(50), nullable=False) 
    contact = db.Column(db.String(100), nullable=False)  #联系方式
    points = db.Column(db.Integer, default=10)  #初始10分

 
    skills = db.relationship('Skill', backref='author', lazy=True)
    lost_items = db.relationship('LostItem', backref='author', lazy=True)


#失物招领
class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False) 
    desc = db.Column(db.Text)  #描述
    location = db.Column(db.String(100))  #地点

    #0丢东西 1捡到了
    type = db.Column(db.Integer, default=0)

    #0进行中 1已认领
    status = db.Column(db.Integer, default=0)

    image = db.Column(db.String(500)) 
    create_time = db.Column(db.DateTime, default=datetime.now)

 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


#技能
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.String(100), nullable=False)  #代价

    #1我能提供 2我急需
    type = db.Column(db.Integer, default=1)

    #0开放中 1锁定 2完成
    status = db.Column(db.Integer, default=0)

    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)


    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


#交易记录
class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)

    #发起
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    target_id = db.Column(db.Integer)
    target_type = db.Column(db.String(20))  

    #积分
    point_change = db.Column(db.Integer, default=0)

    create_time = db.Column(db.DateTime, default=datetime.now)