let currentStream = null;

function clearResults() {
    document.getElementById('results').innerHTML = '';
}

function showLoading() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="loading">
            <h3>🚀 Starting search...</h3>
            <p>Please wait while we process your query...</p>
        </div>
    `;
}

function showError(error) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="error">
            <h3>❌ Error</h3>
            <p>${error}</p>
        </div>
    `;
}

function performStreamSearch() {
    const query = document.getElementById('query').value;
    const maxAttempts = document.getElementById('maxAttempts').value;

    if (!query.trim()) {
        alert('Please enter a search query');
        return;
    }

    // Cancel any existing stream
    if (currentStream) {
        currentStream.close();
    }

    showLoading();

    try {
        // Initialize streaming display
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <div class="result-section">
                <h3>🔍 Execution Log (Live)</h3>
                <div id="streamingUpdates" class="execution-log"></div>
            </div>
        `;

        const streamingDiv = document.getElementById('streamingUpdates');

        // Create EventSource URL with query parameters
        const params = new URLSearchParams({
            query: query,
            max_attempts: maxAttempts
        });
        const eventSourceUrl = `/search?${params.toString()}`;

        // Create EventSource for SSE
        const eventSource = new EventSource(eventSourceUrl);
        currentStream = eventSource;

        eventSource.onmessage = function (event) {
            const eventData = JSON.parse(event.data);
            displayStreamEvent(eventData, streamingDiv);
        };

        eventSource.onerror = function (error) {
            console.error('EventSource failed:', error);
            eventSource.close();
            currentStream = null;

            if (streamingDiv.children.length === 0) {
                showError('Connection failed. Please try again.');
            }
        };
    } catch (error) {
        showError(error.message);
        currentStream = null;
    }
}
let lastLogCount = 0; // Track displayed logs to show only new ones

function displayStreamEvent(eventData, streamingDiv) {
    if (eventData.event_type === 'started') {
        streamingDiv.innerHTML += `<div>🚀 Starting search for: ${eventData.data.query}</div><div></div>`;
        lastLogCount = 0; // Reset counter
    } else if (eventData.event_type === 'node_completed') {
        const data = eventData.data;

        // Display only new execution logs since last update
        if (data.execution_log && data.execution_log.length > lastLogCount) {
            const newLogs = data.execution_log.slice(lastLogCount);
            newLogs.forEach(log => {
                streamingDiv.innerHTML += `<div>${log}</div>`;
            });
            lastLogCount = data.execution_log.length;
        }

        // Show plan steps only once when generate_plan completes
        if (data.plan && data.plan.length > 0 && eventData.node_name === 'generate_plan') {
            data.plan.forEach((step, index) => {
                streamingDiv.innerHTML += `<div>   Step ${index + 1}: ${step}</div>`;
            });
            streamingDiv.innerHTML += `<div></div>`; // Add space after plan
        }

    } else if (eventData.event_type === 'completed') {
        // Just add a completion message, we'll show final results separately
        streamingDiv.innerHTML += `<div><strong>🎉 Search completed successfully!</strong></div>`;
        displayFinalResults(eventData.data, streamingDiv);

        // Close EventSource when completed
        if (currentStream) {
            currentStream.close();
            currentStream = null;
        }
    } else if (eventData.event_type === 'error') {
        streamingDiv.innerHTML += `<div style="color: #c62828;">❌ Error: ${eventData.data.error}</div>`;

        // Close EventSource on error
        if (currentStream) {
            currentStream.close();
            currentStream = null;
        }
    }

    // Auto-scroll to bottom
    streamingDiv.scrollTop = streamingDiv.scrollHeight;
}

function displayFinalResults(result, streamingDiv) {
    const resultsDiv = document.getElementById('results');

    // Add final answer section after the execution log
    const finalResultsHtml = `
        <div class="result-section">
            <h3>📝 Final Answer</h3>
            <div class="final-answer">${result.final_answer}</div>
        </div>
    `;

    resultsDiv.innerHTML += finalResultsHtml;
}

// Allow Enter key to trigger search
document.getElementById('query').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        performStreamSearch();
    }
});