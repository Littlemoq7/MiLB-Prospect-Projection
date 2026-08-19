(function () {
    const input = document.getElementById('name-input');
    const list = document.getElementById('name-suggestions');
    if (!input || !list) return;

    let activeIndex = -1;
    let controller = null;
    let debounceTimer = null;

    function clearSuggestions() {
        list.innerHTML = '';
        list.hidden = true;
        activeIndex = -1;
    }

    function selectSuggestion(name) {
        input.value = name;
        clearSuggestions();
    }

    function renderSuggestions(names) {
        list.innerHTML = '';
        if (!names.length) {
            list.hidden = true;
            return;
        }
        names.forEach((name) => {
            const item = document.createElement('li');
            item.textContent = name;
            // mousedown (not click) fires before the input's blur handler,
            // so the suggestion is still in the DOM when it's selected.
            item.addEventListener('mousedown', (event) => {
                event.preventDefault();
                selectSuggestion(name);
            });
            list.appendChild(item);
        });
        activeIndex = -1;
        list.hidden = false;
    }

    function updateActive(items) {
        items.forEach((item, i) => item.classList.toggle('active', i === activeIndex));
        if (activeIndex >= 0) items[activeIndex].scrollIntoView({ block: 'nearest' });
    }

    input.addEventListener('input', () => {
        const query = input.value.trim();
        clearTimeout(debounceTimer);
        if (!query) {
            clearSuggestions();
            return;
        }
        debounceTimer = setTimeout(() => {
            if (controller) controller.abort();
            controller = new AbortController();
            fetch(`/api/player-names?q=${encodeURIComponent(query)}`, { signal: controller.signal })
                .then((res) => (res.ok ? res.json() : []))
                .then(renderSuggestions)
                .catch((err) => {
                    if (err.name !== 'AbortError') clearSuggestions();
                });
        }, 150);
    });

    input.addEventListener('keydown', (event) => {
        const items = Array.from(list.children);
        if (list.hidden || !items.length) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            activeIndex = (activeIndex + 1) % items.length;
            updateActive(items);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            activeIndex = (activeIndex - 1 + items.length) % items.length;
            updateActive(items);
        } else if (event.key === 'Enter') {
            if (activeIndex >= 0) {
                event.preventDefault();
                selectSuggestion(items[activeIndex].textContent);
            }
        } else if (event.key === 'Escape') {
            clearSuggestions();
        }
    });

    input.addEventListener('blur', () => {
        setTimeout(clearSuggestions, 100);
    });
})();
