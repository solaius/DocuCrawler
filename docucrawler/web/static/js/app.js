// DocuCrawler Web Application

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchResults = document.getElementById('search-results');
const collectionSelect = document.getElementById('collection-select');
const dbTypeSelect = document.getElementById('db-type-select');
const limitSelect = document.getElementById('limit-select');
const groupChunksCheckbox = document.getElementById('group-chunks-checkbox');

// Advanced Filters Elements
const advancedFiltersToggle = document.getElementById('advanced-filters-toggle');
const advancedFiltersPanel = document.getElementById('advanced-filters-panel');
const applyFiltersButton = document.getElementById('apply-filters-button');
const resetFiltersButton = document.getElementById('reset-filters-button');
const searchTypeRadios = document.querySelectorAll('input[name="search-type"]');
const docTypeCheckboxes = document.querySelectorAll('input[name="doc-type"]');
const contentFeatureCheckboxes = document.querySelectorAll('input[name="content-feature"]');

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
    
    // Add event listeners for search
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Add event listeners for advanced filters
    advancedFiltersToggle.addEventListener('click', toggleAdvancedFilters);
    applyFiltersButton.addEventListener('click', performSearch);
    resetFiltersButton.addEventListener('click', resetFilters);
    
    // Add event listeners for chat
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

// Toggle advanced filters panel
function toggleAdvancedFilters() {
    if (advancedFiltersPanel.style.display === 'block') {
        advancedFiltersPanel.style.display = 'none';
        advancedFiltersToggle.innerHTML = '<i class="fas fa-filter"></i> Advanced Filters';
    } else {
        advancedFiltersPanel.style.display = 'block';
        advancedFiltersToggle.innerHTML = '<i class="fas fa-filter"></i> Hide Filters';
    }
}

// Reset filters to default values
function resetFilters() {
    // Reset search type
    document.getElementById('search-type-semantic').checked = true;
    
    // Reset document types
    docTypeCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Reset content features
    contentFeatureCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
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
    
    // Get basic search parameters
    const collection = collectionSelect.value;
    const dbType = dbTypeSelect.value;
    const limit = limitSelect.value;
    const groupChunks = groupChunksCheckbox.checked;
    
    // Get advanced filter parameters
    const filters = getAdvancedFilters();
    
    // Save preferences to local storage
    savePreferences();
    
    // Prepare search URL
    let searchUrl = `/api/search?query=${encodeURIComponent(query)}&collection=${collection}&db_type=${dbType}&limit=${limit}&group_chunks=${groupChunks}`;
    
    // Add search type parameter
    if (filters.searchType) {
        searchUrl += `&search_type=${filters.searchType}`;
    }
    
    // Perform search
    fetch(searchUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            collection: collection,
            db_type: dbType,
            limit: parseInt(limit),
            group_chunks: groupChunks,
            filters: filters
        })
    })
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

// Get advanced filters
function getAdvancedFilters() {
    const filters = {};
    
    // Get search type
    for (const radio of searchTypeRadios) {
        if (radio.checked) {
            filters.searchType = radio.value;
            break;
        }
    }
    
    // Get document types
    const docTypes = [];
    for (const checkbox of docTypeCheckboxes) {
        if (checkbox.checked) {
            docTypes.push(checkbox.value);
        }
    }
    if (docTypes.length > 0) {
        filters.docTypes = docTypes;
    }
    
    // Get content features
    const contentFeatures = [];
    for (const checkbox of contentFeatureCheckboxes) {
        if (checkbox.checked) {
            contentFeatures.push(checkbox.value);
        }
    }
    if (contentFeatures.length > 0) {
        filters.contentFeatures = contentFeatures;
    }
    
    return filters;
}

