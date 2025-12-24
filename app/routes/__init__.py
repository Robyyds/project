from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from flask_wtf.csrf import CSRFProtect
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.projects import projects_bp
from app.routes.admin import admin_bp

__all__ = ['main_bp', 'auth_bp', 'projects_bp', 'admin_bp']
# 初始化扩展，但不在这里导入蓝图
csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    """应用工厂函数"""
    # 创建 Flask 应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # 登录管理器配置
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    # 清空现有的蓝图注册（如果存在）
    app.blueprints = {}
    
    # 注册蓝图 - 使用延迟导入避免循环导入
    register_blueprints(app)
    
    # 错误处理
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """注册所有蓝图"""
    # 注意：这里使用绝对导入，避免循环导入问题
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.admin import admin_bp
    
    # 检查是否已经注册过（防止重复注册）
    if 'main_bp' not in app.blueprints:
        app.register_blueprint(main_bp)
    
    if 'auth_bp' not in app.blueprints:
        app.register_blueprint(auth_bp, url_prefix='/auth')
    
    if 'projects_bp' not in app.blueprints:
        # 确保只有一个蓝图实例
        app.register_blueprint(projects_bp, url_prefix='/projects')
    
    if 'admin_bp' not in app.blueprints:
        app.register_blueprint(admin_bp, url_prefix='/admin')

def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500
