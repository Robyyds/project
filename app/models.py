from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:100000',
            salt_length=16
        )
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
class DynamicColumn(db.Model):
    __tablename__ = 'dynamic_columns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DynamicColumn {self.name}>'
class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_name = db.Column(db.String(200), nullable=False)
    sign_date = db.Column(db.Date, nullable=False)
    contract_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    contract_progress = db.Column(db.String(50), default='未开始', index=True)
    party_a = db.Column(db.String(100), nullable=False)
    party_b = db.Column(db.String(100), nullable=False)
    party_c = db.Column(db.String(100))
    project_amount = db.Column(db.Float, default=0.0)
    invoice_status = db.Column(db.String(50), default='未开具')
    payment_status = db.Column(db.String(50), default='未收款')
    supply_status = db.Column(db.String(50), default='未供货')
    acceptance_status = db.Column(db.String(50), default='未验收')
    maintenance_time = db.Column(db.Date)
    business_person = db.Column(db.String(100), index=True)
    project_manager = db.Column(db.String(100), index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义（修复点1：使用 back_populates 替代 backref）
    creator = db.relationship('User', backref='projects')
    notes = db.relationship('ProjectNote', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('ProjectFile', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    dynamic_values = db.relationship('ProjectDynamicValue', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.contract_name}>'
class ProjectNote(db.Model):
    __tablename__ = 'project_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    # 修复点2：删除重复的 content 字段（只保留一个）
    content = db.Column(db.Text, nullable=False)  # 保留此字段
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 修复点3：使用 back_populates 显式定义双向关系
    project = db.relationship('Project', back_populates='notes')  # 关联到 Project.notes
    author = db.relationship('User', backref='notes')  # 关联到 User.notes
    
    def __repr__(self):
        return f'<ProjectNote {self.id}>'
class ProjectFile(db.Model):
    __tablename__ = 'project_files'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    uploader = db.relationship('User', backref='files')
    
    def __repr__(self):
        return f'<ProjectFile {self.filename}>'
class ProjectDynamicValue(db.Model):
    __tablename__ = 'project_dynamic_values'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('dynamic_columns.id'), nullable=False)
    value_string = db.Column(db.String(500))
    value_integer = db.Column(db.Integer)
    value_date = db.Column(db.Date)
    value_boolean = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    column = db.relationship('DynamicColumn')
    
    @property
    def value(self):
        if self.column.data_type == 'string':
            return self.value_string
        elif self.column.data_type == 'integer':
            return self.value_integer
        elif self.column.data_type == 'date':
            return self.value_date
        elif self.column.data_type == 'boolean':
            return self.value_boolean
        return None
    @value.setter
    def value(self, val):
        if self.column.data_type == 'string':
            self.value_string = str(val) if val is not None else None
        elif self.column.data_type == 'integer':
            self.value_integer = int(val) if val is not None else None
        elif self.column.data_type == 'date':
            self.value_date = val if isinstance(val, datetime.date) else None
        elif self.column.data_type == 'boolean':
            self.value_boolean = bool(val) if val is not None else None
    
    def __repr__(self):
        return f'<ProjectDynamicValue {self.id}>'
