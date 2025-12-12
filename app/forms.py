# app/forms.py
from flask_wtf import FlaskForm  # 需安装 flask-wtf，若未安装会报错
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
class LoginForm(FlaskForm):
    """登录表单类（必须与视图函数中的导入名称一致）"""
    username = StringField(
        '用户名',  # 表单标签
        validators=[
            DataRequired(message='用户名不能为空'),  # 非空验证
            Length(min=3, max=20, message='用户名长度为3-20个字符')  # 长度验证
        ],
        render_kw={'class': 'form-control', 'placeholder': '请输入用户名'}  # 前端样式
    )
    password = PasswordField(
        '密码',
        validators=[
            DataRequired(message='密码不能为空'),
            Length(min=6, max=20, message='密码长度为6-20个字符')
        ],
        render_kw={'class': 'form-control', 'placeholder': '请输入密码'}
    )
    remember_me = BooleanField('记住我', default=True)  # 记住登录状态
    submit = SubmitField('登录', render_kw={'class': 'btn btn-primary'})