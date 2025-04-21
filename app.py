import os
from datetime import datetime, timedelta
import json

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import base64

from email_service import send_contact_form_notification

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///website.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# Make sure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import User, Section, Content, Testimonial, Image, PortfolioItem, PortfolioComment, PortfolioLike
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(admin)
        
        # Add default sections if there are none
        if Section.query.count() == 0:
            sections = [
                Section(name="hero", title="معرض أعمال فراس"),
                Section(name="about", title="من أنا؟"),
                Section(name="services", title="الخدمات"),
                Section(name="portfolio", title="معرض الأعمال"),
                Section(name="testimonials", title="آراء العملاء"),
                Section(name="contact", title="تواصل معي")
            ]
            db.session.add_all(sections)
        
        db.session.commit()
        app.logger.info("Created admin user and default sections")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    sections = Section.query.all()
    section_data = {}
    
    for section in sections:
        contents = Content.query.filter_by(section_id=section.id).all()
        content_data = {}
        
        for content in contents:
            content_data[content.key] = content.value
        
        section_data[section.name] = {
            'title': section.title,
            'contents': content_data
        }
    
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).all()
    
    return render_template('index.html', 
                          sections=section_data, 
                          testimonials=testimonials)

@app.route('/portfolio')
def portfolio():
    # في المستقبل يمكن جلب بيانات معرض الأعمال من قاعدة البيانات
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template('portfolio.html', testimonials=testimonials)

@app.route('/en')
def english_home():
    sections = Section.query.all()
    section_data = {}
    
    for section in sections:
        contents = Content.query.filter_by(section_id=section.id).all()
        content_data = {}
        
        for content in contents:
            content_data[content.key] = content.value
        
        section_data[section.name] = {
            'title': section.title,
            'contents': content_data
        }
    
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).all()
    
    return render_template('en/index.html', 
                          sections=section_data, 
                          testimonials=testimonials)

@app.route('/en/portfolio')
def english_portfolio():
    # في المستقبل يمكن جلب بيانات معرض الأعمال من قاعدة البيانات
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template('en/portfolio.html', testimonials=testimonials)

