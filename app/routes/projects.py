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
from app.models import Project, ProjectNote, ProjectFile, DynamicColumn, ProjectDynamicValue
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
        flash('项目创建成功！', 'success')
        return redirect(url_for('projects.detail', id=project.id))
        try:
            db.session.add(project)
            db.session.commit()
            flash('项目创建成功！', 'success')
            return redirect(url_for('projects.index'))
        except IntegrityError:
            db.session.rollback()  # 回滚事务（避免事务锁定）
            flash(f'合同编号 {form.contract_number.data} 已存在，请更换编号', 'danger')        
            return redirect(url_for('projects.create'))

    return render_template('project_form.html', title='创建项目')
@projects_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑项目"""
    project = Project.query.get_or_404(id)
    
    if request.method == 'POST':
        project.contract_name = request.form.get('contract_name')
        project.sign_date = datetime.strptime(request.form.get('sign_date'), '%Y-%m-%d').date() if request.form.get('sign_date') else None
        project.contract_number = request.form.get('contract_number')
        project.contract_progress = request.form.get('contract_progress')
        project.party_a = request.form.get('party_a')
        project.party_b = request.form.get('party_b')
        project.party_c = request.form.get('party_c')
        project.project_amount = float(request.form.get('project_amount', 0))
        project.invoice_status = request.form.get('invoice_status')
        project.payment_status = request.form.get('payment_status')
        project.supply_status = request.form.get('supply_status')
        project.acceptance_status = request.form.get('acceptance_status')
        project.maintenance_time = datetime.strptime(request.form.get('maintenance_time'), '%Y-%m-%d').date() if request.form.get('maintenance_time') else None
        project.business_person = request.form.get('business_person')
        project.project_manager = request.form.get('project_manager')
        
        db.session.commit()
        flash('项目更新成功！', 'success')
        return redirect(url_for('projects.detail', id=project.id))
    
    return render_template('project_form.html', title='编辑项目', project=project)
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

@projects_bp.route('/<int:project_id>/add_note', methods=['POST'])  # 路由包含 project_id
@login_required  # 确保登录用户才能添加备注
def add_note(project_id):  # 接受 project_id 参数
    # 1. 获取表单提交的备注内容（与模板中 textarea 的 name="content" 对应）
    """添加项目备注（对应模板中的 add_note 端点）"""
    content = request.form.get('content', '').strip()
    if not content:
        flash('备注内容不能为空', 'danger')
        return redirect(url_for('projects.detail', id=project_id))  # 重定向回项目详情页
        # 2. 验证项目是否存在
    project = Project.query.get_or_404(project_id)  # 如项目不存在返回 404
            # 3. 创建备注记录（假设 ProjectNote 模型存在，关联 project_id 和 author_id）
    note = ProjectNote(
        content=content,
        project_id=project_id,  # 关联到当前项目
        created_by=current_user.id  # 关联到当前登录用户（需确保 current_user 已导入）
    )
        
        # 4. 保存到数据库并处理异常
    try:
        db.session.add(note)
        db.session.commit()
        flash('备注添加成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'添加备注失败：{str(e)}', 'danger')

        
            # 5. 重定向回项目详情页
    return redirect(url_for('projects.detail', id=project_id))
# 辅助函数：检查文件类型是否允许上传
def allowed_file(filename):
    allowed_extensions = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in allowed_extensions

@projects_bp.route('/<int:project_id>/upload_file', methods=['POST'])  # 路由包含 project_id
@login_required  # 确保登录用户才能上传
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)
    if 'file' not in request.files:
        flash('未选择文件', 'danger')
        return redirect(url_for('projects.detail', id=project_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件', 'danger')
        return redirect(url_for('projects.detail', id=project_id))
    
        # 3. 验证文件类型和保存文件
    if file and allowed_file(file.filename):  # 需定义 allowed_file 函数（见下文）
                        # 安全处理文件名（避免特殊字符）
        filename = secure_filename(file.filename)
        # 生成存储路径（确保目录存在）
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'projects', str(project_id))
        os.makedirs(upload_folder, exist_ok=True)  # 自动创建不存在的目录
                # 保存文件到服务器
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
                # 4. 记录文件信息到数据库（ProjectFile 模型）
        new_file = ProjectFile(
            project_id=project_id,
            filename=filename,
            original_filename=file.filename,  # 保留原始文件名
            file_type=request.form.get('file_type', 'other'),  # 从表单获取文件类型（如 contract/acceptance）

            file_path=file_path,
            uploaded_by=current_user.id  # 上传者 ID（当前登录用户）
        )
        db.session.add(new_file)
        db.session.commit()
        
        flash('文件上传成功！', 'success')
    else:
        flash('不支持的文件类型', 'danger')
                                    
    # 5. 重定向回项目详情页
    return redirect(url_for('projects.detail', id=project_id))

@projects_bp.route('/files/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """删除项目文件（修复端点缺失错误）"""
    # 1. 查询文件记录
    file = ProjectFile.query.get_or_404(file_id)
    project_id = file.project_id  # 获取关联的项目ID
    
    try:
        # 2. 删除服务器上的文件
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
        
        # 3. 删除数据库记录
        db.session.delete(file)
        db.session.commit()
        flash('文件已成功删除', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    # 4. 重定向回项目详情页
    return redirect(url_for('projects.detail', id=project_id))
