from datetime import datetime
from extensions import db


#用户表
#存账号信息和积分
#==============================================
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    #用户名唯一，防止重复注册
    username = db.Column(db.String(50), nullable=False, unique=True)

    #目前是明文，后期要改PBKDF2 Argon2加密
    password = db.Column(db.String(50), nullable=False)

    #联系方式
    contact = db.Column(db.String(100), nullable=False)

    #注册默认10分
    points = db.Column(db.Integer, default=10)

    #用户头像URL
    avatar = db.Column(db.String(500))

    #数据库关系定义
    #backref='author' #通过skill.author直接拿到对应User
    #lazy=True #只有用到时才加载
    skills = db.relationship('Skill', backref='author', lazy=True, foreign_keys='Skill.user_id')
    lost_items = db.relationship('LostItem', backref='author', lazy=True, foreign_keys='LostItem.user_id')


#会话表 交易前咨询，关联User和具体物品/技能
#==========================
class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)

    #咨询者
    user_a_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    #发布者
    user_b_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #关联物品
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'), nullable=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)

    create_time = db.Column(db.DateTime, default=datetime.now)

    #建立关系    方便查询
    messages = db.relationship('Message', backref='session', lazy=True)

    #方便拿到User对象
    user_a = db.relationship('User', foreign_keys=[user_a_id])
    user_b = db.relationship('User', foreign_keys=[user_b_id])


#消息表
#=======================
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)

    #关联会话ID
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=True)

    #发送者 接收者 关联到User表的id
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #聊天内容 文本 如果是图片存为image:URL格式
    content = db.Column(db.String(500), nullable=False)

    #按时间排序聊天记录用
    create_time = db.Column(db.DateTime, default=datetime.now)


#失物招领表
#===================================================
class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text)  #详细描述
    location = db.Column(db.String(100))  #丢失/拾取地点

    #0丢东西, 1捡到东西
    type = db.Column(db.Integer, default=0)

    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)

    #发布人ID (外键)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #status: 0 = 待接单 广场可见
    #        1 = 进行中 已被接单，锁定
    #        2 = 已完成 双方确认，结算积分
    status = db.Column(db.Integer, default=0)

    #接单人ID
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    #0=未评, 1=好评+2分, 2=差评-2分
    poster_review = db.Column(db.Integer, default=0)  #发布者评价
    helper_review = db.Column(db.Integer, default=0)  #接单者评价

    #建立与User表的关系，方便查helper信息
    helper = db.relationship('User', foreign_keys=[helper_id])


#技能互助表
#===============================================
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    #报酬/代价
    cost = db.Column(db.String(100), nullable=False)

    #1提供技能, 2求助
    type = db.Column(db.Integer, default=1)

    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)

    #发布人
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #0待接单, 1进行中, 2已完成
    status = db.Column(db.Integer, default=0)

    #接单人
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    #评价状态
    poster_review = db.Column(db.Integer, default=0)
    helper_review = db.Column(db.Integer, default=0)

    #关联接单人信息
    helper = db.relationship('User', foreign_keys=[helper_id])