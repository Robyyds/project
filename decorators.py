from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
def admin_required(f):
    """验证管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 未登录用户重定向到登录页
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        # 非管理员用户拒绝访问
        if not current_user.is_admin:
            flash('您没有权限访问此页面', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
