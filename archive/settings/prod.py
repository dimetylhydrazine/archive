from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['192.168.1.103', '10.8.1.31', 'localhost'])

# Безопасность
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_TRUSTED_ORIGINS = [
    'http://192.168.1.103',
    'http://10.8.1.31',
]

# Логи в файл (не только в консоль)
LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'app.log',
    'maxBytes': 5 * 1024 * 1024,
    'backupCount': 3,
    'formatter': 'verbose',
    'encoding': 'utf-8',
}
LOGGING['root']['handlers'] = ['console', 'file']
LOGGING['loggers']['videoplayer']['handlers'] = ['console', 'file']