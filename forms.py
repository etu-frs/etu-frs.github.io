from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, BooleanField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])

class TestimonialForm(FlaskForm):
    name = StringField('الاسم', validators=[DataRequired(), Length(min=2, max=100)])
    company = StringField('الشركة', validators=[Optional(), Length(max=100)])
    content = TextAreaField('التعليق', validators=[DataRequired(), Length(min=10, max=1000)])
    rating = IntegerField('التقييم', validators=[NumberRange(min=1, max=5)], default=5)

class ContentForm(FlaskForm):
    section_id = HiddenField('القسم', validators=[DataRequired()])
    key = StringField('المفتاح', validators=[DataRequired()])
    value = TextAreaField('القيمة', validators=[Optional()])

class ProfileForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    current_password = PasswordField('كلمة المرور الحالية', validators=[Optional()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[Optional(), Length(min=6)])

class ImageUploadForm(FlaskForm):
    image = FileField('الصورة', validators=[DataRequired()])
    section = HiddenField('القسم', validators=[DataRequired()])
    key = HiddenField('المفتاح', validators=[DataRequired()])
