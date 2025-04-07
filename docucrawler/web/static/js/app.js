// DocuCrawler Web Application

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchResults = document.getElementById('search-results');
const collectionSelect = document.getElementById('collection-select');
const dbTypeSelect = document.getElementById('db-type-select');
const limitSelect = document.getElementById('limit-select');
const groupChunksCheckbox = document.getElementById('group-chunks-checkbox');

const chatInput = document.getElementById('chat-input');
const sendMessageButton = document.getElementById('send-message-button');
const chatMessages = document.getElementById('chat-messages');
const chatCollectionSelect = document.getElementById('chat-collection-select');
const chatDbTypeSelect = document.getElementById('chat-db-type-select');
const clearChatButton = document.getElementById('clear-chat-button');

const searchTab = document.getElementById('search-tab');
const chatbotTab = document.getElementById('chatbot-tab');
const aboutTab = document.getElementById('about-tab');

const searchSection = document.getElementById('search-section');
const chatbotSection = document.getElementById('chatbot-section');
const aboutSection = document.getElementById('about-section');

// Chat history
let chatHistory = [];

// Initialize the application
function init() {
    // Load available collections
    loadCollections();
    
    // Load available database types
    loadDbTypes();
    
    // Add event listeners
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    sendMessageButton.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    
    clearChatButton.addEventListener('click', clearChat);
    
    // Tab navigation
    searchTab.addEventListener('click', (e) => {
        e.preventDefault();
        activateTab('search');
    });
    
    chatbotTab.addEventListener('click', (e) => {
        e.preventDefault();
        activateTab('chatbot');
    });
    
    aboutTab.addEventListener('click', (e) => {
        e.preventDefault();
        activateTab('about');
    });
    
    // Load preferences from local storage
    loadPreferences();
}

// Load available collections
function loadCollections() {
    fetch('/api/collections')
        .then(response => response.json())
        .then(data => {
            const collections = data.collections;
            
            // Clear existing options
            collectionSelect.innerHTML = '';
            chatCollectionSelect.innerHTML = '';
            
            // Add new options
            collections.forEach(collection => {
                const option = document.createElement('option');
                option.value = collection.id;
                option.textContent = `${collection.name} (${collection.count})`;
                collectionSelect.appendChild(option);
                
                const chatOption = document.createElement('option');
                chatOption.value = collection.id;
                chatOption.textContent = `${collection.name} (${collection.count})`;
                chatCollectionSelect.appendChild(chatOption);
            });
        })
        .catch(error => {
            console.error('Error loading collections:', error);
        });
}

// Load available database types
function loadDbTypes() {
    fetch('/api/db-types')
        .then(response => response.json())
        .then(data => {
            const dbTypes = data.db_types;
            
            // Clear existing options
            dbTypeSelect.innerHTML = '';
            chatDbTypeSelect.innerHTML = '';
            
            // Add new options
            dbTypes.forEach(dbType => {
                const option = document.createElement('option');
                option.value = dbType.id;
                option.textContent = dbType.name;
                dbTypeSelect.appendChild(option);
                
                const chatOption = document.createElement('option');
                chatOption.value = dbType.id;
                chatOption.textContent = dbType.name;
                chatDbTypeSelect.appendChild(chatOption);
            });
        })
        .catch(error => {
            console.error('Error loading database types:', error);
        });
}

// Perform search
function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        return;
    }
    
    // Show loading indicator
    searchResults.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
        </div>
    `;
    
    // Get search parameters
    const collection = collectionSelect.value;
    const dbType = dbTypeSelect.value;
    const limit = limitSelect.value;
    const groupChunks = groupChunksCheckbox.checked;
    
    // Save preferences to local storage
    savePreferences();
    
    // Perform search
    fetch(`/api/search?query=${encodeURIComponent(query)}&collection=${collection}&db_type=${dbType}&limit=${limit}&group_chunks=${groupChunks}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error performing search:', error);
            searchResults.innerHTML = `
                <div class="error">
                    <p>Error performing search. Please try again.</p>
                </div>
            `;
        });
}

