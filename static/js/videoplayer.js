(function () {
    'use strict';

    document.querySelectorAll('.js-player').forEach(function (el) {
        const player = new Plyr(el, {
            controls: [
                'play-large', 'restart', 'rewind', 'play',
                'fast-forward', 'progress', 'current-time', 'duration',
                'mute', 'volume', 'settings', 'pip', 'airplay',
                'download', 'fullscreen'
            ],
            settings: ['speed'],
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] },
            keyboard: { focused: true, global: false },
            tooltips: { controls: true, seek: true },
            i18n: {
                restart: 'Заново',
                rewind: 'Назад {seektime} сек',
                play: 'Играть',
                pause: 'Пауза',
                fastForward: 'Вперёд {seektime} сек',
                seek: 'Перемотка',
                played: 'Проиграно',
                buffered: 'Буфер',
                currentTime: 'Текущее время',
                duration: 'Длительность',
                volume: 'Громкость',
                mute: 'Без звука',
                unmute: 'Со звуком',
                enterFullscreen: 'На весь экран',
                exitFullscreen: 'Выйти из полноэкранного',
                settings: 'Настройки',
                speed: 'Скорость',
                normal: 'Обычная',
                quality: 'Качество',
                loop: 'Повтор',
                start: 'Начало',
                end: 'Конец',
                all: 'Все',
                reset: 'Сброс',
                disabled: 'Выкл',
                enabled: 'Вкл',
                advertisement: 'Реклама',
            },
        });

        // запоминание позиции
        const src = el.querySelector('source')?.src;
        if (!src) return;

        const key = 'video-pos:' + src;
        const SAVE_INTERVAL = 3000;
        const MIN_POS = 5;
        const END_OFFSET = 10;

        player.on('loadedmetadata', function () {
            const saved = parseFloat(localStorage.getItem(key));
            if (saved && saved > MIN_POS && saved < player.duration - END_OFFSET) {
                player.currentTime = saved;
            }
        });

        let lastSave = 0;
        player.on('timeupdate', function () {
            if (Date.now() - lastSave > SAVE_INTERVAL) {
                localStorage.setItem(key, player.currentTime);
                lastSave = Date.now();
            }
        });

        window.addEventListener('beforeunload', function () {
            localStorage.setItem(key, player.currentTime);
        });
    });
})();