// إعداد WebSocket
const socket = io();

// الانضمام إلى room الخاص بالمدرسة
socket.emit('join', {school_name: schoolName});

// تطبيق الإعدادات الحالية على المعاينة
applyPreviewSettings(currentSettings);

// معالج تغيير الإعدادات
document.getElementById('settingsForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const backgroundColor = document.getElementById('backgroundColor').value;
    const textColor = document.getElementById('textColor').value;
    const fontSize = document.getElementById('fontSize').value;
    
    const newSettings = {
        background_color: backgroundColor,
        text_color: textColor,
        font_size: fontSize,
        logo: currentSettings.logo // الاحتفاظ بالشعار الحالي
    };
    
    // إرسال الإعدادات الجديدة عبر WebSocket
    socket.emit('update_school_settings', {
        school_name: schoolName,
        settings: newSettings
    });
    
    // تحديث المعاينة
    applyPreviewSettings(newSettings);
    
    // إظهار رسالة نجاح
    showMessage('تم حفظ الإعدادات بنجاح!', 'success');
});

// معالج تغيير الإعدادات في الوقت الفعلي (للمعاينة)
document.getElementById('backgroundColor').addEventListener('input', updatePreview);
document.getElementById('textColor').addEventListener('input', updatePreview);
document.getElementById('fontSize').addEventListener('change', updatePreview);

function updatePreview() {
    const backgroundColor = document.getElementById('backgroundColor').value;
    const textColor = document.getElementById('textColor').value;
    const fontSize = document.getElementById('fontSize').value;
    
    const previewSettings = {
        background_color: backgroundColor,
        text_color: textColor,
        font_size: fontSize,
        logo: currentSettings.logo
    };
    
    applyPreviewSettings(previewSettings);
}

// دالة تطبيق الإعدادات على المعاينة
function applyPreviewSettings(settings) {
    const preview = document.getElementById('preview');
    const title = preview.querySelector('h4');
    const nameItems = preview.querySelectorAll('.name-item');
    
    preview.style.backgroundColor = settings.background_color;
    preview.style.color = settings.text_color;
    preview.style.fontSize = settings.font_size;
    
    if (title) {
        title.style.color = settings.text_color;
    }
    
    nameItems.forEach(item => {
        item.style.color = settings.text_color;
        item.style.borderRightColor = settings.text_color;
    });
}

// معالج رفع الشعار
document.getElementById('logoUpload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const logoData = e.target.result;
            
            // حفظ الشعار في الإعدادات
            currentSettings.logo = logoData;
            
            // إرسال الإعدادات المحدثة
            socket.emit('update_school_settings', {
                school_name: schoolName,
                settings: currentSettings
            });
            
            showMessage('تم رفع الشعار بنجاح!', 'success');
        };
        reader.readAsDataURL(file);
    }
});

// دالة إظهار الرسائل
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = text;
    messageDiv.className = `message ${type}`;
    
    // إخفاء الرسالة بعد 5 ثوان
    setTimeout(() => {
        messageDiv.innerHTML = '';
        messageDiv.className = 'message';
    }, 5000);
}

// استقبال تأكيد تحديث الإعدادات
socket.on('update_settings', function(data) {
    currentSettings = data.settings;
    console.log('تم تحديث الإعدادات:', data.settings);
});

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

// إضافة أزرار إعادة تعيين
document.addEventListener('DOMContentLoaded', function() {
    // إضافة زر إعادة تعيين الألوان
    const resetButton = document.createElement('button');
    resetButton.type = 'button';
    resetButton.textContent = 'إعادة تعيين الألوان الافتراضية';
    resetButton.style.backgroundColor = '#95a5a6';
    resetButton.style.marginTop = '10px';
    
    resetButton.addEventListener('click', function() {
        document.getElementById('backgroundColor').value = '#ffffff';
        document.getElementById('textColor').value = '#000000';
        document.getElementById('fontSize').value = '24px';
        updatePreview();
    });
    
    document.getElementById('settingsForm').appendChild(resetButton);
});

// دالة لفتح شاشة العرض في نافذة جديدة
function openDisplayWindow() {
    const displayUrl = `/${schoolName}/display`;
    window.open(displayUrl, '_blank', 'fullscreen=yes');
}

// إضافة زر فتح شاشة العرض
document.addEventListener('DOMContentLoaded', function() {
    const openDisplayButton = document.createElement('button');
    openDisplayButton.type = 'button';
    openDisplayButton.textContent = 'فتح شاشة العرض';
    openDisplayButton.style.backgroundColor = '#27ae60';
    openDisplayButton.style.marginTop = '10px';
    
    openDisplayButton.addEventListener('click', openDisplayWindow);
    
    document.querySelector('.links-section').appendChild(openDisplayButton);
});