// Display search results
function displaySearchResults(data) {
    const results = data.results;
    const query = data.query;
    const searchType = data.search_type || 'semantic';
    
    if (!results || results.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <p>No results found for "${query}".</p>
            </div>
        `;
        return;
    }
    
    // Build results HTML
    let resultsHtml = `
        <div class="results-header">
            <h2>Results for "${query}"</h2>
            <div class="results-meta">
                <span>Search type: <strong>${searchType}</strong></span>
                <span>Found: <strong>${results.length}</strong> results</span>
            </div>
        </div>
    `;
    
    results.forEach((result, index) => {
        const title = result.title || 'Untitled';
        const id = result.id || '';
        const similarity = (result.similarity * 100).toFixed(2);
        let content = result.content || '';
        
        // Highlight search terms in content
        const queryTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
        
        // Convert content from markdown to HTML
        let contentHtml = marked.parse(content);
        
        // Highlight search terms in the HTML content
        if (queryTerms.length > 0) {
            // Create a temporary div to manipulate the HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = contentHtml;
            
            // Function to highlight text in a text node
            function highlightTextNode(textNode, term) {
                const text = textNode.nodeValue;
                const lowerText = text.toLowerCase();
                let lastIndex = 0;
                let result = document.createDocumentFragment();
                let match;
                
                // Find all occurrences of the term
                let startIndex = lowerText.indexOf(term, lastIndex);
                while (startIndex !== -1) {
                    // Add text before the match
                    if (startIndex > lastIndex) {
                        result.appendChild(document.createTextNode(text.substring(lastIndex, startIndex)));
                    }
                    
                    // Add the highlighted match
                    const span = document.createElement('span');
                    span.className = 'highlight';
                    span.textContent = text.substring(startIndex, startIndex + term.length);
                    result.appendChild(span);
                    
                    // Update lastIndex
                    lastIndex = startIndex + term.length;
                    
                    // Find the next occurrence
                    startIndex = lowerText.indexOf(term, lastIndex);
                }
                
                // Add any remaining text
                if (lastIndex < text.length) {
                    result.appendChild(document.createTextNode(text.substring(lastIndex)));
                }
                
                return result;
            }
            
            // Function to recursively process nodes
            function processNode(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    let highlighted = node;
                    
                    // Apply highlighting for each term
                    for (const term of queryTerms) {
                        if (node.nodeValue.toLowerCase().includes(term)) {
                            highlighted = highlightTextNode(node, term);
                            break;
                        }
                    }
                    
                    if (highlighted !== node) {
                        node.parentNode.replaceChild(highlighted, node);
                    }
                } else if (node.nodeType === Node.ELEMENT_NODE && 
                          !['script', 'style', 'pre', 'code'].includes(node.nodeName.toLowerCase())) {
                    // Process child nodes
                    Array.from(node.childNodes).forEach(processNode);
                }
            }
            
            // Process all nodes in the content
            Array.from(tempDiv.childNodes).forEach(processNode);
            
            // Get the highlighted HTML
            contentHtml = tempDiv.innerHTML;
        }
        
        // Add chunk information if available
        let chunksHtml = '';
        if (result.chunks && result.chunks.length > 0) {
            chunksHtml = `
                <div class="result-chunks">
                    <div class="chunks-header">
                        <span>Contains ${result.chunks.length} chunks</span>
                        <button class="toggle-chunks secondary-button">Show Chunks</button>
                    </div>
                    <div class="chunks-content" style="display: none;">
                        ${result.chunks.map((chunk, i) => `
                            <div class="chunk-item">
                                <div class="chunk-header">
                                    <span>Chunk ${i+1}</span>
                                    <span>Similarity: ${(chunk.similarity * 100).toFixed(2)}%</span>
                                </div>
                                <div class="chunk-content">${chunk.content}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        resultsHtml += `
            <div class="result-item">
                <h3 class="result-title">${title}</h3>
                <div class="result-meta">
                    <span>ID: ${id}</span>
                    <span>Similarity: ${similarity}%</span>
                    ${result.search_type ? `<span>Match type: ${result.search_type}</span>` : ''}
                </div>
                <div class="result-content">${contentHtml}</div>
                ${chunksHtml}
            </div>
        `;
    });
    
    searchResults.innerHTML = resultsHtml;
    
    // Add event listeners to toggle chunks
    document.querySelectorAll('.toggle-chunks').forEach(button => {
        button.addEventListener('click', function() {
            const chunksContent = this.parentNode.nextElementSibling;
            if (chunksContent.style.display === 'none') {
                chunksContent.style.display = 'block';
                this.textContent = 'Hide Chunks';
            } else {
                chunksContent.style.display = 'none';
                this.textContent = 'Show Chunks';
            }
        });
    });
    
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