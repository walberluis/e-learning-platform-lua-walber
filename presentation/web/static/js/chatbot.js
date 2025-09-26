// Chatbot JavaScript - AI Assistant Integration

// Chatbot state
let chatHistory = [];
let isTyping = false;
let currentUserId = null;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const quickActionBtns = document.querySelectorAll('.quick-action-btn');

// Initialize chatbot
function initChat() {
    // Check if user is authenticated
    if (!window.elearning?.isAuthenticated) {
        console.error('User not authenticated');
        showModal('loginModal');
        return;
    }
    
    currentUserId = window.elearning?.getCurrentUser()?.id;
    
    if (!currentUserId) {
        console.error('User not logged in');
        showModal('loginModal');
        return;
    }
    
    setupChatEventListeners();
    loadChatHistory();
    
    console.log('Chatbot initialized for user:', currentUserId);
}

// Setup event listeners
function setupChatEventListeners() {
    // Send message button
    sendMessageBtn.addEventListener('click', sendMessage);
    
    // Enter key to send message
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Quick action buttons
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const message = btn.dataset.message;
            if (message) {
                chatInput.value = message;
                sendMessage();
            }
        });
    });
    
    // Auto-resize chat input
    chatInput.addEventListener('input', autoResizeInput);
}

// Load chat history
async function loadChatHistory() {
    try {
        const response = await ChatbotAPI.getHistory(currentUserId, 10);
        
        if (response.success && response.data.history) {
            chatHistory = response.data.history;
            renderChatHistory();
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Render chat history
function renderChatHistory() {
    // Clear existing messages except welcome message
    const welcomeMessage = chatMessages.querySelector('.message.bot-message');
    chatMessages.innerHTML = '';
    
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }
    
    // Render history messages
    chatHistory.forEach(entry => {
        addMessageToChat(entry.user_message, 'user', false);
        addMessageToChat(entry.bot_response, 'bot', false);
    });
    
    scrollToBottom();
}

// Send message
async function sendMessage() {
    // Check authentication before sending
    if (!window.elearning?.isAuthenticated) {
        showModal('loginModal');
        return;
    }
    
    const message = chatInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    chatInput.value = '';
    autoResizeInput();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send message to API
        const response = await ChatbotAPI.sendMessage(currentUserId, message);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (response.success) {
            // Add bot response to chat
            addMessageToChat(response.data.response, 'bot');
            
            // Update chat history
            chatHistory.push({
                timestamp: new Date().toISOString(),
                user_message: message,
                bot_response: response.data.response,
                intent: response.data.metadata?.intent || 'unknown'
            });
            
            // Handle special intents
            handleSpecialIntent(response.data.metadata);
            
        } else {
            addMessageToChat('Desculpe, estou com dificuldades para responder agora. Tente novamente.', 'bot');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessageToChat('Erro de conexão. Verifique sua internet e tente novamente.', 'bot');
    }
}

// Add message to chat
function addMessageToChat(message, sender, animate = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (animate) {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Process message content (handle markdown-like formatting)
    const processedMessage = processMessageContent(message);
    content.innerHTML = processedMessage;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    if (animate) {
        // Animate message appearance
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
    }
    
    scrollToBottom();
}

// Process message content (basic markdown-like formatting)
function processMessageContent(message) {
    return message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
        .replace(/`(.*?)`/g, '<code>$1</code>') // Code
        .replace(/\n/g, '<br>') // Line breaks
        .replace(/📚|🎯|📖|⭐|⏱️|🔥|🌟|👍|💪|📊|🤖|💡/g, '<span class="emoji">$&</span>'); // Emojis
}

// Show typing indicator
function showTypingIndicator() {
    if (document.querySelector('.typing-indicator')) return;
    
    isTyping = true;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = `
        <div class="typing-animation">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(content);
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    isTyping = false;
}

// Handle special intents
function handleSpecialIntent(metadata) {
    if (!metadata) return;
    
    const intent = metadata.intent;
    
    switch (intent) {
        case 'recommendation':
            // Could trigger loading of recommendations in dashboard
            if (typeof loadDashboard === 'function') {
                setTimeout(loadDashboard, 1000);
            }
            break;
            
        case 'progress':
            // Could show progress modal or redirect to dashboard
            showProgressSummary();
            break;
            
        case 'course_info':
            // Could show course catalog
            if (typeof showSection === 'function') {
                setTimeout(() => showSection('trilhas'), 2000);
            }
            break;
    }
}

// Show progress summary
async function showProgressSummary() {
    if (!currentUserId) return;
    
    try {
        const response = await UserAPI.getAnalytics(currentUserId);
        
        if (response.success) {
            const analytics = response.data;
            
            // Create progress summary message
            const summaryMessage = `
                📊 **Seu Resumo de Progresso:**
                
                🎯 Taxa de Conclusão: ${analytics.completion_rate || 0}%
                📚 Atividades Totais: ${analytics.total_activities || 0}
                ⭐ Nota Média: ${analytics.average_grade_all_time || 0}/100
                ⏱️ Tempo de Estudo: ${analytics.total_study_time_hours || 0}h
                🔥 Sequência: ${analytics.learning_streak || 0} dias
            `;
            
            setTimeout(() => {
                addMessageToChat(summaryMessage, 'bot');
            }, 1500);
        }
    } catch (error) {
        console.error('Error getting progress summary:', error);
    }
}

// Auto-resize input
function autoResizeInput() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

// Scroll to bottom
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Clear chat history
async function clearChatHistory() {
    if (!confirm('Tem certeza que deseja limpar o histórico de conversa?')) {
        return;
    }
    
    try {
        const response = await ChatbotAPI.clearHistory(currentUserId);
        
        if (response.success) {
            // Clear local history
            chatHistory = [];
            
            // Clear chat messages except welcome
            const welcomeMessage = chatMessages.querySelector('.message.bot-message');
            chatMessages.innerHTML = '';
            
            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }
            
            window.elearning?.showNotification('Histórico de conversa limpo!', 'success');
        }
    } catch (error) {
        console.error('Error clearing chat history:', error);
        window.elearning?.showNotification('Erro ao limpar histórico.', 'error');
    }
}

// Get quick help
async function getQuickHelp(topic) {
    if (!currentUserId) return;
    
    showTypingIndicator();
    
    try {
        const response = await ChatbotAPI.getQuickHelp(currentUserId, topic);
        
        hideTypingIndicator();
        
        if (response.success) {
            addMessageToChat(`💡 **Ajuda Rápida: ${topic}**\n\n${response.data.response}`, 'bot');
        }
    } catch (error) {
        console.error('Error getting quick help:', error);
        hideTypingIndicator();
        addMessageToChat('Não consegui obter ajuda sobre esse tópico agora.', 'bot');
    }
}

// Submit feedback
async function submitChatFeedback(rating, feedback = null) {
    if (!currentUserId) return;
    
    try {
        const response = await ChatbotAPI.submitFeedback(currentUserId, rating, feedback);
        
        if (response.success) {
            window.elearning?.showNotification('Obrigado pelo seu feedback!', 'success');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
        window.elearning?.showNotification('Erro ao enviar feedback.', 'error');
    }
}

// Voice input (if supported)
function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        window.elearning?.showNotification('Reconhecimento de voz não suportado neste navegador.', 'warning');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'pt-BR';
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = () => {
        chatInput.placeholder = 'Ouvindo... Fale agora!';
        chatInput.style.borderColor = 'var(--error-color)';
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendMessage();
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        window.elearning?.showNotification('Erro no reconhecimento de voz.', 'error');
    };
    
    recognition.onend = () => {
        chatInput.placeholder = 'Digite sua mensagem...';
        chatInput.style.borderColor = 'var(--gray-300)';
    };
    
    recognition.start();
}

// Export functions
window.chatbot = {
    init: initChat,
    sendMessage,
    clearHistory: clearChatHistory,
    getQuickHelp,
    submitFeedback: submitChatFeedback,
    startVoiceInput
};

// Add CSS for typing animation
const style = document.createElement('style');
style.textContent = `
    .typing-animation {
        display: flex;
        gap: 4px;
        padding: 8px 0;
    }
    
    .typing-animation span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary-color);
        animation: typing 1.4s ease-in-out infinite;
    }
    
    .typing-animation span:nth-child(1) { animation-delay: 0s; }
    .typing-animation span:nth-child(2) { animation-delay: 0.2s; }
    .typing-animation span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
    
    .emoji {
        font-size: 1.2em;
    }
    
    .message-content code {
        background: var(--gray-100);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    .message-content strong {
        font-weight: 600;
        color: var(--gray-900);
    }
    
    .user-message .message-content strong {
        color: var(--white);
    }
`;

document.head.appendChild(style);
