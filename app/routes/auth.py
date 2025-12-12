# 确保顶部导入以下模块
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required

# 在文件顶部添加（如果不存在）
from flask import Blueprint
auth_bp = Blueprint('auth', __name__)  # 定义蓝图（名称必须与导入一致）


from app import db
from app.models import User
from app.forms import LoginForm  # 关键：导入登录表单类
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. 如果已登录，重定向到首页（避免重复登录）
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # 确保 'main.index' 是首页路由
    
    # 2. 实例化登录表单（关键步骤：必须创建表单对象）
    form = LoginForm()  # 这里的 LoginForm 来自 app.forms.py
    
    # 3. 处理表单提交（POST 请求）
    if form.validate_on_submit():
        # 查询用户
        user = User.query.filter_by(username=form.username.data).first()
        # 验证用户和密码
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        # 登录用户
        login_user(user, remember=form.remember_me.data)
        # 处理跳转页面
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.index'))
    
    # 4. GET 请求：传递表单给模板（必须包含 form=form）
    return render_template('auth/login.html', title='登录', form=form)  # 关键：form=form

@auth_bp.route('/logout')  
@login_required
def logout():
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('main.index'))

