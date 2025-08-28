from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import sqlite3
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import re
from contextlib import contextmanager

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إنشاء المجلدات المطلوبة
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

# إعداد قاعدة البيانات
DATABASE = 'data/schools.db'

def init_db():
    """تهيئة قاعدة البيانات"""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS school_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id INTEGER NOT NULL,
                background_color TEXT DEFAULT '#ffffff',
                text_color TEXT DEFAULT '#000000',
                font_size TEXT DEFAULT '24px',
                logo_path TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS student_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools (id)
            )
        ''')
        
        conn.commit()

@contextmanager
def get_db():
    """مدير السياق لقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def validate_school_name(name):
    """التحقق من صحة اسم المدرسة"""
    if not name or len(name.strip()) < 2:
        return False, "اسم المدرسة يجب أن يكون أكثر من حرف واحد"
    
    if len(name) > 100:
        return False, "اسم المدرسة طويل جداً"
    
    # السماح بالأحرف العربية والإنجليزية والأرقام والمسافات
    if not re.match(r'^[\u0600-\u06FFa-zA-Z0-9\s]+$', name.strip()):
        return False, "اسم المدرسة يحتوي على أحرف غير مسموحة"
    
    return True, ""

def validate_student_name(name):
    """التحقق من صحة اسم الطالب"""
    if not name or len(name.strip()) < 2:
        return False, "اسم الطالب يجب أن يكون أكثر من حرف واحد"
    
    if len(name) > 50:
        return False, "اسم الطالب طويل جداً"
    
    # السماح بالأحرف العربية والإنجليزية والمسافات
    if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', name.strip()):
        return False, "اسم الطالب يحتوي على أحرف غير مسموحة"
    
    return True, ""

def get_school_by_name(school_name):
    """الحصول على بيانات المدرسة من قاعدة البيانات"""
    try:
        with get_db() as conn:
            school = conn.execute(
                'SELECT * FROM schools WHERE name = ?', (school_name,)
            ).fetchone()
            
            if not school:
                return None
            
            settings = conn.execute(
                'SELECT * FROM school_settings WHERE school_id = ?', (school['id'],)
            ).fetchone()
            
            recent_names = conn.execute(
                '''SELECT name FROM student_names 
                   WHERE school_id = ? 
                   ORDER BY submitted_at DESC 
                   LIMIT 12''', (school['id'],)
            ).fetchall()
            
            return {
                'id': school['id'],
                'name': school['name'],
                'display_name': school['display_name'],
                'is_active': school['is_active'],
                'settings': {
                    'background_color': settings['background_color'] if settings else '#ffffff',
                    'text_color': settings['text_color'] if settings else '#000000',
                    'font_size': settings['font_size'] if settings else '24px',
                    'logo_path': settings['logo_path'] if settings else ''
                },
                'recent_names': [row['name'] for row in recent_names]
            }
    except Exception as e:
        logger.error(f"خطأ في الحصول على بيانات المدرسة: {e}")
        return None

def create_school(school_name, display_name):
    """إنشاء مدرسة جديدة"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO schools (name, display_name) VALUES (?, ?)',
                (school_name, display_name)
            )
            school_id = cursor.lastrowid
            
            cursor.execute(
                '''INSERT INTO school_settings (school_id, background_color, text_color, font_size, logo_path) 
                   VALUES (?, ?, ?, ?, ?)''',
                (school_id, '#ffffff', '#000000', '24px', '')
            )
            
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"خطأ في إنشاء المدرسة: {e}")
        return False

# الصفحات الرئيسية
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return render_template('home.html')

@app.route('/<school_name>/entry')
def entry(school_name):
    """صفحة إدخال الأسماء"""
    school_data = get_school_by_name(school_name)
    if not school_data or not school_data['is_active']:
        flash('المدرسة غير موجودة أو غير نشطة', 'error')
        return redirect(url_for('home'))
    
    return render_template('entry.html', 
                         school_name=school_name, 
                         display_name=school_data['display_name'])

@app.route('/<school_name>/display')
def display(school_name):
    """صفحة العرض"""
    school_data = get_school_by_name(school_name)
    if not school_data or not school_data['is_active']:
        flash('المدرسة غير موجودة أو غير نشطة', 'error')
        return redirect(url_for('home'))
    
    return render_template('display.html', 
                         school_name=school_name,
                         display_name=school_data['display_name'],
                         settings=school_data['settings'])

@app.route('/<school_name>/admin')
def school_admin(school_name):
    """لوحة تحكم المدرسة"""
    school_data = get_school_by_name(school_name)
    if not school_data:
        flash('المدرسة غير موجودة', 'error')
        return redirect(url_for('home'))
    
    return render_template('school_admin.html', 
                         school_name=school_name,
                         display_name=school_data['display_name'],
                         settings=school_data['settings'])

@app.route('/super_admin')
def super_admin():
    """لوحة تحكم المالك"""
    try:
        with get_db() as conn:
            schools = conn.execute('SELECT * FROM schools ORDER BY created_at DESC').fetchall()
        return render_template('super_admin.html', schools=schools)
    except Exception as e:
        logger.error(f"خطأ في جلب المدارس: {e}")
        flash('خطأ في جلب بيانات المدارس', 'error')
        return render_template('super_admin.html', schools=[])

@app.route('/add_school', methods=['POST'])
def add_school():
    """إضافة مدرسة جديدة"""
    school_name = request.form.get('school_name', '').strip()
    display_name = request.form.get('display_name', '').strip()
    
    if not display_name:
        display_name = school_name
    
    is_valid, error_msg = validate_school_name(school_name)
    if not is_valid:
        flash(error_msg, 'error')
        return redirect(url_for('super_admin'))
    
    # تحويل الاسم لشكل مناسب للURL
    url_name = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9]', '_', school_name)
    
    if create_school(url_name, display_name):
        flash(f'تم إضافة مدرسة {display_name} بنجاح', 'success')
        logger.info(f"تم إنشاء مدرسة جديدة: {display_name}")
    else:
        flash('فشل في إضافة المدرسة - قد تكون موجودة مسبقاً', 'error')
    
    return redirect(url_for('super_admin'))

@app.route('/toggle_school/<school_name>', methods=['POST'])
def toggle_school(school_name):
    """تفعيل/إيقاف مدرسة"""
    try:
        with get_db() as conn:
            school = conn.execute(
                'SELECT id, is_active FROM schools WHERE name = ?', (school_name,)
            ).fetchone()
            
            if school:
                new_status = not school['is_active']
                conn.execute(
                    'UPDATE schools SET is_active = ? WHERE id = ?',
                    (new_status, school['id'])
                )
                conn.commit()
                
                status_text = "تم تفعيل" if new_status else "تم إيقاف"
                flash(f'{status_text} المدرسة بنجاح', 'success')
                logger.info(f"{status_text} المدرسة: {school_name}")
            else:
                flash('المدرسة غير موجودة', 'error')
                
    except Exception as e:
        logger.error(f"خطأ في تغيير حالة المدرسة: {e}")
        flash('خطأ في تحديث حالة المدرسة', 'error')
    
    return redirect(url_for('super_admin'))

@app.route('/delete_school/<school_name>', methods=['POST'])
def delete_school(school_name):
    """حذف مدرسة"""
    try:
        with get_db() as conn:
            school = conn.execute(
                'SELECT id FROM schools WHERE name = ?', (school_name,)
            ).fetchone()
            
            if school:
                # حذف البيانات المرتبطة
                conn.execute('DELETE FROM student_names WHERE school_id = ?', (school['id'],))
                conn.execute('DELETE FROM school_settings WHERE school_id = ?', (school['id'],))
                conn.execute('DELETE FROM schools WHERE id = ?', (school['id'],))
                conn.commit()
                
                flash('تم حذف المدرسة بنجاح', 'success')
                logger.info(f"تم حذف المدرسة: {school_name}")
            else:
                flash('المدرسة غير موجودة', 'error')
                
    except Exception as e:
        logger.error(f"خطأ في حذف المدرسة: {e}")
        flash('خطأ في حذف المدرسة', 'error')
    
    return redirect(url_for('super_admin'))

# WebSocket Events
@socketio.on('join')
def on_join(data):
    """انضمام المستخدم لغرفة المدرسة"""
    school_name = data.get('school_name')
    if not school_name:
        return
    
    join_room(school_name)
    school_data = get_school_by_name(school_name)
    
    if school_data:
        emit('current_names', {'names': school_data['recent_names']}, room=school_name)
        emit('update_settings', {'settings': school_data['settings']}, room=school_name)
    
    logger.info(f"مستخدم انضم لغرفة: {school_name}")

@socketio.on('submit_name')
def handle_submit_name(data):
    """معالجة إرسال اسم طالب جديد"""
    school_name = data.get('school_name')
    student_name = data.get('name', '').strip()
    
    if not school_name or not student_name:
        emit('error', {'message': 'بيانات غير مكتملة'})
        return
    
    is_valid, error_msg = validate_student_name(student_name)
    if not is_valid:
        emit('error', {'message': error_msg})
        return
    
    try:
        school_data = get_school_by_name(school_name)
        if not school_data or not school_data['is_active']:
            emit('error', {'message': 'المدرسة غير متاحة'})
            return
        
        with get_db() as conn:
            conn.execute(
                'INSERT INTO student_names (school_id, name) VALUES (?, ?)',
                (school_data['id'], student_name)
            )
            conn.commit()
            
            # الحصول على آخر 12 اسم
            recent_names = conn.execute(
                '''SELECT name FROM student_names 
                   WHERE school_id = ? 
                   ORDER BY submitted_at DESC 
                   LIMIT 12''', (school_data['id'],)
            ).fetchall()
            
            names_list = [row['name'] for row in recent_names]
        
        emit('new_name', {
            'name': student_name, 
            'names': names_list
        }, room=school_name)
        
        logger.info(f"تم إضافة اسم جديد: {student_name} للمدرسة: {school_name}")
        
    except Exception as e:
        logger.error(f"خطأ في إضافة الاسم: {e}")
        emit('error', {'message': 'خطأ في حفظ الاسم'})

@socketio.on('update_school_settings')
def handle_update_school_settings(data):
    """تحديث إعدادات المدرسة"""
    school_name = data.get('school_name')
    new_settings = data.get('settings', {})
    
    if not school_name:
        return
    
    try:
        school_data = get_school_by_name(school_name)
        if not school_data:
            emit('error', {'message': 'المدرسة غير موجودة'})
            return
        
        with get_db() as conn:
            conn.execute(
                '''UPDATE school_settings 
                   SET background_color = ?, text_color = ?, font_size = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE school_id = ?''',
                (
                    new_settings.get('background_color', '#ffffff'),
                    new_settings.get('text_color', '#000000'),
                    new_settings.get('font_size', '24px'),
                    school_data['id']
                )
            )
            conn.commit()
        
        emit('update_settings', {'settings': new_settings}, room=school_name)
        logger.info(f"تم تحديث إعدادات المدرسة: {school_name}")
        
    except Exception as e:
        logger.error(f"خطأ في تحديث الإعدادات: {e}")
        emit('error', {'message': 'خطأ في حفظ الإعدادات'})

@socketio.on('clear_names')
def handle_clear_names(data):
    """مسح جميع الأسماء"""
    school_name = data.get('school_name')
    
    if not school_name:
        return
    
    try:
        school_data = get_school_by_name(school_name)
        if not school_data:
            return
        
        with get_db() as conn:
            conn.execute('DELETE FROM student_names WHERE school_id = ?', (school_data['id'],))
            conn.commit()
        
        emit('current_names', {'names': []}, room=school_name)
        logger.info(f"تم مسح أسماء المدرسة: {school_name}")
        
    except Exception as e:
        logger.error(f"خطأ في مسح الأسماء: {e}")

# معالج الأخطاء
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"خطأ داخلي: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    logger.info("تم تشغيل التطبيق")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)