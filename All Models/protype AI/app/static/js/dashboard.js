
/**
 * Dashboard JavaScript for Protype.AI
 * Handles dashboard functionality, stats and visualizations
 */

// Setup dashboard functionality
function setupDashboard() {
    // Initialize dashboard data
    loadDashboardStats();
    
    // Setup analyze button
    document.getElementById('analyze-ai-btn').addEventListener('click', analyzeAI);
    
    // Setup report generation
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);
    
    // Refresh dashboard every 30 seconds
    setInterval(loadDashboardStats, 30000);
}

// Load dashboard statistics
function loadDashboardStats() {
    fetch('/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateKnowledgeStats(data);
                updateActivityLog(data.activities);
            } else {
                console.error('Error loading dashboard stats:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Update knowledge stats display
function updateKnowledgeStats(data) {
    const statsContainer = document.getElementById('kb-stats');
    
    const statsHtml = `
        <div class="stat-item">
            <span class="stat-label">Questions:</span>
            <span class="stat-value">${data.question_count}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Knowledge Graph Nodes:</span>
            <span class="stat-value">${data.node_count}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Knowledge Graph Connections:</span>
            <span class="stat-value">${data.edge_count}</span>
        </div>
    `;
    
    statsContainer.innerHTML = statsHtml;
}

// Update activity log display
function updateActivityLog(activities) {
    const activityContainer = document.getElementById('learning-activity');
    
    if (!activities || activities.length === 0) {
        activityContainer.innerHTML = '<p>No recent activities.</p>';
        return;
    }
    
    let activityHtml = '';
    
    activities.forEach(activity => {
        activityHtml += `
            <div class="activity-item">
                <div class="activity-time">${activity.timestamp}</div>
                <div class="activity-description">
                    <strong>${activity.user}</strong> - ${activity.action}: ${activity.description}
                </div>
            </div>
        `;
    });
    
    activityContainer.innerHTML = activityHtml;
}

// Analyze AI
function analyzeAI() {
    const analysisContainer = document.getElementById('ai-analysis-results');
    
    // Show loading
    analysisContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Analyzing...</div>';
    
    fetch('/analyze-ai')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const kbAnalysis = data.kb_analysis;
                const learningStats = data.learning_stats;
                
                let analysisHtml = '<div class="analysis-section mb-4">';
                analysisHtml += '<h5>Knowledge Base Analysis</h5>';
                
                if (kbAnalysis.status === 'success') {
                    // Question stats
                    analysisHtml += `
                        <div class="card mb-3">
                            <div class="card-body">
                                <h6 class="card-title">Question Statistics</h6>
                                <p>Total Questions: ${kbAnalysis.question_count}</p>
                                <p>Average Answer Length: ${Math.round(kbAnalysis.answer_length_avg)} characters</p>
                                <div class="mb-2">Question Types:</div>
                                <ul>
                    `;
                    
                    for (const [type, count] of Object.entries(kbAnalysis.question_types || {})) {
                        analysisHtml += `<li>${type}: ${count}</li>`;
                    }
                    
                    analysisHtml += `
                                </ul>
                            </div>
                        </div>
                    `;
                    
                    // Entity Analysis
                    analysisHtml += `
                        <div class="card mb-3">
                            <div class="card-body">
                                <h6 class="card-title">Entity Analysis</h6>
                                <div class="mb-2">Common Entity Types:</div>
                                <ul>
                    `;
                    
                    for (const [entity, count] of Object.entries(kbAnalysis.entities || {})) {
                        analysisHtml += `<li>${entity}: ${count}</li>`;
                    }
                    
                    analysisHtml += `
                                </ul>
                                <div class="mb-2">Example Entities:</div>
                                <p>${(kbAnalysis.entity_examples || []).join(', ')}</p>
                            </div>
                        </div>
                    `;
                } else {
                    analysisHtml += `
                        <div class="alert alert-warning">
                            ${kbAnalysis.message || 'Limited analysis available'}
                        </div>
                    `;
                }
                
                analysisHtml += '</div>';
                
                // Learning Stats
                analysisHtml += '<div class="analysis-section mb-4">';
                analysisHtml += '<h5>Learning Statistics</h5>';
                
                analysisHtml += `
                    <div class="card mb-3">
                        <div class="card-body">
                            <h6 class="card-title">Learning Activity</h6>
                            <p>Total Learning Actions: ${learningStats.total_logs}</p>
                            <div class="mb-2">Sources:</div>
                            <ul>
                `;
                
                for (const [source, count] of Object.entries(learningStats.sources || {})) {
                    analysisHtml += `<li>${source}: ${count}</li>`;
                }
                
                analysisHtml += `
                            </ul>
                            <div class="mb-2">Actions:</div>
                            <ul>
                `;
                
                for (const [action, count] of Object.entries(learningStats.actions || {})) {
                    analysisHtml += `<li>${action}: ${count}</li>`;
                }
                
                analysisHtml += `
                            </ul>
                        </div>
                    </div>
                `;
                
                // Recent Logs
                analysisHtml += `
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Recent Learning Logs</h6>
                            <div style="max-height: 200px; overflow-y: auto;">
                `;
                
                if (learningStats.recent_logs && learningStats.recent_logs.length > 0) {
                    learningStats.recent_logs.forEach(log => {
                        const timestamp = log.timestamp.split('T')[0] + ' ' + log.timestamp.split('T')[1].substring(0, 8);
                        analysisHtml += `
                            <div class="mb-2">
                                <strong>${timestamp}</strong> - ${log.source}: ${log.action} - ${log.description}
                            </div>
                        `;
                    });
                } else {
                    analysisHtml += '<p>No recent logs available.</p>';
                }
                
                analysisHtml += `
                            </div>
                        </div>
                    </div>
                `;
                
                analysisHtml += '</div>';
                
                analysisContainer.innerHTML = analysisHtml;
            } else {
                analysisContainer.innerHTML = `<div class="alert alert-danger">${data.message || 'Error analyzing AI'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            analysisContainer.innerHTML = '<div class="alert alert-danger">Error analyzing AI. Please try again.</div>';
        });
}

// Generate knowledge report
function generateReport() {
    const reportContainer = document.getElementById('report-results');
    
    // Show loading
    reportContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Generating report...</div>';
    
    fetch('/generate-report', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                reportContainer.innerHTML = `
                    <div class="alert alert-success">
                        Report generated successfully!
                    </div>
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Available Reports</h6>
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    Knowledge Base Report
                                    <a href="/reports/knowledge_report.txt" class="btn btn-sm btn-primary" target="_blank">
                                        <i class="fas fa-download"></i> Download
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                `;
            } else {
                reportContainer.innerHTML = `<div class="alert alert-danger">${data.message || 'Error generating report'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            reportContainer.innerHTML = '<div class="alert alert-danger">Error generating report. Please try again.</div>';
        });
}
