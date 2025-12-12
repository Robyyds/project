from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user  # ✅ 导入 current_user
from sqlalchemy import func  # ✅ 导入 func
from app import db
from app.models import User, DynamicColumn, Project  # ✅ 导入 Project（dashboard用）
from app.utils.decorators import admin_required
admin_bp = Blueprint('admin', __name__)
# ---------------------- 动态列管理 ----------------------
@admin_bp.route('/columns', methods=['GET', 'POST'])  # ✅ 支持 GET/POST
@login_required
@admin_required
def columns():
    """列管理列表页"""
    columns = DynamicColumn.query.order_by(DynamicColumn.created_at.desc()).all()
    return render_template('admin/columns.html', title='列管理', columns=columns)
@admin_bp.route('/columns/add', methods=['POST'])  # 处理添加列表单
@login_required
@admin_required
def add_column():
    """添加动态列"""
    name = request.form.get('name', '').strip()
    data_type = request.form.get('data_type', 'string')
    
    if not name:
        flash('列名称不能为空', 'danger')
        return redirect(url_for('admin.columns'))
    
    if DynamicColumn.query.filter_by(name=name).first():
        flash(f'列名称 "{name}" 已存在', 'danger')
        return redirect(url_for('admin.columns'))
    
    new_column = DynamicColumn(name=name, data_type=data_type, is_active=True)
    db.session.add(new_column)
    db.session.commit()
    flash('动态列添加成功', 'success')
    return redirect(url_for('admin.columns'))
@admin_bp.route('/columns/edit/<int:column_id>', methods=['GET', 'POST'])  # ✅ 参数名 column_id
@login_required
@admin_required
def edit_column(column_id):
    """编辑动态列"""
    column = DynamicColumn.query.get_or_404(column_id)
    
    if request.method == 'POST':
        column.name = request.form.get('name', '').strip()
        column.data_type = request.form.get('data_type', 'string')
        column.is_active = 'is_active' in request.form
        
        if not column.name:
            flash('列名称不能为空', 'danger')
            return redirect(url_for('admin.edit_column', column_id=column_id))
        
        db.session.commit()
        flash('列更新成功！', 'success')
        return redirect(url_for('admin.columns'))
    
    return render_template('admin/column_form.html', title='编辑列', column=column)
@admin_bp.route('/columns/toggle/<int:column_id>', methods=['POST'])  # ✅ 参数名 column_id
@login_required
@admin_required
def toggle_column(column_id):
    """切换列激活状态"""
    column = DynamicColumn.query.get_or_404(column_id)
    column.is_active = not column.is_active
    db.session.commit()
    status = '激活' if column.is_active else '停用'
    flash(f'列已{status}', 'success')
    return redirect(url_for('admin.columns'))
@admin_bp.route('/columns/delete/<int:column_id>', methods=['POST'])  # ✅ 参数名 column_id
@login_required
@admin_required
def delete_column(column_id):
    """删除动态列"""
    column = DynamicColumn.query.get_or_404(column_id)
    db.session.delete(column)
    db.session.commit()
    flash('列已删除', 'success')
    return redirect(url_for('admin.columns'))
# ---------------------- 用户管理 ----------------------
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """用户管理列表页"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', title='用户管理', users=users)
@admin_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """添加用户"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    is_admin = 'is_admin' in request.form
    
    if not all([username, email, password]):
        flash('用户名、邮箱和密码不能为空', 'danger')
        return redirect(url_for('admin.users'))
    
    if User.query.filter_by(username=username).first():
        flash(f'用户名 "{username}" 已存在', 'danger')
        return redirect(url_for('admin.users'))
    
    if User.query.filter_by(email=email).first():
        flash(f'邮箱 "{email}" 已存在', 'danger')
        return redirect(url_for('admin.users'))
    
    new_user = User(username=username, email=email, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('用户添加成功', 'success')
    return redirect(url_for('admin.users'))
@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    if user_id == current_user.id:  # ✅ current_user 已导入
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除', 'success')
    return redirect(url_for('admin.users'))
# ---------------------- 其他管理功能 ----------------------
@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """操作日志页面"""
    return render_template('admin/logs.html', title='操作日志')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """管理员仪表盘"""
    total_projects = Project.query.count()
    total_amount = db.session.query(func.sum(Project.project_amount)).scalar() or 0  # ✅ func 已导入
    total_columns = DynamicColumn.query.count()
    total_users = User.query.count()
    return render_template('admin/dashboard.html',
                         total_projects=total_projects,
                         total_amount=total_amount,
                         total_columns=total_columns,
                         total_users=total_users)
