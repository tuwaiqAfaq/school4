// إعداد WebSocket
const socket = io();

// متغير لتخزين الأسماء الحالية
let currentNames = [];

// الانضمام إلى room الخاص بالمدرسة
socket.emit('join', {school_name: schoolName});

// تطبيق الإعدادات الأولية
applySettings(initialSettings);

// استقبال الأسماء الحالية
socket.on('current_names', function(data) {
    currentNames = data.names || [];
    updateNamesList(currentNames, false); // false = لا تطبق أنيميشن الدخول
});

// استقبال اسم جديد
socket.on('new_name', function(data) {
    const newNames = data.names || [];
    const newName = data.name;
    
    // التحقق من وجود أسماء جديدة
    const addedNames = newNames.filter(name => !currentNames.includes(name));
    
    currentNames = newNames;
    updateNamesList(currentNames, true, addedNames); // true = طبق أنيميشن للأسماء الجديدة فقط
});

// استقبال تحديث الإعدادات
socket.on('update_settings', function(data) {
    applySettings(data.settings);
});

// دالة تحديث قائمة الأسماء المحسنة
function updateNamesList(names, animateNew = false, newNames = []) {
    const namesList = document.getElementById('namesList');
    
    if (names.length === 0) {
        namesList.innerHTML = '<div class="no-names">لا توجد أسماء حتى الآن</div>';
        return;
    }
    
    namesList.innerHTML = '';
    
    names.forEach((name, index) => {
        const nameDiv = document.createElement('div');
        nameDiv.className = 'name-display';
        nameDiv.textContent = name;
        
        // تطبيق الأنيميشن فقط على الأسماء الجديدة
        if (animateNew && newNames.includes(name)) {
            nameDiv.style.animation = 'slideIn 0.8s ease-out forwards';
            nameDiv.style.transform = 'scale(0)'; // البداية
        } else {
            // للأسماء الموجودة مسبقاً - أظهرها مباشرة
            nameDiv.style.animation = 'none';
            nameDiv.style.transform = 'scale(1)';
            nameDiv.style.opacity = '1';
        }
        
        namesList.appendChild(nameDiv);
    });
}

// دالة تطبيق الإعدادات
function applySettings(settings) {
    const body = document.getElementById('displayBody');
    const title = document.getElementById('schoolTitle');
    const logo = document.getElementById('schoolLogo');
    
    // تطبيق الألوان
    body.style.backgroundColor = settings.background_color || '#ffffff';
    body.style.color = settings.text_color || '#000000';
    
    // تطبيق حجم الخط
    body.style.fontSize = settings.font_size || '24px';
    
    // تطبيق الشعار
    if (settings.logo && settings.logo !== '') {
        logo.src = settings.logo;
        logo.style.display = 'block';
    } else {
        logo.style.display = 'none';
    }
    
    // تحديث لون العناوين
    title.style.color = settings.text_color || '#000000';
    const namesHeader = document.querySelector('.names-container h2');
    if (namesHeader) {
        namesHeader.style.color = settings.text_color || '#2c3e50';
    }
}

// دالة محسنة لتسليط الضوء على الاسم الجديد
function highlightNewName(newName) {
    setTimeout(() => {
        const nameElements = document.querySelectorAll('.name-display');
        nameElements.forEach(element => {
            if (element.textContent === newName) {
                // إضافة تأثير النبض للاسم الجديد
                element.classList.add('new-name-highlight');
                
                // إزالة التأثير بعد 3 ثوان
                setTimeout(() => {
                    element.classList.remove('new-name-highlight');
                }, 3000);
            }
        });
    }, 100);
}

// إضافة الستايلات للتأثير الجديد
const highlightStyle = document.createElement('style');
highlightStyle.textContent = `
    .new-name-highlight {
        animation: newNamePulse 1s ease-in-out 3 !important;
        box-shadow: 0 0 20px rgba(52, 152, 219, 0.8) !important;
    }
    
    @keyframes newNamePulse {
        0%, 100% { 
            transform: scale(1);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        50% { 
            transform: scale(1.05);
            box-shadow: 0 12px 24px rgba(52, 152, 219, 0.4);
        }
    }
`;
document.head.appendChild(highlightStyle);

// معالج الأخطاء
socket.on('connect_error', function(error) {
    console.error('خطأ في الاتصال:', error);
});

socket.on('disconnect', function() {
    console.log('تم قطع الاتصال بالخادم');
});

// إعادة الاتصال
socket.on('connect', function() {
    console.log('تم الاتصال بالخادم');
    socket.emit('join', {school_name: schoolName});
});

// معالج الأخطاء من الخادم
socket.on('error', function(data) {
    console.error('خطأ من الخادم:', data.message);
});

// منع النقر بالزر الأيمن وF12 (لحماية شاشة العرض)
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
        e.preventDefault();
    }
});

// تحديث الوقت (اختياري)
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ar-SA');
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

// تحديث الوقت كل ثانية (اختياري)
// setInterval(updateTime, 1000);