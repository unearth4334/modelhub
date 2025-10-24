// Dashboard JavaScript

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
    setupTextGenerationForm();
    setupImageAnalysisForm();
    
    // Auto-refresh status every 30 seconds
    setInterval(checkSystemStatus, 30000);
});

// Check system status
async function checkSystemStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        // Update API status
        updateStatusCard('api-status', data.status === 'healthy' ? 'Healthy' : 'Degraded', 
                         data.status === 'healthy');
        
        // Update Ollama status
        updateStatusCard('ollama-status', data.ollama_available ? 'Available' : 'Offline', 
                         data.ollama_available);
        
        // Update Image Model status
        updateStatusCard('image-model-status', data.image_model_loaded ? 'Loaded' : 'Not Loaded', 
                         data.image_model_loaded);
        
    } catch (error) {
        console.error('Error checking status:', error);
        updateStatusCard('api-status', 'Error', false);
        updateStatusCard('ollama-status', 'Unknown', false);
        updateStatusCard('image-model-status', 'Unknown', false);
    }
}

// Update status card
function updateStatusCard(cardId, statusText, isHealthy) {
    const statusValue = document.getElementById(cardId + '-value');
    if (statusValue) {
        statusValue.textContent = statusText;
        statusValue.className = 'status-value';
        
        if (isHealthy) {
            statusValue.classList.add('healthy');
        } else if (statusText === 'Not Loaded' || statusText === 'Unknown') {
            statusValue.classList.add('degraded');
        } else {
            statusValue.classList.add('offline');
        }
    }
}

// Setup text generation form
function setupTextGenerationForm() {
    const form = document.getElementById('text-generation-form');
    const resultDiv = document.getElementById('text-result');
    const resultContent = document.getElementById('text-result-content');
    const resultMeta = document.getElementById('text-result-meta');
    const loadingDiv = document.getElementById('text-loading');
    const errorDiv = document.getElementById('text-error');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous results/errors
        resultDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        loadingDiv.style.display = 'block';
        
        // Get form data
        const formData = {
            prompt: document.getElementById('text-prompt').value,
            model: document.getElementById('text-model').value,
            max_tokens: parseInt(document.getElementById('max-tokens').value),
            temperature: parseFloat(document.getElementById('temperature').value)
        };
        
        try {
            const response = await fetch('/api/v1/generate/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            loadingDiv.style.display = 'none';
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate text');
            }
            
            const data = await response.json();
            
            // Display result
            resultContent.textContent = data.text;
            resultMeta.textContent = `Model: ${data.model}`;
            resultDiv.style.display = 'block';
            
        } catch (error) {
            loadingDiv.style.display = 'none';
            errorDiv.textContent = 'Error: ' + error.message;
            errorDiv.style.display = 'block';
        }
    });
}

// Setup image analysis form
function setupImageAnalysisForm() {
    const form = document.getElementById('image-analysis-form');
    const fileInput = document.getElementById('image-file');
    const previewDiv = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const resultDiv = document.getElementById('image-result');
    const resultContent = document.getElementById('image-result-content');
    const resultMeta = document.getElementById('image-result-meta');
    const loadingDiv = document.getElementById('image-loading');
    const errorDiv = document.getElementById('image-error');
    
    // Handle file selection for preview
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewDiv.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            previewDiv.style.display = 'none';
        }
    });
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous results/errors
        resultDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        loadingDiv.style.display = 'block';
        
        const formData = new FormData();
        const file = fileInput.files[0];
        
        if (!file) {
            loadingDiv.style.display = 'none';
            errorDiv.textContent = 'Please select an image file';
            errorDiv.style.display = 'block';
            return;
        }
        
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/v1/analyze/image', {
                method: 'POST',
                body: formData
            });
            
            loadingDiv.style.display = 'none';
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze image');
            }
            
            const data = await response.json();
            
            // Display results
            resultContent.innerHTML = '';
            data.predictions.forEach(pred => {
                const predItem = document.createElement('div');
                predItem.className = 'prediction-item';
                
                const label = document.createElement('div');
                label.className = 'prediction-label';
                label.textContent = pred.label;
                
                const scoreDiv = document.createElement('div');
                scoreDiv.className = 'prediction-score';
                
                const scoreBar = document.createElement('div');
                scoreBar.className = 'score-bar';
                const scoreFill = document.createElement('div');
                scoreFill.className = 'score-fill';
                scoreFill.style.width = (pred.score * 100) + '%';
                scoreBar.appendChild(scoreFill);
                
                const scoreText = document.createElement('div');
                scoreText.className = 'score-text';
                scoreText.textContent = (pred.score * 100).toFixed(2) + '%';
                
                scoreDiv.appendChild(scoreBar);
                scoreDiv.appendChild(scoreText);
                
                predItem.appendChild(label);
                predItem.appendChild(scoreDiv);
                resultContent.appendChild(predItem);
            });
            
            resultMeta.textContent = `Model: ${data.model}`;
            resultDiv.style.display = 'block';
            
        } catch (error) {
            loadingDiv.style.display = 'none';
            errorDiv.textContent = 'Error: ' + error.message;
            errorDiv.style.display = 'block';
        }
    });
}
