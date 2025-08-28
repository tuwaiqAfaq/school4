// إعداد WebSocket
const socket = io();

// الانضمام إلى room الخاص بالمدرسة
socket.emit('join', {school_name: schoolName});

// معالج إرسال النموذج
document.getElementById('nameForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const studentName = document.getElementById('studentName').value.trim();
    const messageDiv = document.getElementById('message');
    
    if (studentName === '') {
        showMessage('يرجى إدخال اسم الطالب', 'error');
        return;
    }
    
    // إرسال الاسم عبر WebSocket
    socket.emit('submit_name', {
        school_name: schoolName,
        name: studentName
    });
    
    // مسح الحقل وإظهار رسالة نجاح
    document.getElementById('studentName').value = '';
    showMessage('تم إرسال الاسم بنجاح!', 'success');
    
    // إخفاء الرسالة بعد 3 ثوان
    setTimeout(() => {
        messageDiv.innerHTML = '';
        messageDiv.className = 'message';
    }, 3000);
});

// دالة لإظهار الرسائل
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = text;
    messageDiv.className = `message ${type}`;
}

// معالج الأخطاء
socket.on('connect_error', function(error) {
    showMessage('خطأ في الاتصال بالخادم', 'error');
});

socket.on('disconnect', function() {
    showMessage('تم قطع الاتصال بالخادم', 'error');
});

// إعادة الاتصال
socket.on('connect', function() {
    console.log('تم الاتصال بالخادم');
    socket.emit('join', {school_name: schoolName});
});

// التركيز على حقل الإدخال عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('studentName').focus();
});

// إضافة تأثير الضغط على Enter
document.getElementById('studentName').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('nameForm').dispatchEvent(new Event('submit'));
    }
});

