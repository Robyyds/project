from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask import current_app
import os
import uuid
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from app import db
from app.models import Project, ProjectNote, ProjectFile, DynamicColumn, ProjectDynamicValue, ProjectStep
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError


projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/list', methods=['GET'])
@login_required
def list():
    """项目列表页面"""
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('projects/list.html', title='项目列表', projects=projects, pagination=projects)

@projects_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    """项目详情页"""
    project = Project.query.get_or_404(id)
    notes = project.notes.order_by(ProjectNote.created_at.desc()).all()
    contract_files = project.files.filter_by(file_type='contract').all()
    acceptance_files = project.files.filter_by(file_type='acceptance').all()
    other_files = project.files.filter_by(file_type='other').all()
    
    return render_template('project_detail.html',
                         title=project.contract_name,
                         project=project,
                         notes=notes,
                         contract_files=contract_files,
                         acceptance_files=acceptance_files,
                         other_files=other_files)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建新项目"""
    if request.method == 'POST':
        try:
            project = Project(
                contract_name=request.form.get('contract_name'),
                sign_date=datetime.strptime(request.form.get('sign_date'), '%Y-%m-%d').date() if request.form.get('sign_date') else None,
                contract_number=request.form.get('contract_number'),
                contract_progress=request.form.get('contract_progress', '未开始'),
                party_a=request.form.get('party_a'),
                party_b=request.form.get('party_b'),
                party_c=request.form.get('party_c'),
                project_amount=float(request.form.get('project_amount', 0)),
                invoice_status=request.form.get('invoice_status', '未开具'),
                payment_status=request.form.get('payment_status', '未收款'),
                supply_status=request.form.get('supply_status', '未供货'),
                acceptance_status=request.form.get('acceptance_status', '未验收'),
                maintenance_time=datetime.strptime(request.form.get('maintenance_time'), '%Y-%m-%d').date() if request.form.get('maintenance_time') else None,
                business_person=request.form.get('business_person'),
                project_manager=request.form.get('project_manager')
            )
            db.session.add(project)
            db.session.commit()
            
            # 添加默认步骤
            default_steps = [
                ('项目启动', True),
                ('项目验收', False),
                ('验收回款', False)
            ]
            for i, (title, is_completed) in enumerate(default_steps):
                step = ProjectStep(
                    project_id=project.id,
                    title=title,
                    is_completed=is_completed,
                    is_fixed=True,
                    order=i
                )
                db.session.add(step)
            
            db.session.commit()
            flash('项目创建成功！', 'success')
            return redirect(url_for('projects.detail', id=project.id))
        except IntegrityError as e:
            db.session.rollback()
            if 'contract_number' in str(e.orig):
                flash(f'合同编号「{request.form.get("contract_number")}」已存在，请更换', 'danger')
            else:
                flash('数据冲突，请检查输入', 'danger')
            return redirect(url_for('projects.create'))

    return render_template('project_form.html', title='创建项目', project=None)

@projects_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑项目 - 仅编辑时允许合同号相同（方案 A 修正版）"""
    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        new_number = request.form.get('contract_number', '').strip()

        # 1. 检查新编号是否被其他项目占用（排除当前项目）
        if new_number != project.contract_number:  # 只有合同编号改变时才检查
            existing = Project.query.filter(
                Project.contract_number == new_number,
                Project.id != id
            ).first()
            if existing:
                flash(f'合同编号「{new_number}」已被其他项目使用，请更换', 'warning')
                return render_template('project_form.html', project=project, title='编辑项目')

        # 2. 更新项目信息（包含合同编号）
        try:
            project.contract_name = request.form.get('contract_name')
            if request.form.get('sign_date'):
                project.sign_date = datetime.strptime(request.form.get('sign_date'), '%Y-%m-%d').date()
            project.contract_number = new_number  # 更新合同编号
            project.contract_progress = request.form.get('contract_progress')
            project.party_a = request.form.get('party_a')
            project.party_b = request.form.get('party_b')
            project.party_c = request.form.get('party_c') or None
            project.project_amount = float(request.form.get('project_amount', 0))
            project.invoice_status = request.form.get('invoice_status')
            project.payment_status = request.form.get('payment_status')
            project.supply_status = request.form.get('supply_status')
            project.acceptance_status = request.form.get('acceptance_status')
            if request.form.get('maintenance_time'):
                project.maintenance_time = datetime.strptime(request.form.get('maintenance_time'), '%Y-%m-%d').date()
            else:
                project.maintenance_time = None
            project.business_person = request.form.get('business_person') or None
            project.project_manager = request.form.get('project_manager') or None

            db.session.commit()
            flash('项目更新成功！', 'success')
            return redirect(url_for('projects.detail', id=project.id))
            
        except IntegrityError as e:
            db.session.rollback()
            if 'contract_number' in str(e.orig):
                flash(f'合同编号「{new_number}」已存在，请更换', 'danger')
            else:
                flash('数据冲突，请检查输入', 'danger')
            return render_template('project_form.html', project=project, title='编辑项目')

    # GET 回显
    return render_template('project_form.html', project=project, title='编辑项目')

