/* MAS tour — floating chatbot widget */
(function () {
    'use strict';

    const script = document.currentScript || document.querySelector('script[data-chatbot-url]');
    const API_URL = script.dataset.chatbotUrl;
    const WELCOME_MESSAGE = '¡Hola! 🇨🇺 Soy el asistente virtual de MAS tour. ¿Cómo puedo ayudarte a explorar Cuba hoy?';

    const root = document.getElementById('chatbot');
    const fab = document.getElementById('chatbot-fab');
    const body = document.getElementById('chatbot-body');
    const quickReplies = document.getElementById('chatbot-quick-replies');
    const form = document.getElementById('chatbot-form');
    const input = document.getElementById('chatbot-input');
    const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;

    let historyLoaded = false;
    let sending = false;

    function currentTime() {
        return new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function linkify(escapedText) {
        return escapedText.replace(
            /(https?:\/\/[^\s<]+|(?:^|(?<=[\s(]))\/[a-z0-9\-]+(?:\/[a-z0-9\-]+)*\/?)/gi,
            function (url) {
                return '<a href="' + url + '">' + url + '</a>';
            }
        );
    }

    function appendMessage(role, text, time) {
        const row = document.createElement('div');
        row.className = 'chatbot__row chatbot__row--' + role;
        const bubble =
            '<div class="chatbot__bubble chatbot__bubble--' + role + '">' +
            '<p class="chatbot__text">' + linkify(escapeHtml(text)) + '</p>' +
            '<span class="chatbot__time">' + (time || currentTime()) + '</span>' +
            '</div>';
        if (role === 'assistant') {
            row.innerHTML =
                '<span class="chatbot__bot-badge">' +
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>' +
                '</span>' + bubble;
        } else {
            row.innerHTML = bubble;
        }
        body.insertBefore(row, quickReplies);
        body.scrollTop = body.scrollHeight;
        return row;
    }

    function appendTyping() {
        const row = document.createElement('div');
        row.className = 'chatbot__row chatbot__row--assistant chatbot__row--typing';
        row.innerHTML =
            '<span class="chatbot__bot-badge">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>' +
            '</span>' +
            '<div class="chatbot__bubble chatbot__bubble--assistant chatbot__typing">' +
            '<span></span><span></span><span></span></div>';
        body.insertBefore(row, quickReplies);
        body.scrollTop = body.scrollHeight;
        return row;
    }

    function loadHistory() {
        if (historyLoaded) return;
        historyLoaded = true;
        fetch(API_URL, { headers: { 'Accept': 'application/json' } })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.messages.length === 0) {
                    appendMessage('assistant', WELCOME_MESSAGE);
                    return;
                }
                data.messages.forEach(function (message) {
                    appendMessage(message.role, message.content, message.time);
                });
                quickReplies.hidden = true;
            })
            .catch(function () {
                appendMessage('assistant', WELCOME_MESSAGE);
            });
    }

    function sendMessage(text) {
        if (sending || !text) return;
        sending = true;
        quickReplies.hidden = true;
        appendMessage('user', text);
        const typingRow = appendTyping();
        fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ message: text }),
        })
            .then(function (response) {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            })
            .then(function (data) {
                typingRow.remove();
                appendMessage('assistant', data.reply, data.time);
            })
            .catch(function () {
                typingRow.remove();
                appendMessage('assistant', 'Lo siento, hubo un problema de conexión 😔. Inténtalo de nuevo.');
            })
            .finally(function () {
                sending = false;
            });
    }

    function openChat() {
        root.classList.add('chatbot--open');
        fab.setAttribute('aria-expanded', 'true');
        loadHistory();
        input.focus();
    }

    function closeChat() {
        root.classList.remove('chatbot--open');
        fab.setAttribute('aria-expanded', 'false');
    }

    fab.addEventListener('click', function () {
        if (root.classList.contains('chatbot--open')) closeChat();
        else openChat();
    });

    root.querySelectorAll('[data-chatbot-close]').forEach(function (element) {
        element.addEventListener('click', closeChat);
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && root.classList.contains('chatbot--open')) closeChat();
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        const text = input.value.trim();
        input.value = '';
        sendMessage(text);
    });

    quickReplies.querySelectorAll('[data-chatbot-quick]').forEach(function (chip) {
        chip.addEventListener('click', function () {
            sendMessage(chip.textContent.trim());
        });
    });
})();
