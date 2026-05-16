(function () {
    const csrfToken = getCookie('csrftoken');

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const cookie of cookies) {
            const [rawKey, ...rawValue] = cookie.trim().split('=');
            if (rawKey === name) return decodeURIComponent(rawValue.join('='));
        }
        return '';
    }

    const menuButton = document.querySelector('[data-menu-toggle]');
    const menu = document.querySelector('[data-menu]');
    if (menuButton && menu) {
        menuButton.addEventListener('click', () => menu.classList.toggle('open'));
    }

    const formCard = document.querySelector('.form-card');
    if (formCard) {
        const modelsScript = document.querySelector('#car-models-data');
        let models = {};
        try {
            models = modelsScript ? JSON.parse(modelsScript.textContent) : JSON.parse(formCard.dataset.carModels || '{}');
        } catch (e) {
            models = {};
        }
        const brand = document.querySelector('#id_brand');
        const model = document.querySelector('#id_model');
        const currentModel = model ? model.dataset.currentModel : '';
        const appendModelOption = (parent, item) => {
            const option = document.createElement('option');
            option.value = item;
            option.textContent = item;
            if (item === currentModel) option.selected = true;
            parent.appendChild(option);
        };
        const rebuildModels = () => {
            if (!brand || !model) return;
            const selectedBrand = brand.value;
            model.innerHTML = '<option value="">Выберите модель</option>';
            if (selectedBrand) {
                (models[selectedBrand] || []).forEach((item) => appendModelOption(model, item));
                return;
            }
            Object.entries(models).forEach(([brandName, brandModels]) => {
                const group = document.createElement('optgroup');
                group.label = brandName;
                brandModels.forEach((item) => appendModelOption(group, item));
                model.appendChild(group);
            });
        };
        if (brand && model) {
            brand.addEventListener('change', rebuildModels);
            rebuildModels();
        }
    }

    document.querySelectorAll('[data-ajax-field]').forEach((wrapper) => {
        const input = wrapper.querySelector('input');
        const hint = wrapper.querySelector('.field-hint');
        const url = wrapper.dataset.url;
        if (!input || !hint || !url) return;

        let timer = null;
        input.addEventListener('input', () => {
            window.clearTimeout(timer);
            timer = window.setTimeout(async () => {
                const param = input.name.includes('phone') ? 'phone' : 'email';
                const carId = document.querySelector('[name="car_id"]')?.value || '';
                const query = new URLSearchParams({ [param]: input.value, car_id: carId });
                try {
                    const response = await fetch(`${url}?${query}`);
                    const data = await response.json();
                    hint.textContent = data.message;
                    hint.className = `field-hint ${data.valid && !data.exists ? 'ok' : 'bad'}`;
                } catch (e) {
                    hint.textContent = 'Не удалось проверить поле.';
                    hint.className = 'field-hint bad';
                }
            }, 450);
        });
    });

    document.querySelectorAll('[data-favorite-url]').forEach((button) => {
        button.addEventListener('click', async () => {
            try {
                const response = await fetch(button.dataset.favoriteUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                });
                if (response.status === 403) return;
                const data = await response.json();
                button.classList.toggle('active', data.is_favorite);
                if (button.textContent.trim().length > 1) {
                    button.textContent = data.is_favorite ? 'В избранном' : 'В избранное';
                }
            } catch (e) {
                console.warn('Favorite request failed', e);
            }
        });
    });

    const deferredPanel = document.querySelector('[data-deferred-panel]');
    if (deferredPanel) {
        const statsUrl = deferredPanel.dataset.statsUrl;
        const latestUrl = deferredPanel.dataset.latestUrl;
        Promise.all([fetch(statsUrl), fetch(latestUrl)])
            .then(async ([statsResponse, latestResponse]) => [await statsResponse.json(), await latestResponse.json()])
            .then(([stats, latest]) => {
                Object.keys(stats).forEach((key) => {
                    const el = deferredPanel.querySelector(`[data-stat="${key}"]`);
                    if (el) el.textContent = stats[key];
                });
                const list = deferredPanel.querySelector('[data-latest-list]');
                if (list && latest.items) {
                    list.innerHTML = latest.items.map((item) => `<li><a href="${item.detail_url}">${item.title}</a> — ${item.city}</li>`).join('');
                }
            })
            .catch(() => {});
    }
})();