@projects_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """删除项目"""
    project = Project.query.get_or_404(id)
    if not current_user.is_admin and project.created_by != current_user.id:
        flash('无权删除他人项目', 'warning')
        return redirect(url_for('projects.list'))
    
    try:
        # 1. 清理关联文件
        project_files = ProjectFile.query.filter_by(project_id=id).all()  # 使用 id 筛选
        for file in project_files:
            file_path = os.path.join(
                current_app.root_path, 
                'static', 'uploads', 'projects', 
                str(id), file.filename  # 使用 id 构建路径
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(file)
        
        # 2. 删除项目记录
        db.session.delete(project)
        db.session.commit()
        flash(f'项目「{project.contract_name}」已成功删除', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('projects.list'))

@projects_bp.route('/import_excel', methods=['GET', 'POST'])
@login_required
def import_excel():
    """Excel导入项目"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('请选择文件', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('请选择文件', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            try:
                excel_data = pd.read_excel(BytesIO(file.read()))
                
                required_columns = ['合同项目', '签订日期', '合同编号', '甲方', '乙方']
                missing_columns = [col for col in required_columns if col not in excel_data.columns]
                if missing_columns:
                    flash(f'Excel文件缺少必需列: {", ".join(missing_columns)}', 'danger')
                    return redirect(request.url)
                
                success_count = 0
                error_count = 0
                errors = []
                
                for index, row in excel_data.iterrows():
                    try:
                        existing_project = Project.query.filter_by(
                            contract_number=str(row['合同编号'])
                        ).first()
                        if existing_project:
                            errors.append(f"第{index+2}行: 合同编号 {row['合同编号']} 已存在")
                            error_count += 1
                            continue
                        
                        project = Project(
                            contract_name=str(row['合同项目']),
                            sign_date=pd.to_datetime(row['签订日期']).date() if pd.notna(row['签订日期']) else None,
                            contract_number=str(row['合同编号']),
                            contract_progress=str(row.get('合同进度', '未开始')),
                            party_a=str(row['甲方']),
                            party_b=str(row['乙方']),
                            party_c=str(row.get('丙方', '')) if pd.notna(row.get('丙方')) else None,
                            project_amount=float(row.get('项目金额', 0)) if pd.notna(row.get('项目金额')) else 0.0,
                            invoice_status=str(row.get('发票开具情况', '未开具')),
                            payment_status=str(row.get('收款情况', '未收款')),
                            supply_status=str(row.get('供货情况', '未供货')),
                            acceptance_status=str(row.get('验收情况', '未验收')),
                            maintenance_time=pd.to_datetime(row.get('维保时间')).date() if pd.notna(row.get('维保时间')) else None,
                            business_person=str(row.get('商务人员', '')) if pd.notna(row.get('商务人员')) else None,
                            project_manager=str(row.get('项目负责人', '')) if pd.notna(row.get('项目负责人')) else None
                        )
                        db.session.add(project)
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"第{index+2}行: {str(e)}")
                        error_count += 1
                
                db.session.commit()
                
                if success_count > 0:
                    flash(f'成功导入 {success_count} 个项目', 'success')
                if error_count > 0:
                    flash(f'导入失败 {error_count} 个项目', 'danger')
                    for error in errors[:5]:
                        flash(error, 'warning')
                
                return redirect(url_for('main.index'))
                
            except Exception as e:
                flash(f'处理Excel文件时出错: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('请上传Excel文件 (.xlsx 或 .xls)', 'danger')
            return redirect(request.url)
    
    return render_template('import_excel.html', title='Excel导入')

@projects_bp.route('/export_excel')
@login_required
def export_excel():
    """导出项目数据为Excel"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    
    data = []
    headers = [
        '合同项目', '签订日期', '合同编号', '合同进度', '甲方', '乙方', '丙方',
        '项目金额', '发票开具情况', '收款情况', '供货情况', '验收情况',
        '维保时间', '商务人员', '项目负责人'
    ]
    data.append(headers)
    
    for project in projects:
        row = [
            project.contract_name,
            project.sign_date.strftime('%Y-%m-%d') if project.sign_date else '',
            project.contract_number,
            project.contract_progress,
            project.party_a,
            project.party_b,
            project.party_c or '',
            project.project_amount,
            project.invoice_status,
            project.payment_status,
            project.supply_status,
            project.acceptance_status,
            project.maintenance_time.strftime('%Y-%m-%d') if project.maintenance_time else '',
            project.business_person or '',
            project.project_manager or ''
        ]
        data.append(row)
    
    df = pd.DataFrame(data[1:], columns=data[0])
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        df.to_excel(tmp.name, index=False, engine='openpyxl')
        return send_file(tmp.name, as_attachment=True, 
                        download_name=f'项目数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@projects_bp.route('/<int:project_id>/add_note', methods=['POST'])
@login_required
def add_note(project_id):
    """添加项目备注（对应模板中的 add_note 端点）"""
    content = request.form.get('content', '').strip()
    if not content:
        flash('备注内容不能为空', 'danger')
        return redirect(url_for('projects.detail', id=project_id))
    
    project = Project.query.get_or_404(project_id)
    
    note = ProjectNote(
        content=content,
        project_id=project_id,
        created_by=current_user.id
    )
    
    try:
        db.session.add(note)
        db.session.commit()
        flash('备注添加成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'添加备注失败：{str(e)}', 'danger')
    
    return redirect(url_for('projects.detail', id=project_id))

# 辅助函数：检查文件类型是否允许上传
def allowed_file(filename):
    allowed_extensions = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in allowed_extensions

@projects_bp.route('/<int:project_id>/upload_file', methods=['POST'])
@login_required
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)
    if 'file' not in request.files:
        flash('未选择文件', 'danger')
        return redirect(url_for('projects.detail', id=project_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件', 'danger')
        return redirect(url_for('projects.detail', id=project_id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'projects', str(project_id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        new_file = ProjectFile(
            project_id=project_id,
            filename=filename,
            original_filename=file.filename,
            file_type=request.form.get('file_type', 'other'),
            file_path=file_path,
            uploaded_by=current_user.id
        )
        db.session.add(new_file)
        db.session.commit()
        
        flash('文件上传成功！', 'success')
    else:
        flash('不支持的文件类型', 'danger')
    
    return redirect(url_for('projects.detail', id=project_id))

@projects_bp.route('/files/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """删除项目文件（修复端点缺失错误）"""
    file = ProjectFile.query.get_or_404(file_id)
    project_id = file.project_id
    
    try:
        file_path = os.path.join(
            current_app.root_path, 
            'static', 
            'uploads', 
            'projects', 
            str(project_id), 
            file.filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(file)
        db.session.commit()
        flash('文件已成功删除', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('projects.detail', id=project_id))

# ================ 项目进度管理路由（只保留一份） ================

@projects_bp.route('/<int:project_id>/steps', methods=['GET'])
@login_required
def get_steps(project_id):
    """获取项目步骤"""
    steps = ProjectStep.query.filter_by(project_id=project_id).order_by(ProjectStep.order).all()
    return jsonify([{
        'id': step.id,
        'title': step.title,
        'is_completed': step.is_completed,
        'is_fixed': step.is_fixed
    } for step in steps])

@projects_bp.route('/<int:project_id>/progress', methods=['GET'])
@login_required
def get_progress(project_id):
    """获取项目进度"""
    total_steps = ProjectStep.query.filter_by(project_id=project_id).count()
    completed_steps = ProjectStep.query.filter_by(project_id=project_id, is_completed=True).count()
    
    percent = 0
    if total_steps > 0:
        percent = int((completed_steps / total_steps) * 100)
    
    return jsonify({
        'total': total_steps,
        'completed': completed_steps,
        'percent': percent
    })

@projects_bp.route('/<int:project_id>/steps/add', methods=['POST'])
@login_required
def add_step(project_id):
    """添加项目步骤"""
    title = request.form.get('title', '').strip()
    if not title:
        return jsonify({'error': '步骤标题不能为空'}), 400
    
    try:
        max_order = db.session.query(db.func.max(ProjectStep.order)).filter_by(project_id=project_id).scalar() or 0
        
        step = ProjectStep(
            project_id=project_id,
            title=title,
            is_fixed=False,
            order=max_order + 1
        )
        db.session.add(step)
        db.session.commit()
        
        return jsonify({'success': True, 'id': step.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/steps/toggle/<int:step_id>', methods=['POST'])
@login_required
def toggle_step(step_id):
    """切换步骤完成状态"""
    step = ProjectStep.query.get_or_404(step_id)
    
    try:
        step.is_completed = not step.is_completed
        db.session.commit()
        return jsonify({'success': True, 'is_completed': step.is_completed})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        
@projects_bp.route('/steps/<int:step_id>', methods=['DELETE'])
@login_required
def delete_step(step_id):
    step = ProjectStep.query.get_or_404(step_id)
    # 1. 内置保护：标题为「项目验收完成」不可删
    if step.title == '项目验收完成':
        return jsonify({'error': '系统固定步骤，不可删除'}), 403

    # 2. 简单权限：只有创建人或管理员可删，自行扩展
    if step.creator_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '无权删除'}), 403

    project_id = step.project_id
    try:
        db.session.delete(step)
        db.session.commit()
        # 3. 重新计算进度
        ProjectStep.recalc_progress(project_id)   # 见下方模型方法
        return jsonify({'result': 'ok'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(e)
        return jsonify({'error': '删除失败'}), 500
        
@projects_bp.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta

    now = datetime.now()

    # 1. 顶部卡片数据
    total_projects   = Project.query.count()
    total_amount     = db.session.query(func.sum(Project.project_amount)).scalar() or 0
    upcoming_maint   = Project.query.filter(
                            Project.maintenance_time.between(
                                now.date(),
                                now.date() + timedelta(days=30)
                            )).all()
    payment_kinds    = db.session.query(Project.payment_status).distinct().all()

    # 2. 图表数据
    progress_stats = db.session.query(
                        Project.contract_progress,
                        func.count(Project.id).label('count')
                     ).group_by(Project.contract_progress).all()

    year_stats = db.session.query(
                    extract('year', Project.sign_date).label('year'),
                    func.count(Project.id).label('count')
                 ).filter(Project.sign_date >= now.replace(year=now.year-4, month=1, day=1))\
                  .group_by('year').order_by('year').all()

    month_stats = db.session.query(
                    extract('month', Project.sign_date).label('month'),
                    func.count(Project.id).label('count')
                  ).filter(extract('year', Project.sign_date) == now.year)\
                   .group_by('month').order_by('month').all()

    payment_stats = db.session.query(
                        Project.payment_status,
                        func.sum(Project.project_amount).label('amount')
                      ).group_by(Project.payment_status).all()

    return render_template('dashboard.html',
                           total_projects=total_projects,
                           total_amount=total_amount,
                           upcoming_maintenance=upcoming_maint,
                           payment_stats=payment_stats,
                           progress_stats=progress_stats,
                           year_stats=year_stats,
                           month_stats=month_stats,
                           now=now)