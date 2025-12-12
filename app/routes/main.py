from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app import db
from app.models import Project
# 定义蓝图（避免重复定义）
main_bp = Blueprint('main', __name__)
@main_bp.route('/')
@login_required
def index():
    """首页 - 项目列表"""
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('index.html', 
                         title='项目列表',
                         projects=projects,
                         pagination=projects)
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """数据仪表盘（修复返回响应）"""
    now = datetime.now()
    # 基础统计
    total_projects = Project.query.count()
    total_amount = db.session.query(func.sum(Project.project_amount)).scalar() or 0
    
    # 按状态统计
    progress_stats = db.session.query(
        Project.contract_progress,
        func.count(Project.id).label('count')
    ).group_by(Project.contract_progress).all()
    
    # 按年份统计项目数量
    year_stats = db.session.query(
        extract('year', Project.sign_date).label('year'),
        func.count(Project.id).label('count')
    ).group_by(extract('year', Project.sign_date)).order_by('year').all()
    
    # 按月份统计（当前年）
    current_year = datetime.now().year
    month_stats = db.session.query(
        extract('month', Project.sign_date).label('month'),
        func.count(Project.id).label('count')
    ).filter(
        extract('year', Project.sign_date) == current_year
    ).group_by(extract('month', Project.sign_date)).order_by('month').all()
    
    # 收款统计
    payment_stats = db.session.query(
        Project.payment_status,
        func.count(Project.id).label('count'),
        func.sum(Project.project_amount).label('amount')
    ).group_by(Project.payment_status).all()
    
    # 即将到期的维保项目（30天内）
    upcoming_maintenance = Project.query.filter(
        Project.maintenance_time.isnot(None),
        Project.maintenance_time <= datetime.now().date() + timedelta(days=30),
        Project.maintenance_time >= datetime.now().date()
    ).order_by(Project.maintenance_time).all()
    
    # ✅ 关键修复：返回模板响应（传递所有统计数据）
    return render_template('dashboard.html',
        title='数据仪表盘',
        total_projects=total_projects,
        total_amount=total_amount,
        progress_stats=progress_stats,
        year_stats=year_stats,
        month_stats=month_stats,
        payment_stats=payment_stats,
        upcoming_maintenance=upcoming_maintenance,
        current_year=current_year,
        now=now
    )
