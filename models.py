from datetime import datetime
from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    
    contents = db.relationship('Content', backref='section', lazy=True, cascade="all, delete-orphan")
    images = db.relationship('Image', backref='section', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Section {self.name}>'

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        db.UniqueConstraint('section_id', 'key', name='uix_content_section_key'),
    )
    
    def __repr__(self):
        return f'<Content {self.section.name}.{self.key}>'

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Testimonial by {self.name}>'

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Image {self.filename}>'

class PortfolioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    comments = db.relationship('PortfolioComment', backref='portfolio_item', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('PortfolioLike', backref='portfolio_item', lazy=True, cascade="all, delete-orphan")
    
    def increment_views(self):
        self.views_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<PortfolioItem {self.title}>'

class PortfolioComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<PortfolioComment {self.id}>'

class PortfolioLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    user_ip = db.Column(db.String(45), nullable=False)  # IPv6 can be up to 45 chars
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('portfolio_id', 'user_ip', name='uix_like_portfolio_ip'),
    )
    
    def __repr__(self):
        return f'<PortfolioLike {self.id}>'