// Display search results
function displaySearchResults(data) {
    const results = data.results;
    
    if (!results || results.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <p>No results found for "${data.query}".</p>
            </div>
        `;
        return;
    }
    
    // Build results HTML
    let resultsHtml = `<h2>Results for "${data.query}"</h2>`;
    
    results.forEach((result, index) => {
        const title = result.title || 'Untitled';
        const id = result.id || '';
        const similarity = (result.similarity * 100).toFixed(2);
        const content = result.content || '';
        
        // Convert content from markdown to HTML
        const contentHtml = marked.parse(content);
        
        resultsHtml += `
            <div class="result-item">
                <h3 class="result-title">${title}</h3>
                <div class="result-meta">
                    <span>ID: ${id}</span>
                    <span>Similarity: ${similarity}%</span>
                </div>
                <div class="result-content">${contentHtml}</div>
            </div>
        `;
    });
    
    searchResults.innerHTML = resultsHtml;
    
    // Apply syntax highlighting to code blocks
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Send chat message
function sendChatMessage() {
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Get chat parameters
    const collection = chatCollectionSelect.value;
    const dbType = chatDbTypeSelect.value;
    
    // Add message to history
    chatHistory.push({
        role: 'user',
        content: message
    });
    
    // Show loading indicator
    addChatMessage('system', 'Thinking...', 'loading-message');
    
    // Send message to chatbot
    fetch('/chatbot/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            collection: collection,
            db_type: dbType,
            history: chatHistory.slice(0, -1) // Exclude the message we just added
        })
    })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            document.querySelector('.loading-message').remove();
            
            // Add assistant message to chat
            addChatMessage('assistant', data.reply, null, data.sources);
            
            // Add message to history
            chatHistory.push({
                role: 'assistant',
                content: data.reply
            });
        })
        .catch(error => {
            console.error('Error sending chat message:', error);
            
            // Remove loading message
            document.querySelector('.loading-message').remove();
            
            // Add error message to chat
            addChatMessage('system', 'Error: Failed to get a response. Please try again.');
        });
}

// Add chat message
function addChatMessage(role, content, className = null, sources = null) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    if (className) {
        messageElement.classList.add(className);
    }
    
    // Convert content from markdown to HTML if it's from the assistant
    const contentHtml = role === 'assistant' ? marked.parse(content) : content;
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                Sources: ${sources.map(source => `<a href="#" title="${source.title}">${source.id}</a>`).join(', ')}
            </div>
        `;
    }
    
    messageElement.innerHTML = `
        <div class="message-content">
            ${contentHtml}
            ${sourcesHtml}
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Apply syntax highlighting to code blocks
    messageElement.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Clear chat
function clearChat() {
    // Clear chat history
    chatHistory = [];
    
    // Clear chat messages
    chatMessages.innerHTML = `
        <div class="message system">
            <div class="message-content">
                <p>Hello! I'm DocuCrawler Assistant. Ask me anything about the documentation.</p>
            </div>
        </div>
    `;
}

// Activate tab
function activateTab(tab) {
    // Update tab links
    searchTab.classList.remove('active');
    chatbotTab.classList.remove('active');
    aboutTab.classList.remove('active');
    
    // Update tab sections
    searchSection.classList.remove('active');
    chatbotSection.classList.remove('active');
    aboutSection.classList.remove('active');
    
    // Activate selected tab
    if (tab === 'search') {
        searchTab.classList.add('active');
        searchSection.classList.add('active');
    } else if (tab === 'chatbot') {
        chatbotTab.classList.add('active');
        chatbotSection.classList.add('active');
    } else if (tab === 'about') {
        aboutTab.classList.add('active');
        aboutSection.classList.add('active');
    }
}

// Save preferences to local storage
function savePreferences() {
    const preferences = {
        collection: collectionSelect.value,
        dbType: dbTypeSelect.value,
        limit: limitSelect.value,
        groupChunks: groupChunksCheckbox.checked,
        chatCollection: chatCollectionSelect.value,
        chatDbType: chatDbTypeSelect.value
    };
    
    localStorage.setItem('docucrawler_preferences', JSON.stringify(preferences));
}

// Load preferences from local storage
function loadPreferences() {
    const preferences = JSON.parse(localStorage.getItem('docucrawler_preferences'));
    
    if (preferences) {
        if (preferences.collection) {
            collectionSelect.value = preferences.collection;
        }
        
        if (preferences.dbType) {
            dbTypeSelect.value = preferences.dbType;
        }
        
        if (preferences.limit) {
            limitSelect.value = preferences.limit;
        }
        
        if (preferences.groupChunks !== undefined) {
            groupChunksCheckbox.checked = preferences.groupChunks;
        }
        
        if (preferences.chatCollection) {
            chatCollectionSelect.value = preferences.chatCollection;
        }
        
        if (preferences.chatDbType) {
            chatDbTypeSelect.value = preferences.chatDbType;
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);