@app.route('/en/service/<service_type>')
def english_service_detail(service_type):
    # Get service details based on service_type and add English translations
    service = {}
    
    if service_type == 'social-media':
        service = {
            'title': 'تصميم منشورات السوشيال ميديا',
            'title_en': 'Social Media Posts Design',
            'subtitle': 'محتوى بصري جذاب ومميز لمنصات التواصل الاجتماعي',
            'subtitle_en': 'Attractive and distinctive visual content for social media platforms',
            'price': '5000 دج - 15000 دج',
            'price_en': '$50 - $150',
            'delivery_time': '24 - 48 ساعة',
            'delivery_time_en': '24 - 48 hours',
            'revisions': 'غير محدودة',
            'revisions_en': 'Unlimited',
            'formats': 'JPG, PNG, PSD',
            'image_url': '/static/uploads/social-media-design.jpg',
            'description': '<p>تعتبر منشورات السوشيال ميديا من أهم الأدوات التسويقية في العصر الحالي، ويمكنها أن تحدث فرقاً كبيراً في نجاح علامتك التجارية عبر المنصات المختلفة مثل فيسبوك وانستغرام وتويتر.</p><p>أقدم لك تصاميم احترافية تجذب انتباه الجمهور المستهدف وتعكس هوية علامتك التجارية بأفضل شكل ممكن. سواء كنت تحتاج إلى منشورات ترويجية، اقتباسات ملهمة، إعلانات، أو أي نوع آخر من المحتوى البصري.</p>',
            'description_en': '<p>Social media posts are one of the most important marketing tools nowadays, and they can make a big difference in the success of your brand across different platforms like Facebook, Instagram, and Twitter.</p><p>I provide you with professional designs that attract the attention of your target audience and reflect your brand identity in the best possible way. Whether you need promotional posts, inspirational quotes, advertisements, or any other type of visual content.</p>',
            'features': [
                'تصاميم متوافقة مع جميع منصات التواصل الاجتماعي',
                'استخدام ألوان وعناصر تتناسب مع هوية العلامة التجارية',
                'تصميم انفوجرافيك وتصاميم معلوماتية',
                'تصميم منشورات متسلسلة (كاروسيل)',
                'تصميم قوالب للستوري والريلز',
                'تعديلات غير محدودة حتى الوصول للنتيجة المطلوبة'
            ],
            'features_en': [
                'Designs compatible with all social media platforms',
                'Using colors and elements that match the brand identity',
                'Infographic and informational designs',
                'Carousel post designs',
                'Story and Reels templates',
                'Unlimited edits until reaching the desired result'
            ],
            'package_includes': [
                'ملفات بصيغة JPG/PNG جاهزة للنشر',
                'ملفات المصدر بصيغة PSD',
                'تعديلات غير محدودة',
                'ترخيص تجاري للاستخدام'
            ],
            'package_includes_en': [
                'JPG/PNG files ready for publishing',
                'PSD source files',
                'Unlimited revisions',
                'Commercial license for use'
            ],
            'gallery': [
                {'image': '/static/uploads/sm-1.jpg', 'caption': 'تصميم للفيسبوك', 'caption_en': 'Facebook Design'},
                {'image': '/static/uploads/sm-2.jpg', 'caption': 'تصميم للانستغرام', 'caption_en': 'Instagram Design'},
                {'image': '/static/uploads/sm-3.jpg', 'caption': 'تصميم للتويتر', 'caption_en': 'Twitter Design'},
                {'image': '/static/uploads/sm-4.jpg', 'caption': 'انفوجرافيك', 'caption_en': 'Infographic'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم بصري للمناسبات', 'short_desc': 'تصاميم للفعاليات والمناسبات الخاصة', 'url': '/service/events'}
            ],
            'related_services_en': [
                {'title': 'Logo & Brand Identity Design', 'short_desc': 'Distinctive logo and comprehensive brand identity', 'url': '/en/service/logo-brand'},
                {'title': 'Print Design', 'short_desc': 'Brochures, flyers, business cards and more', 'url': '/en/service/print'},
                {'title': 'Event Visual Design', 'short_desc': 'Designs for events and special occasions', 'url': '/en/service/events'}
            ]
        }
    # Add similar translations for other service types
    elif service_type == 'logo-brand':
        service = {
            'title': 'تصميم الشعارات والهوية البصرية',
            'title_en': 'Logo & Brand Identity Design',
            'subtitle': 'شعار مميز يعكس روح علامتك التجارية وهوية بصرية متكاملة',
            'subtitle_en': 'A distinctive logo that reflects your brand spirit and comprehensive visual identity',
            'price': '15000 دج - 50000 دج',
            'price_en': '$150 - $500',
            'delivery_time': '3 - 7 أيام',
            'delivery_time_en': '3 - 7 days',
            'revisions': 'غير محدودة',
            'revisions_en': 'Unlimited',
            'formats': 'AI, EPS, SVG, PNG, JPG, PDF',
            'image_url': '/static/uploads/logo-design.jpg',
            'description': '<p>الشعار هو العنصر الأساسي لأي علامة تجارية ناجحة، وهو الانطباع الأول الذي يتركه عملك في أذهان العملاء. أقدم لك تصميماً فريداً يعكس قيم وروح علامتك التجارية ويميزها عن المنافسين.</p><p>خدمة تصميم الشعار والهوية البصرية تشمل تصميم شعار احترافي وكامل عناصر الهوية البصرية مثل ألوان العلامة التجارية، الخطوط، القرطاسية، وأكثر من ذلك.</p>',
            'description_en': '<p>The logo is the essential element of any successful brand, and it\'s the first impression your business leaves in customers\' minds. I offer you a unique design that reflects your brand\'s values and spirit, distinguishing it from competitors.</p><p>The logo and brand identity design service includes designing a professional logo and all visual identity elements such as brand colors, fonts, stationery, and more.</p>',
            'features': [
                'شعار فريد وحصري 100%',
                'ملفات بصيغ متعددة تناسب جميع الاستخدامات',
                'دليل استخدام الهوية البصرية',
                'تصميم القرطاسية (بطاقات العمل، الأوراق الرسمية، الأظرف)',
                'شعار بألوان وإصدارات متعددة (ملون، أحادي اللون، سالب وموجب)',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'features_en': [
                '100% unique and exclusive logo',
                'Files in multiple formats suitable for all uses',
                'Brand identity usage guide',
                'Stationery design (business cards, letterheads, envelopes)',
                'Logo in multiple colors and versions (colored, monochrome, negative and positive)',
                'Unlimited revisions until complete satisfaction'
            ],
            'package_includes': [
                'شعار بصيغ متعددة (AI, EPS, SVG, PNG, JPG, PDF)',
                'دليل استخدام الهوية البصرية',
                'ملفات القرطاسية بصيغ قابلة للتعديل',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'package_includes_en': [
                'Logo in multiple formats (AI, EPS, SVG, PNG, JPG, PDF)',
                'Brand identity usage guide',
                'Stationery files in editable formats',
                'Full commercial license for use',
                'Unlimited revisions'
            ],
            'gallery': [
                {'image': '/static/uploads/logo-1.jpg', 'caption': 'شعار لشركة تقنية', 'caption_en': 'Tech Company Logo'},
                {'image': '/static/uploads/logo-2.jpg', 'caption': 'هوية بصرية لمطعم', 'caption_en': 'Restaurant Brand Identity'},
                {'image': '/static/uploads/logo-3.jpg', 'caption': 'شعار لعلامة ملابس', 'caption_en': 'Clothing Brand Logo'},
                {'image': '/static/uploads/logo-4.jpg', 'caption': 'هوية بصرية متكاملة', 'caption_en': 'Comprehensive Brand Identity'}
            ],
            'related_services': [
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم الويب', 'short_desc': 'واجهات مستخدم جذابة وسهلة الاستخدام', 'url': '/service/web-design'}
            ],
            'related_services_en': [
                {'title': 'Social Media Posts Design', 'short_desc': 'Attractive designs for social media platforms', 'url': '/en/service/social-media'},
                {'title': 'Print Design', 'short_desc': 'Brochures, flyers, business cards and more', 'url': '/en/service/print'},
                {'title': 'Web Design', 'short_desc': 'Attractive and user-friendly interfaces', 'url': '/en/service/web-design'}
            ]
        }
    else:
        # For other services, redirect to English home
        return redirect(url_for('english_home'))
    
    return render_template('en/service_detail.html', service=service, service_type=service_type)

@app.route('/service/<service_type>')
def service_detail(service_type):
    # Define service details based on service_type
    service = {}
    
    if service_type == 'social-media':
        service = {
            'title': 'تصميم منشورات السوشيال ميديا',
            'subtitle': 'محتوى بصري جذاب ومميز لمنصات التواصل الاجتماعي',
            'price': '5000 دج - 15000 دج',
            'delivery_time': '24 - 48 ساعة',
            'revisions': 'غير محدودة',
            'formats': 'JPG, PNG, PSD',
            'image_url': '/static/uploads/social-media-design.jpg',
            'description': '<p>تعتبر منشورات السوشيال ميديا من أهم الأدوات التسويقية في العصر الحالي، ويمكنها أن تحدث فرقاً كبيراً في نجاح علامتك التجارية عبر المنصات المختلفة مثل فيسبوك وانستغرام وتويتر.</p><p>أقدم لك تصاميم احترافية تجذب انتباه الجمهور المستهدف وتعكس هوية علامتك التجارية بأفضل شكل ممكن. سواء كنت تحتاج إلى منشورات ترويجية، اقتباسات ملهمة، إعلانات، أو أي نوع آخر من المحتوى البصري.</p>',
            'features': [
                'تصاميم متوافقة مع جميع منصات التواصل الاجتماعي',
                'استخدام ألوان وعناصر تتناسب مع هوية العلامة التجارية',
                'تصميم انفوجرافيك وتصاميم معلوماتية',
                'تصميم منشورات متسلسلة (كاروسيل)',
                'تصميم قوالب للستوري والريلز',
                'تعديلات غير محدودة حتى الوصول للنتيجة المطلوبة'
            ],
            'package_includes': [
                'ملفات بصيغة JPG/PNG جاهزة للنشر',
                'ملفات المصدر بصيغة PSD',
                'تعديلات غير محدودة',
                'ترخيص تجاري للاستخدام'
            ],
            'gallery': [
                {'image': '/static/uploads/sm-1.jpg', 'caption': 'تصميم للفيسبوك'},
                {'image': '/static/uploads/sm-2.jpg', 'caption': 'تصميم للانستغرام'},
                {'image': '/static/uploads/sm-3.jpg', 'caption': 'تصميم للتويتر'},
                {'image': '/static/uploads/sm-4.jpg', 'caption': 'انفوجرافيك'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم بصري للمناسبات', 'short_desc': 'تصاميم للفعاليات والمناسبات الخاصة', 'url': '/service/events'}
            ]
        }
    elif service_type == 'logo-brand':
        service = {
            'title': 'تصميم الشعارات والهوية البصرية',
            'subtitle': 'شعار مميز يعكس روح علامتك التجارية وهوية بصرية متكاملة',
            'price': '15000 دج - 50000 دج',
            'delivery_time': '3 - 7 أيام',
            'revisions': 'غير محدودة',
            'formats': 'AI, EPS, SVG, PNG, JPG, PDF',
            'image_url': '/static/uploads/logo-design.jpg',
            'description': '<p>الشعار هو العنصر الأساسي لأي علامة تجارية ناجحة، وهو الانطباع الأول الذي يتركه عملك في أذهان العملاء. أقدم لك تصميماً فريداً يعكس قيم وروح علامتك التجارية ويميزها عن المنافسين.</p><p>خدمة تصميم الشعار والهوية البصرية تشمل تصميم شعار احترافي وكامل عناصر الهوية البصرية مثل ألوان العلامة التجارية، الخطوط، القرطاسية، وأكثر من ذلك.</p>',
            'features': [
                'شعار فريد وحصري 100%',
                'ملفات بصيغ متعددة تناسب جميع الاستخدامات',
                'دليل استخدام الهوية البصرية',
                'تصميم القرطاسية (بطاقات العمل، الأوراق الرسمية، الأظرف)',
                'شعار بألوان وإصدارات متعددة (ملون، أحادي اللون، سالب وموجب)',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'شعار بصيغ متعددة (AI, EPS, SVG, PNG, JPG, PDF)',
                'دليل استخدام الهوية البصرية',
                'ملفات القرطاسية بصيغ قابلة للتعديل',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/logo-1.jpg', 'caption': 'شعار لشركة تقنية'},
                {'image': '/static/uploads/logo-2.jpg', 'caption': 'هوية بصرية لمطعم'},
                {'image': '/static/uploads/logo-3.jpg', 'caption': 'شعار لعلامة ملابس'},
                {'image': '/static/uploads/logo-4.jpg', 'caption': 'هوية بصرية متكاملة'}
            ],
            'related_services': [
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم الويب', 'short_desc': 'واجهات مستخدم جذابة وسهلة الاستخدام', 'url': '/service/web-design'}
            ]
        }
    elif service_type == 'print':
        service = {
            'title': 'تصميم المطبوعات',
            'subtitle': 'بروشورات، فلايرز، بطاقات عمل، ملصقات وأكثر بتصاميم عصرية وجذابة',
            'price': '3000 دج - 20000 دج',
            'delivery_time': '2 - 5 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PDF, AI, PSD',
            'image_url': '/static/uploads/print-design.jpg',
            'description': '<p>تعتبر المطبوعات من أهم أدوات التسويق التقليدية التي لا تزال تحتفظ بفعاليتها حتى في العصر الرقمي. أقدم لك تصاميم مطبوعات احترافية تلفت الانتباه وتوصل رسالتك بوضوح إلى الجمهور المستهدف.</p><p>سواء كنت تحتاج إلى بروشورات، فلايرز، بطاقات عمل، ملصقات، أو أي نوع آخر من المطبوعات، سأصمم لك منتجات ذات جودة عالية وجاهزة للطباعة.</p>',
            'features': [
                'تصاميم جاهزة للطباعة بدقة عالية (300dpi)',
                'التزام بمعايير CMYK اللونية للطباعة',
                'تصميم يتناسب مع الهوية البصرية لعلامتك التجارية',
                'اختيار الخطوط والألوان المناسبة لنوع المطبوعة والجمهور المستهدف',
                'إضافة الباركود أو QR code حسب الطلب',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات جاهزة للطباعة بصيغة PDF',
                'ملفات المصدر بصيغة AI أو PSD',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/print-1.jpg', 'caption': 'بروشور لشركة عقارية'},
                {'image': '/static/uploads/print-2.jpg', 'caption': 'بطاقات عمل'},
                {'image': '/static/uploads/print-3.jpg', 'caption': 'فلاير إعلاني'},
                {'image': '/static/uploads/print-4.jpg', 'caption': 'ملصق لفعالية'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم التغليف', 'short_desc': 'تغليف منتجات بتصاميم جذابة', 'url': '/service/packaging'}
            ]
        }
    elif service_type == 'book-cover':
        service = {
            'title': 'تصميم أغلفة الكتب',
            'subtitle': 'أغلفة احترافية للكتب والمجلات تجذب القراء وتعكس محتوى الكتاب',
            'price': '8000 دج - 25000 دج',
            'delivery_time': '3 - 7 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PDF, AI, PSD, JPG',
            'image_url': '/static/uploads/book-cover.jpg',
            'description': '<p>غلاف الكتاب هو أول ما يلفت انتباه القارئ، وهو عامل رئيسي في قرار شراء الكتاب. أقدم تصاميم أغلفة كتب احترافية تعكس محتوى الكتاب وتجذب القراء المستهدفين.</p><p>سواء كان كتابك رواية، كتاباً علمياً، كتاب طبخ، أو أي نوع آخر من الكتب، سأصمم لك غلافاً فريداً يميز كتابك عن غيره ويترك انطباعاً قوياً.</p>',
            'features': [
                'تصميم الغلاف الأمامي والخلفي والعمود',
                'اختيار الخطوط والألوان المناسبة لنوع الكتاب',
                'تصميم يتوافق مع معايير دور النشر',
                'إمكانية تصميم صفحات داخلية مميزة',
                'تصميم النسخة الإلكترونية للكتاب',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات جاهزة للطباعة بصيغة PDF',
                'ملفات المصدر بصيغة AI أو PSD',
                'نسخة بدقة عالية للكتاب الإلكتروني',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/book-1.jpg', 'caption': 'غلاف رواية'},
                {'image': '/static/uploads/book-2.jpg', 'caption': 'غلاف كتاب علمي'},
                {'image': '/static/uploads/book-3.jpg', 'caption': 'غلاف كتاب أطفال'},
                {'image': '/static/uploads/book-4.jpg', 'caption': 'غلاف مجلة'}
            ],
            'related_services': [
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'التصميم الإبداعي والفوتومانيبوليشن', 'short_desc': 'تصاميم إبداعية متقدمة', 'url': '/service/photo-manipulation'},
                {'title': 'التصميم الداخلي للكتب', 'short_desc': 'تنسيق الصفحات الداخلية للكتب', 'url': '/service/book-layout'}
            ]
        }
    elif service_type == 'photo-manipulation':
        service = {
            'title': 'التصميم الإبداعي والفوتومانيبوليشن',
            'subtitle': 'تصاميم إبداعية متقدمة وتعديل احترافي للصور',
            'price': '7000 دج - 30000 دج',
            'delivery_time': '3 - 10 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PSD, JPG, PNG, TIFF',
            'image_url': '/static/uploads/photo-manipulation.jpg',
            'description': '<p>خدمة الفوتومانيبوليشن تتيح إمكانيات لا حدود لها في عالم التصميم، من دمج الصور وإضافة عناصر خيالية إلى تعديل الصور الاحترافي وصناعة تصاميم إبداعية لا مثيل لها.</p><p>أقدم خدمات متقدمة في مجال الفوتومانيبوليشن والتصميم الإبداعي لإنشاء صور فنية استثنائية تلفت الأنظار وتوصل رسالتك بطريقة مبتكرة.</p>',
            'features': [
                'دمج الصور باحترافية عالية',
                'إزالة أو إضافة عناصر للصور',
                'تعديل الإضاءة والألوان',
                'إنشاء تأثيرات خاصة وتصاميم خيالية',
                'تحسين جودة الصور القديمة أو منخفضة الدقة',
                'ترميم الصور التالفة',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات بدقة عالية بصيغة JPG/PNG/TIFF',
                'ملفات المصدر بصيغة PSD',
                'إصدارات متعددة بأحجام مختلفة حسب الاستخدام',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/manip-1.jpg', 'caption': 'دمج صور لإعلان'},
                {'image': '/static/uploads/manip-2.jpg', 'caption': 'تصميم خيالي'},
                {'image': '/static/uploads/manip-3.jpg', 'caption': 'تعديل احترافي للصور'},
                {'image': '/static/uploads/manip-4.jpg', 'caption': 'ترميم صورة قديمة'}
            ],
            'related_services': [
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم أغلفة الكتب', 'short_desc': 'أغلفة كتب جذابة', 'url': '/service/book-cover'},
                {'title': 'تصميم الإعلانات', 'short_desc': 'إعلانات مطبوعة ورقمية', 'url': '/service/advertising'}
            ]
        }
    else:
        # Default service or 404
        abort(404)
    
    return render_template('service_detail.html', service=service)

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    sections_count = Section.query.count()
    contents_count = Content.query.count()
    testimonials_count = Testimonial.query.count()
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    
    return render_template('admin/dashboard.html', 
                          sections_count=sections_count,
                          contents_count=contents_count,
                          testimonials_count=testimonials_count,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/content')
@login_required
def admin_content():
    sections = Section.query.all()
    return render_template('admin/content.html', sections=sections)
    
@app.route('/admin/services')
@login_required
def admin_service_content():
    return render_template('admin/service_content.html')

@app.route('/admin/services/<service_type>/edit')
@login_required
def admin_edit_service(service_type):
    service = {}
    
    # Get service data based on service_type
    if service_type == 'social-media':
        service = {
            'title': 'تصميم منشورات السوشيال ميديا',
            'subtitle': 'محتوى بصري جذاب ومميز لمنصات التواصل الاجتماعي',
            'price': '5000 دج - 15000 دج',
            'delivery_time': '24 - 48 ساعة',
            'revisions': 'غير محدودة',
            'formats': 'JPG, PNG, PSD',
            'image_url': '/static/uploads/social-media-design.jpg',
            'description': '<p>تعتبر منشورات السوشيال ميديا من أهم الأدوات التسويقية في العصر الحالي، ويمكنها أن تحدث فرقاً كبيراً في نجاح علامتك التجارية عبر المنصات المختلفة مثل فيسبوك وانستغرام وتويتر.</p><p>أقدم لك تصاميم احترافية تجذب انتباه الجمهور المستهدف وتعكس هوية علامتك التجارية بأفضل شكل ممكن. سواء كنت تحتاج إلى منشورات ترويجية، اقتباسات ملهمة، إعلانات، أو أي نوع آخر من المحتوى البصري.</p>',
            'features': [
                'تصاميم متوافقة مع جميع منصات التواصل الاجتماعي',
                'استخدام ألوان وعناصر تتناسب مع هوية العلامة التجارية',
                'تصميم انفوجرافيك وتصاميم معلوماتية',
                'تصميم منشورات متسلسلة (كاروسيل)',
                'تصميم قوالب للستوري والريلز',
                'تعديلات غير محدودة حتى الوصول للنتيجة المطلوبة'
            ],
            'package_includes': [
                'ملفات بصيغة JPG/PNG جاهزة للنشر',
                'ملفات المصدر بصيغة PSD',
                'تعديلات غير محدودة',
                'ترخيص تجاري للاستخدام'
            ],
            'gallery': [
                {'image': '/static/uploads/sm-1.jpg', 'caption': 'تصميم للفيسبوك'},
                {'image': '/static/uploads/sm-2.jpg', 'caption': 'تصميم للانستغرام'},
                {'image': '/static/uploads/sm-3.jpg', 'caption': 'تصميم للتويتر'},
                {'image': '/static/uploads/sm-4.jpg', 'caption': 'انفوجرافيك'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم بصري للمناسبات', 'short_desc': 'تصاميم للفعاليات والمناسبات الخاصة', 'url': '/service/events'}
            ]
        }
    elif service_type == 'logo-brand':
        service = {
            'title': 'تصميم الشعارات والهوية البصرية',
            'subtitle': 'شعار مميز يعكس روح علامتك التجارية وهوية بصرية متكاملة',
            'price': '15000 دج - 50000 دج',
            'delivery_time': '3 - 7 أيام',
            'revisions': 'غير محدودة',
            'formats': 'AI, EPS, SVG, PNG, JPG, PDF',
            'image_url': '/static/uploads/logo-design.jpg',
            'description': '<p>الشعار هو العنصر الأساسي لأي علامة تجارية ناجحة، وهو الانطباع الأول الذي يتركه عملك في أذهان العملاء. أقدم لك تصميماً فريداً يعكس قيم وروح علامتك التجارية ويميزها عن المنافسين.</p><p>خدمة تصميم الشعار والهوية البصرية تشمل تصميم شعار احترافي وكامل عناصر الهوية البصرية مثل ألوان العلامة التجارية، الخطوط، القرطاسية، وأكثر من ذلك.</p>',
            'features': [
                'شعار فريد وحصري 100%',
                'ملفات بصيغ متعددة تناسب جميع الاستخدامات',
                'دليل استخدام الهوية البصرية',
                'تصميم القرطاسية (بطاقات العمل، الأوراق الرسمية، الأظرف)',
                'شعار بألوان وإصدارات متعددة (ملون، أحادي اللون، سالب وموجب)',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'شعار بصيغ متعددة (AI, EPS, SVG, PNG, JPG, PDF)',
                'دليل استخدام الهوية البصرية',
                'ملفات القرطاسية بصيغ قابلة للتعديل',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/logo-1.jpg', 'caption': 'شعار لشركة تقنية'},
                {'image': '/static/uploads/logo-2.jpg', 'caption': 'هوية بصرية لمطعم'},
                {'image': '/static/uploads/logo-3.jpg', 'caption': 'شعار لعلامة ملابس'},
                {'image': '/static/uploads/logo-4.jpg', 'caption': 'هوية بصرية متكاملة'}
            ],
            'related_services': [
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'تصميم الويب', 'short_desc': 'واجهات مستخدم جذابة وسهلة الاستخدام', 'url': '/service/web-design'}
            ]
        }
    elif service_type == 'print':
        service = {
            'title': 'تصميم المطبوعات',
            'subtitle': 'بروشورات، فلايرز، بطاقات عمل، ملصقات وأكثر بتصاميم عصرية وجذابة',
            'price': '3000 دج - 20000 دج',
            'delivery_time': '2 - 5 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PDF, AI, PSD',
            'image_url': '/static/uploads/print-design.jpg',
            'description': '<p>تعتبر المطبوعات من أهم أدوات التسويق التقليدية التي لا تزال تحتفظ بفعاليتها حتى في العصر الرقمي. أقدم لك تصاميم مطبوعات احترافية تلفت الانتباه وتوصل رسالتك بوضوح إلى الجمهور المستهدف.</p><p>سواء كنت تحتاج إلى بروشورات، فلايرز، بطاقات عمل، ملصقات، أو أي نوع آخر من المطبوعات، سأصمم لك منتجات ذات جودة عالية وجاهزة للطباعة.</p>',
            'features': [
                'تصاميم جاهزة للطباعة بدقة عالية (300dpi)',
                'التزام بمعايير CMYK اللونية للطباعة',
                'تصميم يتناسب مع الهوية البصرية لعلامتك التجارية',
                'اختيار الخطوط والألوان المناسبة لنوع المطبوعة والجمهور المستهدف',
                'إضافة الباركود أو QR code حسب الطلب',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات جاهزة للطباعة بصيغة PDF',
                'ملفات المصدر بصيغة AI أو PSD',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/print-1.jpg', 'caption': 'بروشور لشركة عقارية'},
                {'image': '/static/uploads/print-2.jpg', 'caption': 'بطاقات عمل'},
                {'image': '/static/uploads/print-3.jpg', 'caption': 'فلاير إعلاني'},
                {'image': '/static/uploads/print-4.jpg', 'caption': 'ملصق لفعالية'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم التغليف', 'short_desc': 'تغليف منتجات بتصاميم جذابة', 'url': '/service/packaging'}
            ]
        }
    elif service_type == 'book-cover':
        service = {
            'title': 'تصميم أغلفة الكتب',
            'subtitle': 'أغلفة احترافية للكتب والمجلات تجذب القراء وتعكس محتوى الكتاب',
            'price': '8000 دج - 25000 دج',
            'delivery_time': '3 - 7 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PDF, AI, PSD, JPG',
            'image_url': '/static/uploads/book-cover.jpg',
            'description': '<p>غلاف الكتاب هو أول ما يلفت انتباه القارئ، وهو عامل رئيسي في قرار شراء الكتاب. أقدم تصاميم أغلفة كتب احترافية تعكس محتوى الكتاب وتجذب القراء المستهدفين.</p><p>سواء كان كتابك رواية، كتاباً علمياً، كتاب طبخ، أو أي نوع آخر من الكتب، سأصمم لك غلافاً فريداً يميز كتابك عن غيره ويترك انطباعاً قوياً.</p>',
            'features': [
                'تصميم الغلاف الأمامي والخلفي والعمود',
                'اختيار الخطوط والألوان المناسبة لنوع الكتاب',
                'تصميم يتوافق مع معايير دور النشر',
                'إمكانية تصميم صفحات داخلية مميزة',
                'تصميم النسخة الإلكترونية للكتاب',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات جاهزة للطباعة بصيغة PDF',
                'ملفات المصدر بصيغة AI أو PSD',
                'نسخة بدقة عالية للكتاب الإلكتروني',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/book-1.jpg', 'caption': 'غلاف رواية'},
                {'image': '/static/uploads/book-2.jpg', 'caption': 'غلاف كتاب علمي'},
                {'image': '/static/uploads/book-3.jpg', 'caption': 'غلاف كتاب أطفال'},
                {'image': '/static/uploads/book-4.jpg', 'caption': 'غلاف مجلة'}
            ],
            'related_services': [
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز، بطاقات عمل وأكثر', 'url': '/service/print'},
                {'title': 'التصميم الإبداعي والفوتومانيبوليشن', 'short_desc': 'تصاميم إبداعية متقدمة', 'url': '/service/photo-manipulation'},
                {'title': 'التصميم الداخلي للكتب', 'short_desc': 'تنسيق الصفحات الداخلية للكتب', 'url': '/service/book-layout'}
            ]
        }
    elif service_type == 'photo-manipulation':
        service = {
            'title': 'التصميم الإبداعي والفوتومانيبوليشن',
            'subtitle': 'تصاميم إبداعية متقدمة وتعديل احترافي للصور',
            'price': '7000 دج - 30000 دج',
            'delivery_time': '3 - 10 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PSD, JPG, PNG, TIFF',
            'image_url': '/static/uploads/photo-manipulation.jpg',
            'description': '<p>خدمة الفوتومانيبوليشن تتيح إمكانيات لا حدود لها في عالم التصميم، من دمج الصور وإضافة عناصر خيالية إلى تعديل الصور الاحترافي وصناعة تصاميم إبداعية لا مثيل لها.</p><p>أقدم خدمات متقدمة في مجال الفوتومانيبوليشن والتصميم الإبداعي لإنشاء صور فنية استثنائية تلفت الأنظار وتوصل رسالتك بطريقة مبتكرة.</p>',
            'features': [
                'دمج الصور باحترافية عالية',
                'إزالة أو إضافة عناصر للصور',
                'تعديل الإضاءة والألوان',
                'إنشاء تأثيرات خاصة وتصاميم خيالية',
                'تحسين جودة الصور القديمة أو منخفضة الدقة',
                'ترميم الصور التالفة',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات بدقة عالية بصيغة JPG/PNG/TIFF',
                'ملفات المصدر بصيغة PSD',
                'إصدارات متعددة بأحجام مختلفة حسب الاستخدام',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/manip-1.jpg', 'caption': 'دمج صور لإعلان'},
                {'image': '/static/uploads/manip-2.jpg', 'caption': 'تصميم خيالي'},
                {'image': '/static/uploads/manip-3.jpg', 'caption': 'تعديل احترافي للصور'},
                {'image': '/static/uploads/manip-4.jpg', 'caption': 'ترميم صورة قديمة'}
            ],
            'related_services': [
                {'title': 'تصميم منشورات السوشيال ميديا', 'short_desc': 'تصاميم جذابة لمنصات التواصل الاجتماعي', 'url': '/service/social-media'},
                {'title': 'تصميم أغلفة الكتب', 'short_desc': 'أغلفة كتب جذابة', 'url': '/service/book-cover'},
                {'title': 'تصميم الإعلانات', 'short_desc': 'إعلانات مطبوعة ورقمية', 'url': '/service/advertising'}
            ]
        }
    elif service_type == 'business-card':
        service = {
            'title': 'تصميم بطاقات العمل',
            'subtitle': 'بطاقات عمل احترافية تعكس هوية شركتك بتصاميم عصرية وطباعة عالية الجودة',
            'price': '2000 دج - 5000 دج',
            'delivery_time': '1 - 3 أيام',
            'revisions': 'غير محدودة',
            'formats': 'PDF, AI, PSD, JPG',
            'image_url': '/static/uploads/business-card.jpg',
            'description': '<p>بطاقة العمل هي أول تواصل مادي بينك وبين عملائك المحتملين، وهي تعكس احترافية علامتك التجارية وتترك انطباعًا أوليًا مهمًا.</p><p>أقدم خدمة تصميم بطاقات عمل فريدة ومميزة تعكس هوية شركتك وتلفت انتباه العملاء. سواء كنت تفضل تصميمًا بسيطًا وأنيقًا أو تصميمًا إبداعيًا جريئًا، سأصمم لك بطاقة عمل تناسب مجال عملك وتعزز صورة علامتك التجارية.</p>',
            'features': [
                'تصميم بطاقة عمل فريدة ومخصصة',
                'تصميم وجهين (أمامي وخلفي)',
                'ملفات جاهزة للطباعة بدقة عالية',
                'اختيار الخطوط والألوان المناسبة لهوية شركتك',
                'إمكانية إضافة QR code لموقعك أو وسائل التواصل الاجتماعي',
                'تعديلات غير محدودة حتى الرضا الكامل'
            ],
            'package_includes': [
                'ملفات بصيغ متعددة (PDF, AI, PSD, JPG)',
                'ملفات جاهزة للطباعة بدقة 300dpi',
                'نسخة رقمية للاستخدام عبر البريد الإلكتروني',
                'ترخيص تجاري كامل للاستخدام',
                'تعديلات غير محدودة'
            ],
            'gallery': [
                {'image': '/static/uploads/card-1.jpg', 'caption': 'بطاقة عمل لشركة تقنية'},
                {'image': '/static/uploads/card-2.jpg', 'caption': 'بطاقة عمل لمصمم حر'},
                {'image': '/static/uploads/card-3.jpg', 'caption': 'بطاقة عمل لمطعم'},
                {'image': '/static/uploads/card-4.jpg', 'caption': 'بطاقة عمل لصالون تجميل'}
            ],
            'related_services': [
                {'title': 'تصميم الشعارات والهوية البصرية', 'short_desc': 'شعار مميز وهوية بصرية متكاملة', 'url': '/service/logo-brand'},
                {'title': 'تصميم المطبوعات', 'short_desc': 'بروشورات، فلايرز وأكثر', 'url': '/service/print'},
                {'title': 'القرطاسية المكتبية', 'short_desc': 'أوراق رسمية، أظرف وغيرها', 'url': '/service/stationery'}
            ]
        }
    else:
        abort(404)
    
    return render_template('admin/edit_service.html', service=service, service_type=service_type)

@app.route('/admin/services/add', methods=['POST'])
@login_required
def admin_add_service():
    # Logic to add a new service would be implemented here
    # This would include processing the form submission and saving data
    flash('تمت إضافة الخدمة بنجاح!', 'success')
    return redirect(url_for('admin_service_content'))

@app.route('/admin/services/<service_type>/update', methods=['POST'])
@login_required
def update_service(service_type):
    # Logic to update existing service would be implemented here
    # This would include processing the form submission and updating data
    flash('تم تحديث بيانات الخدمة بنجاح!', 'success')
    return redirect(url_for('admin_edit_service', service_type=service_type))

@app.route('/admin/content/<int:section_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_content(section_id):
    section = Section.query.get_or_404(section_id)
    
    if request.method == 'POST':
        section.title = request.form.get('title', section.title)
        
        # Process content updates
        for key, value in request.form.items():
            if key.startswith('content_'):
                content_key = key[8:]  # Remove 'content_' prefix
                content = Content.query.filter_by(section_id=section.id, key=content_key).first()
                
                if content:
                    content.value = value
                else:
                    new_content = Content(section_id=section.id, key=content_key, value=value)
                    db.session.add(new_content)
        
        db.session.commit()
        flash('تم تحديث المحتوى بنجاح', 'success')
        return redirect(url_for('admin_content'))
    
    contents = Content.query.filter_by(section_id=section.id).all()
    return render_template('admin/edit_content.html', section=section, contents=contents)

@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/testimonials/approve/<int:testimonial_id>', methods=['POST'])
@login_required
def approve_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.approved = True
    db.session.commit()
    flash('تم اعتماد التعليق بنجاح', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/testimonials/delete/<int:testimonial_id>', methods=['POST'])
@login_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('تم حذف التعليق بنجاح', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/profile')
@login_required
def admin_profile():
    return render_template('admin/profile.html')

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def update_profile():
    if 'current_password' in request.form and request.form['current_password']:
        if not check_password_hash(current_user.password_hash, request.form['current_password']):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return redirect(url_for('admin_profile'))
        
        if request.form.get('new_password'):
            current_user.password_hash = generate_password_hash(request.form['new_password'])
    
    if request.form.get('email'):
        current_user.email = request.form['email']
    
    db.session.commit()
    flash('تم تحديث الملف الشخصي بنجاح', 'success')
    return redirect(url_for('admin_profile'))

# API Routes for AJAX
@app.route('/api/testimonial/add', methods=['POST'])
def add_testimonial():
    try:
        name = request.form.get('name')
        company = request.form.get('company', '')
        content = request.form.get('content')
        rating = int(request.form.get('rating', 5))
        
        if not name or not content:
            return jsonify({'success': False, 'message': 'يرجى تعبئة جميع الحقول المطلوبة'}), 400
        
        testimonial = Testimonial(
            name=name,
            company=company,
            content=content,
            rating=rating,
            approved=False,
            created_at=datetime.now()
        )
        
        db.session.add(testimonial)
        db.session.commit()
        
        # إرسال إشعار بريد إلكتروني للمسؤول
        try:
            admin = User.query.filter_by(username="admin").first()
            if admin:
                from email_service import send_testimonial_notification
                send_testimonial_notification(
                    name=name,
                    company=company,
                    rating=rating,
                    content=content,
                    admin_email=admin.email
                )
        except Exception as email_error:
            app.logger.error(f"Error sending testimonial notification email: {str(email_error)}")
            # لا نريد أن تفشل العملية إذا فشل إرسال البريد الإلكتروني
        
        return jsonify({'success': True, 'message': 'تم إرسال تعليقك بنجاح وسيتم مراجعته قريبا'})
    
    except Exception as e:
        app.logger.error(f"Error adding testimonial: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام. يرجى المحاولة مرة أخرى لاحقا'}), 500

@app.route('/api/section/content', methods=['GET'])
def get_section_content():
    section_name = request.args.get('section')
    if not section_name:
        return jsonify({'success': False, 'message': 'Section name is required'}), 400
    
    section = Section.query.filter_by(name=section_name).first()
    if not section:
        return jsonify({'success': False, 'message': 'Section not found'}), 404
    
    contents = Content.query.filter_by(section_id=section.id).all()
    content_data = {content.key: content.value for content in contents}
    
    return jsonify({
        'success': True,
        'title': section.title,
        'contents': content_data
    })

@app.route('/api/content/update', methods=['POST'])
@login_required
def update_content():
    try:
        section_id = request.json.get('section_id')
        key = request.json.get('key')
        value = request.json.get('value')
        
        if not section_id or not key or value is None:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        content = Content.query.filter_by(section_id=section_id, key=key).first()
        
        if content:
            content.value = value
        else:
            content = Content(section_id=section_id, key=key, value=value)
            db.session.add(content)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تحديث المحتوى بنجاح'})
    
    except Exception as e:
        app.logger.error(f"Error updating content: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'}), 500

@app.route('/api/section/update', methods=['POST'])
@login_required
def update_section():
    try:
        section_id = request.json.get('section_id')
        title = request.json.get('title')
        
        if not section_id or not title:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        section = Section.query.get(section_id)
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'}), 404
        
        section.title = title
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تحديث عنوان القسم بنجاح'})
    
    except Exception as e:
        app.logger.error(f"Error updating section: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'}), 500

@app.route('/api/image/upload', methods=['POST'])
@login_required
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'لم يتم رفع أي صورة'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'لم يتم اختيار صورة'}), 400
        
        section_name = request.form.get('section')
        key = request.form.get('key')
        
        if not section_name or not key:
            return jsonify({'success': False, 'message': 'قسم أو مفتاح مفقود'}), 400
        
        # Check file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به. الأنواع المسموح بها: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        # Create directories if they don't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        
        section = Section.query.filter_by(name=section_name).first()
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'}), 404
        
        image_url = f"/static/uploads/{new_filename}"
        
        # Save image info to database
        image = Image(
            section_id=section.id,
            key=key,
            filename=new_filename,
            path=image_url
        )
        db.session.add(image)
        
        # Update content to reference this image
        content = Content.query.filter_by(section_id=section.id, key=key).first()
        if content:
            content.value = image_url
        else:
            content = Content(section_id=section.id, key=key, value=image_url)
            db.session.add(content)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'تم رفع الصورة بنجاح',
            'url': image_url
        })
    
    except Exception as e:
        app.logger.error(f"Error uploading image: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'}), 500

@app.route('/api/image/upload_base64', methods=['POST'])
@login_required
def upload_base64_image():
    try:
        data = request.json
        if 'image' not in data or 'section' not in data or 'key' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        base64_data = data['image']
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_profile.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        section = Section.query.filter_by(name=data['section']).first()
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'}), 404
        
        image_url = f"/static/uploads/{filename}"
        
        # Save image info to database
        image = Image(
            section_id=section.id,
            key=data['key'],
            filename=filename,
            path=image_url
        )
        db.session.add(image)
        
        # Update content to reference this image
        content = Content.query.filter_by(section_id=section.id, key=data['key']).first()
        if content:
            content.value = image_url
        else:
            content = Content(section_id=section.id, key=data['key'], value=image_url)
            db.session.add(content)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'تم رفع الصورة بنجاح',
            'url': image_url
        })
    
    except Exception as e:
        app.logger.error(f"Error uploading base64 image: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'}), 500

# Portfolio Items CRUD and interactions
@app.route('/api/portfolio', methods=['GET'])
def get_portfolio_items():
    """Get all portfolio items with filtering options"""
    category = request.args.get('category')
    query = PortfolioItem.query
    
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    items = query.order_by(PortfolioItem.created_at.desc()).all()
    result = []
    
    for item in items:
        result.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'image_url': item.image_url,
            'category': item.category,
            'year': item.year,
            'views_count': item.views_count,
            'likes_count': item.likes_count,
            'comments_count': len(item.comments)
        })
    
    return jsonify({'success': True, 'items': result})

@app.route('/api/portfolio/<int:portfolio_id>/view', methods=['POST'])
def view_portfolio_item(portfolio_id):
    """Increment view count for a portfolio item"""
    item = PortfolioItem.query.get_or_404(portfolio_id)
    
    # Get user IP to avoid counting multiple views from same user in short time
    user_ip = request.remote_addr
    
    # Check if we have a view from this IP in the last hour
    last_hour = datetime.now() - timedelta(hours=1)
    session_key = f'view_{portfolio_id}_{user_ip}'
    
    if session.get(session_key) is None:
        item.views_count += 1
        db.session.commit()
        # Set session to expire in 1 hour
        session[session_key] = True
    
    return jsonify({'success': True, 'views_count': item.views_count})

@app.route('/api/portfolio/<int:portfolio_id>/like', methods=['POST'])
def like_portfolio_item(portfolio_id):
    """Like or unlike a portfolio item"""
    item = PortfolioItem.query.get_or_404(portfolio_id)
    
    # Get user IP
    user_ip = request.remote_addr
    
    # Check if user already liked this item
    existing_like = PortfolioLike.query.filter_by(
        portfolio_id=portfolio_id, 
        user_ip=user_ip
    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        item.likes_count = max(0, item.likes_count - 1)
        liked = False
    else:
        # Like
        new_like = PortfolioLike(portfolio_id=portfolio_id, user_ip=user_ip)
        db.session.add(new_like)
        item.likes_count += 1
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'likes_count': item.likes_count,
        'liked': liked
    })

@app.route('/api/portfolio/<int:portfolio_id>/comments', methods=['GET'])
def get_portfolio_comments(portfolio_id):
    """Get approved comments for a portfolio item"""
    comments = PortfolioComment.query.filter_by(
        portfolio_id=portfolio_id,
        approved=True
    ).order_by(PortfolioComment.created_at.desc()).all()
    
    result = []
    for comment in comments:
        result.append({
            'id': comment.id,
            'name': comment.name,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'success': True, 'comments': result})

@app.route('/api/portfolio/<int:portfolio_id>/comments', methods=['POST'])
def add_portfolio_comment(portfolio_id):
    """Add a new comment to a portfolio item"""
    item = PortfolioItem.query.get_or_404(portfolio_id)
    
    data = request.get_json()
    name = data.get('name')
    email = data.get('email', '')
    content = data.get('content')
    
    if not name or not content:
        return jsonify({'success': False, 'message': 'يرجى تعبئة جميع الحقول المطلوبة'}), 400
    
    comment = PortfolioComment(
        portfolio_id=portfolio_id,
        name=name,
        email=email,
        content=content,
        approved=False
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Send email notification to admin
    try:
        admin = User.query.filter_by(username="admin").first()
        if admin:
            send_contact_form_notification(
                name=name,
                email=email or "غير محدد",
                subject="تعليق جديد على معرض الأعمال",
                message=f"تعليق على العمل: {item.title}\n\n{content}",
                admin_email=admin.email
            )
    except Exception as e:
        app.logger.error(f"خطأ في إرسال الإشعار البريدي: {e}")
    
    return jsonify({
        'success': True,
        'message': 'تم إرسال تعليقك بنجاح وسيظهر بعد الموافقة عليه من قبل الإدارة'
    })

# Admin routes for comments approval
@app.route('/admin/portfolio_comments')
@login_required
def admin_portfolio_comments():
    """Admin interface to manage portfolio comments"""
    pending_comments = PortfolioComment.query.filter_by(approved=False).order_by(PortfolioComment.created_at.desc()).all()
    approved_comments = PortfolioComment.query.filter_by(approved=True).order_by(PortfolioComment.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/portfolio_comments.html',
        pending_comments=pending_comments,
        approved_comments=approved_comments
    )

@app.route('/admin/portfolio_comment/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_portfolio_comment(comment_id):
    """Approve a portfolio comment"""
    comment = PortfolioComment.query.get_or_404(comment_id)
    comment.approved = True
    db.session.commit()
    
    flash('تم الموافقة على التعليق بنجاح', 'success')
    return redirect(url_for('admin_portfolio_comments'))

@app.route('/admin/portfolio_comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_portfolio_comment(comment_id):
    """Delete a portfolio comment"""
    comment = PortfolioComment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    
    flash('تم حذف التعليق بنجاح', 'success')
    return redirect(url_for('admin_portfolio_comments'))

# Update contact form to send emails
@app.route('/api/contact', methods=['POST'])
def contact_form():
    """Handle contact form submission and send email"""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')
    
    if not name or not email or not message:
        return jsonify({'success': False, 'message': 'يرجى تعبئة جميع الحقول المطلوبة'}), 400
    
    # Send email to admin
    try:
        admin = User.query.filter_by(username="admin").first()
        if admin:
            email_sent = send_contact_form_notification(
                name=name,
                email=email,
                subject=subject or "رسالة من نموذج الاتصال",
                message=message,
                admin_email=admin.email
            )
            
            if email_sent:
                return jsonify({'success': True, 'message': 'تم إرسال رسالتك بنجاح'})
            else:
                return jsonify({'success': False, 'message': 'حدث خطأ أثناء إرسال البريد الإلكتروني'}), 500
        else:
            return jsonify({'success': False, 'message': 'لم يتم العثور على بريد المسؤول'}), 500
    except Exception as e:
        app.logger.error(f"خطأ في إرسال البريد الإلكتروني: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
