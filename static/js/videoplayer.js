(function () {
    'use strict';

    document.querySelectorAll('.js-player').forEach(function (el) {
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

        const player = new Plyr(el, {
            fullscreen: {
                enabled: true,
                fallback: true,    // ОБЯЗАТЕЛЬНО true, иначе Plyr удаляет кнопку из верстки на iOS
                iosNative: 'native',
            },
            controls: [
                'play-large', 'restart', 'rewind', 'play',
                'fast-forward', 'progress', 'current-time', 'duration',
                'volume', 'settings', 'pip', 'fullscreen', 'download'
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

        // Обработка перехода в полноэкранный режим
        player.on('enterfullscreen', function () {
            // На iOS запускаем нативный системный видеоплеер Apple
            if (isIOS && el.webkitEnterFullscreen) {
                el.webkitEnterFullscreen();
                return;
            }

            // На Android и десктопах вызываем Fullscreen API браузера
            const container = player.elements.container;
            if (container && container.requestFullscreen) {
                container.requestFullscreen().catch(function () {});
            } else if (container && container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            }
        });

        player.on('exitfullscreen', function () {
            if (document.fullscreenElement || document.webkitFullscreenElement) {
                if (document.exitFullscreen) {
                    document.exitFullscreen().catch(function () {});
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                }
            }
        });

        // Запоминание позиции
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