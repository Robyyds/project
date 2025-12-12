from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, IntegerField, SelectField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User
class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')
class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('该用户名已被使用')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('该邮箱已被注册')
class DynamicColumnForm(FlaskForm):
    """动态列表单"""
    name = StringField('列名', validators=[DataRequired(), Length(max=100)])
    data_type = SelectField('数据类型', choices=[
        ('string', '文本'),
        ('integer', '整数'),
        ('date', '日期'),
        ('boolean', '布尔值')
    ], validators=[DataRequired()])
    submit = SubmitField('提交')
