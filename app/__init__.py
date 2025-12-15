from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy  # 导入SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from flask_wtf.csrf import CSRFProtect  # 顶部新增
csrf = CSRFProtect()                   # 创建扩展实例
# 1. 先初始化数据库对象（关键：必须在导入路由前完成）
db = SQLAlchemy()  # 创建db对象，供其他模块导入
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 已存在
login_manager.login_message = '请先登录'  # 已存在
login_manager.login_message_category = 'info'  # 已存在

@login_manager.user_loader
def load_user(user_id):
    """根据用户ID加载用户（Flask-Login 必需）"""
    from app.models import User  # 导入User模型
    return User.query.get(int(user_id))  # 通过ID查询用户

migrate = Migrate()
def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    # 2. 初始化扩展（将db绑定到app）
    db.init_app(app)  # 这里才将db与app关联，不影响之前的导入
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    # 3. 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    # 4. 最后导入路由蓝图（关键：必须在db初始化后导入）
    from app.routes import main_bp, auth_bp, projects_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # 错误处理
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    return app
# 5. 确保db对象可被外部导入（重要）
__all__ = ['db', 'create_app']


