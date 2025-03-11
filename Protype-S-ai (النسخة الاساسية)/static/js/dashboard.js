
/**
 * dashboard.js - ملف جافاسكريبت للوحة تحكم Protype.AI المتقدمة
 */

document.addEventListener('DOMContentLoaded', function() {
    // ----- تهيئة الصفحة -----
    initDashboard();
    
    // ----- مستمعو الأحداث -----
    setupEventListeners();
});

// ----- الوظائف الرئيسية -----

/**
 * تهيئة لوحة التحكم
 */
function initDashboard() {
    // تحميل الإحصائيات
    loadDashboardStats();
    
    // تحميل سجلات النشاط والتعلم
    loadRecentActivities();
    loadLearningLogs();
    
    // التحديث التلقائي كل 30 ثانية
    setInterval(function() {
        if (document.getElementById('auto-refresh-log').checked) {
            refreshAgentData();
        }
    }, 30000);
    
    setInterval(loadDashboardStats, 60000);
}

/**
 * إعداد مستمعي الأحداث
 */
function setupEventListeners() {
    // ----- نظرة عامة -----
    document.getElementById('start-learning-btn').addEventListener('click', startLearning);
    document.getElementById('stop-learning-btn').addEventListener('click', stopLearning);
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);
    document.getElementById('analyze-ai-btn').addEventListener('click', analyzeAI);
    
    // ----- التفكير النقدي -----
    document.getElementById('evaluate-inference-btn').addEventListener('click', evaluateInference);
    document.getElementById('generate-questions-btn').addEventListener('click', generateCriticalQuestions);
    
    // ----- الذاكرة المتقدمة -----
    document.getElementById('search-memory-btn').addEventListener('click', searchMemory);
    document.getElementById('add-memory-btn').addEventListener('click', addMemory);
    document.getElementById('cleanup-memory-btn').addEventListener('click', cleanupMemory);
    
    // ----- الذكاء متعدد الوسائط -----
    // تحميل الصورة
    const imageUploadArea = document.getElementById('image-upload-area');
    const imageUpload = document.getElementById('image-upload');
    
    imageUploadArea.addEventListener('click', () => {
        imageUpload.click();
    });
    
    imageUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        imageUploadArea.classList.add('border-primary');
    });
    
    imageUploadArea.addEventListener('dragleave', () => {
        imageUploadArea.classList.remove('border-primary');
    });
    
    imageUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        imageUploadArea.classList.remove('border-primary');
        
        if (e.dataTransfer.files.length) {
            imageUpload.files = e.dataTransfer.files;
            handleImageUpload(e.dataTransfer.files[0]);
        }
    });
    
    imageUpload.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleImageUpload(e.target.files[0]);
        }
    });
    
    document.getElementById('analyze-image-btn').addEventListener('click', analyzeImage);
    document.getElementById('generate-speech-btn').addEventListener('click', generateSpeech);
    
    // تحميل الأصوات المتاحة
    loadAvailableVoices();
    
    // ----- الوكيل المستقل -----
    document.getElementById('add-objective-btn').addEventListener('click', addObjective);
    document.getElementById('generate-objectives-btn').addEventListener('click', generateObjectives);
    document.getElementById('start-agent-btn').addEventListener('click', startAgent);
    document.getElementById('pause-agent-btn').addEventListener('click', pauseAgent);
    document.getElementById('export-knowledge-btn').addEventListener('click', exportKnowledge);
    
    // ----- شبكة المعرفة -----
    document.getElementById('query-network-btn').addEventListener('click', queryKnowledgeNetwork);
    document.getElementById('display-mode').addEventListener('change', updateNetworkVisualization);
    document.getElementById('node-size').addEventListener('input', function() {
        document.getElementById('node-size-value').textContent = this.value;
        updateNetworkVisualization();
    });
    document.getElementById('show-labels').addEventListener('change', updateNetworkVisualization);
    document.getElementById('show-inferred').addEventListener('change', updateNetworkVisualization);
    
    // ----- علامات التبويب -----
    document.querySelectorAll('#featureTabs .nav-link').forEach(tab => {
        tab.addEventListener('click', function() {
            if (this.id === 'agent-tab') {
                loadAgentData();
            } else if (this.id === 'self-reflection-tab') {
                loadReflectionHistory();
            }
        });
    });
}

// ----- وظائف تحميل البيانات -----

/**
 * تحميل إحصائيات لوحة التحكم
 */
function loadDashboardStats() {
    fetch('/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDashboardStats(data.stats);
                createActivityChart(data.charts.activity);
                createSourcesChart(data.charts.sources);
            } else {
                console.error('Error loading dashboard stats:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

/**
 * تحديث إحصائيات لوحة التحكم
 */
function updateDashboardStats(stats) {
    document.getElementById('question-count').textContent = stats.question_count || 0;
    document.getElementById('node-count').textContent = stats.node_count || 0;
    document.getElementById('edge-count').textContent = stats.edge_count || 0;
    document.getElementById('memory-count').textContent = stats.memory_entries || 0;
    
    // تحديث إحصائيات الذاكرة
    document.getElementById('memory-entries').textContent = stats.memory_entries || 0;
    document.getElementById('memory-dimension').textContent = stats.memory_dimension || 384;
}

/**
 * تحميل النشاطات الأخيرة
 */
function loadRecentActivities() {
    const activitiesContainer = document.getElementById('recent-activities');
    
    fetch('/get-recent-activities')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.activities.length > 0) {
                let activitiesHtml = '';
                
                data.activities.forEach(activity => {
                    activitiesHtml += `
                        <div class="log-item mb-2 p-2 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="timestamp text-muted"><i class="bi bi-clock me-1"></i>${activity.timestamp}</span>
                                <span class="user badge bg-secondary"><i class="bi bi-person me-1"></i>${activity.user}</span>
                            </div>
                            <div class="mt-1">
                                <span class="badge bg-info me-2"><i class="bi bi-activity me-1"></i>${activity.action}</span>
                                ${activity.description}
                            </div>
                        </div>
                    `;
                });
                
                activitiesContainer.innerHTML = activitiesHtml;
            } else {
                activitiesContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد نشاطات متاحة حتى الآن.</p>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            activitiesContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل النشاطات.</p>';
        });
}

/**
 * تحميل سجلات التعلم
 */
function loadLearningLogs() {
    const logsContainer = document.getElementById('learning-logs');
    
    fetch('/learning-logs')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.logs.length > 0) {
                let logsHtml = '';
                
                data.logs.forEach(log => {
                    const timestamp = log.timestamp.split('T')[0] + ' ' + log.timestamp.split('T')[1].substring(0, 8);
                    
                    // إضافة التنسيق المناسب بناءً على نوع الإجراء
                    let actionClass = 'badge bg-primary';
                    if (log.action.includes('error')) {
                        actionClass = 'badge bg-danger';
                    } else if (log.action.includes('started')) {
                        actionClass = 'badge bg-success';
                    } else if (log.action.includes('stopped')) {
                        actionClass = 'badge bg-warning text-dark';
                    }
                    
                    logsHtml += `
                        <div class="log-item mb-2 p-2 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="timestamp text-muted"><i class="bi bi-clock me-1"></i>${timestamp}</span>
                                <span class="source badge bg-info"><i class="bi bi-box me-1"></i>${log.source}</span>
                            </div>
                            <div class="mt-1">
                                <span class="${actionClass} me-2"><i class="bi bi-activity me-1"></i>${log.action}</span>
                                ${log.description}
                            </div>
                        </div>
                    `;
                });
                
                logsContainer.innerHTML = logsHtml;
            } else {
                logsContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد سجلات تعلم متاحة حتى الآن.</p>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            logsContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل سجلات التعلم.</p>';
        });
}

// ----- وظائف نظرة عامة -----

/**
 * إنشاء مخطط النشاط
 */
function createActivityChart(chartData) {
    const ctx = document.getElementById('activity-chart').getContext('2d');
    
    // إذا كان لدينا مخطط سابق، قم بتدميره
    if (window.activityChart) {
        window.activityChart.destroy();
    }
    
    // إذا كان لدينا بيانات مخطط جاهزة (صورة base64)
    if (chartData) {
        const img = new Image();
        img.src = chartData;
        img.onload = function() {
            ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);
        };
        return;
    }
    
    // إذا لم تكن هناك بيانات، قم بإنشاء مخطط بسيط
    const labels = ['1', '2', '3', '4', '5', '6', '7'];
    const data = {
        labels: labels,
        datasets: [{
            label: 'نشاطات المستخدم',
            data: [12, 19, 3, 5, 2, 3, 15],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }, {
            label: 'عمليات التعلم',
            data: [7, 11, 5, 8, 3, 7, 10],
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
        }]
    };
    
    window.activityChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * إنشاء مخطط المصادر
 */
function createSourcesChart(chartData) {
    const ctx = document.getElementById('sources-chart').getContext('2d');
    
    // إذا كان لدينا مخطط سابق، قم بتدميره
    if (window.sourcesChart) {
        window.sourcesChart.destroy();
    }
    
    // إذا كان لدينا بيانات مخطط جاهزة (صورة base64)
    if (chartData) {
        const img = new Image();
        img.src = chartData;
        img.onload = function() {
            ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);
        };
        return;
    }
    
    // إذا لم تكن هناك بيانات، قم بإنشاء مخطط بسيط
    const data = {
        labels: ['Gemini', 'المستخدم', 'SerpAPI', 'التعلم'],
        datasets: [{
            label: 'مصادر المعرفة',
            data: [40, 20, 30, 10],
            backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(75, 192, 192, 0.6)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    window.sourcesChart = new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

/**
 * بدء التعلم المستمر
 */
function startLearning() {
    const actionResult = document.getElementById('action-result');
    actionResult.innerHTML = '<div class="alert alert-info">جاري بدء التعلم المستمر...</div>';
    
    fetch('/start-learning', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            actionResult.innerHTML = '<div class="alert alert-success">تم بدء التعلم المستمر بنجاح!</div>';
            setTimeout(() => {
                loadLearningLogs();
            }, 1000);
        } else {
            actionResult.innerHTML = `<div class="alert alert-danger">فشل بدء التعلم: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        actionResult.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة بدء التعلم المستمر</div>';
    });
}

/**
 * إيقاف التعلم المستمر
 */
function stopLearning() {
    const actionResult = document.getElementById('action-result');
    actionResult.innerHTML = '<div class="alert alert-info">جاري إيقاف التعلم المستمر...</div>';
    
    fetch('/stop-learning', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            actionResult.innerHTML = '<div class="alert alert-success">تم إيقاف التعلم المستمر بنجاح!</div>';
            setTimeout(() => {
                loadLearningLogs();
            }, 1000);
        } else {
            actionResult.innerHTML = `<div class="alert alert-danger">فشل إيقاف التعلم: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        actionResult.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة إيقاف التعلم المستمر</div>';
    });
}

/**
 * إنشاء تقرير عن قاعدة المعرفة
 */
function generateReport() {
    const actionResult = document.getElementById('action-result');
    actionResult.innerHTML = '<div class="alert alert-info">جاري إنشاء تقرير قاعدة المعرفة...</div>';
    
    fetch('/generate-report', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            actionResult.innerHTML = `
                <div class="alert alert-success">
                    تم إنشاء تقرير قاعدة المعرفة بنجاح!
                    <a href="/download-report" class="btn btn-sm btn-primary mt-2">تنزيل التقرير</a>
                </div>
            `;
        } else {
            actionResult.innerHTML = `<div class="alert alert-danger">فشل إنشاء التقرير: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        actionResult.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة إنشاء التقرير</div>';
    });
}

/**
 * تحليل الذكاء الاصطناعي
 */
function analyzeAI() {
    const actionResult = document.getElementById('action-result');
    actionResult.innerHTML = '<div class="alert alert-info">جاري تحليل نظام الذكاء الاصطناعي...</div>';
    
    fetch('/analyze-ai')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            actionResult.innerHTML = `
                <div class="alert alert-success">
                    تم تحليل النظام بنجاح!
                    <button class="btn btn-sm btn-primary mt-2" data-bs-toggle="modal" data-bs-target="#analysisModal">عرض التحليل</button>
                </div>
            `;
            // إنشاء نافذة منبثقة لعرض التحليل
            createAnalysisModal(data.analysis);
        } else {
            actionResult.innerHTML = `<div class="alert alert-danger">فشل تحليل النظام: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        actionResult.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة تحليل النظام</div>';
    });
}

/**
 * إنشاء نافذة منبثقة لعرض التحليل
 */
function createAnalysisModal(analysis) {
    // التحقق مما إذا كانت النافذة المنبثقة موجودة بالفعل
    let modal = document.getElementById('analysisModal');
    if (modal) {
        document.body.removeChild(modal);
    }
    
    // إنشاء النافذة المنبثقة
    modal = document.createElement('div');
    modal.id = 'analysisModal';
    modal.className = 'modal fade';
    modal.tabIndex = '-1';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">تحليل نظام الذكاء الاصطناعي</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <h6>إحصائيات قاعدة المعرفة</h6>
                        <ul>
                            <li>إجمالي الأسئلة: ${analysis.kb_stats.question_count}</li>
                            <li>متوسط طول الإجابة: ${analysis.kb_stats.avg_answer_length} حرف</li>
                        </ul>
                    </div>
                    <div class="mb-3">
                        <h6>تحليل الذاكرة المتقدمة</h6>
                        <ul>
                            <li>عدد عناصر الذاكرة: ${analysis.memory_stats.entry_count}</li>
                            <li>كفاءة البحث: ${analysis.memory_stats.retrieval_efficiency}%</li>
                        </ul>
                    </div>
                    <div class="mb-3">
                        <h6>تحليل شبكة المعرفة</h6>
                        <ul>
                            <li>عدد العقد: ${analysis.network_stats.node_count}</li>
                            <li>عدد الروابط: ${analysis.network_stats.edge_count}</li>
                            <li>العلاقات المستنتجة: ${analysis.network_stats.inferred_count}</li>
                        </ul>
                    </div>
                    <div class="mb-3">
                        <h6>توصيات لتحسين النظام</h6>
                        <ul>
                            ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // عرض النافذة المنبثقة
    new bootstrap.Modal(modal).show();
}

// ----- وظائف التفكير النقدي الذاتي -----

/**
 * تقييم استنتاج علاقة
 */
function evaluateInference() {
    const reflectionResults = document.getElementById('reflection-results');
    const source = document.getElementById('inference-source').value.trim();
    const target = document.getElementById('inference-target').value.trim();
    const relation = document.getElementById('inference-relation').value.trim();
    
    if (!source || !target || !relation) {
        reflectionResults.innerHTML = '<div class="alert alert-warning">يرجى تعبئة جميع الحقول!</div>';
        return;
    }
    
    reflectionResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التقييم...</span>
            </div>
            <p class="mt-2">جاري تقييم العلاقة...</p>
        </div>
    `;
    
    fetch('/evaluate-inference', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            source: source,
            target: target,
            relation: relation,
            confidence: 0.5 // قيمة افتراضية للثقة الأولية
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const result = data.result;
            const isValid = result.is_valid;
            const judgmentClass = isValid ? 'text-success' : 'text-danger';
            const judgmentIcon = isValid ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
            const confidencePercent = Math.round(result.adjusted_confidence * 100);
            
            reflectionResults.innerHTML = `
                <div class="card border-${isValid ? 'success' : 'danger'}">
                    <div class="card-header bg-${isValid ? 'success' : 'danger'} text-white">
                        <i class="bi ${judgmentIcon} me-2"></i>
                        <span class="fw-bold">${isValid ? 'استنتاج صحيح' : 'استنتاج غير صحيح'}</span>
                        <span class="badge bg-light text-dark float-end">${confidencePercent}% ثقة</span>
                    </div>
                    <div class="card-body">
                        <p class="card-text">
                            <strong>العلاقة المقيمة:</strong> 
                            ${source} <span class="fw-bold">${relation}</span> ${target}
                        </p>
                        <h6 class="card-subtitle mb-2 text-muted">التفكير النقدي:</h6>
                        <p class="card-text">${result.reasoning}</p>
                    </div>
                </div>
            `;
        } else {
            reflectionResults.innerHTML = `<div class="alert alert-danger">فشل تقييم العلاقة: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        reflectionResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة تقييم العلاقة</div>';
    });
}

/**
 * توليد أسئلة تفكير نقدي
 */
function generateCriticalQuestions() {
    const reflectionResults = document.getElementById('reflection-results');
    const topic = document.getElementById('question-topic').value.trim();
    const count = document.getElementById('question-count').value;
    
    if (!topic) {
        reflectionResults.innerHTML = '<div class="alert alert-warning">يرجى إدخال موضوع للتفكير النقدي!</div>';
        return;
    }
    
    reflectionResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري توليد الأسئلة...</span>
            </div>
            <p class="mt-2">جاري توليد أسئلة تفكير نقدي حول "${topic}"...</p>
        </div>
    `;
    
    fetch('/generate-critical-questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic: topic,
            count: count
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.questions.length > 0) {
            reflectionResults.innerHTML = `
                <div class="card border-info">
                    <div class="card-header bg-info text-white">
                        <i class="bi bi-patch-question-fill me-2"></i>
                        أسئلة تفكير نقدي حول "${topic}"
                    </div>
                    <div class="card-body">
                        <ol class="mb-0">
                            ${data.questions.map(question => `<li class="mb-2">${question}</li>`).join('')}
                        </ol>
                    </div>
                </div>
            `;
        } else {
            reflectionResults.innerHTML = `<div class="alert alert-danger">فشل توليد الأسئلة: ${data.message || 'لم يتم توليد أي أسئلة'}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        reflectionResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة توليد الأسئلة</div>';
    });
}

/**
 * تحميل سجل التفكير الذاتي
 */
function loadReflectionHistory() {
    const historyContainer = document.getElementById('reflection-history');
    
    fetch('/get-reflection-history')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.records.length > 0) {
            let historyHtml = '';
            
            data.records.forEach(record => {
                const date = new Date(record.timestamp * 1000).toLocaleString();
                const isValid = record.judgment === 'VALID';
                
                historyHtml += `
                    <div class="log-item mb-2 p-2 border-bottom">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="timestamp text-muted"><i class="bi bi-clock me-1"></i>${date}</span>
                            <span class="badge bg-${isValid ? 'success' : 'danger'}">
                                <i class="bi bi-${isValid ? 'check' : 'x'}-circle me-1"></i>${record.judgment}
                            </span>
                        </div>
                        <div class="mt-1">
                            <strong>${record.source}</strong> 
                            <span class="badge bg-secondary">${record.relation}</span> 
                            <strong>${record.target}</strong>
                        </div>
                    </div>
                `;
            });
            
            historyContainer.innerHTML = historyHtml;
        } else {
            historyContainer.innerHTML = '<p class="text-center text-muted py-3">لا يوجد سجل تفكير متاح حتى الآن.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        historyContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل سجل التفكير.</p>';
    });
}

// ----- وظائف الذاكرة المتقدمة -----

/**
 * البحث في الذاكرة المتقدمة
 */
function searchMemory() {
    const memoryResults = document.getElementById('memory-results');
    const query = document.getElementById('memory-search').value.trim();
    const count = document.getElementById('memory-results-count').value;
    
    if (!query) {
        memoryResults.innerHTML = '<div class="alert alert-warning">يرجى إدخال استعلام للبحث!</div>';
        return;
    }
    
    memoryResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري البحث...</span>
            </div>
            <p class="mt-2">جاري البحث عن "${query}"...</p>
        </div>
    `;
    
    fetch('/search-memory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: query,
            count: count
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.results.length > 0) {
            let resultsHtml = '';
            
            data.results.forEach((result, index) => {
                const similarityPercent = Math.round(result.similarity * 100);
                resultsHtml += `
                    <div class="card mb-3">
                        <div class="card-header bg-light d-flex justify-content-between align-items-center">
                            <span class="fw-bold">${index + 1}. تشابه ${similarityPercent}%</span>
                            <span class="badge bg-secondary">${result.source}</span>
                        </div>
                        <div class="card-body">
                            <h6 class="card-subtitle mb-2 text-primary">${result.question}</h6>
                            <p class="card-text">${result.answer}</p>
                        </div>
                    </div>
                `;
            });
            
            memoryResults.innerHTML = resultsHtml;
        } else {
            memoryResults.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    لم يتم العثور على نتائج مطابقة لـ "${query}" في الذاكرة المتقدمة.
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        memoryResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة البحث في الذاكرة</div>';
    });
}

/**
 * إضافة معرفة جديدة للذاكرة
 */
function addMemory() {
    const memoryResults = document.getElementById('memory-results');
    const question = document.getElementById('memory-question').value.trim();
    const answer = document.getElementById('memory-answer').value.trim();
    
    if (!question || !answer) {
        memoryResults.innerHTML = '<div class="alert alert-warning">يرجى تعبئة حقلي السؤال والإجابة!</div>';
        return;
    }
    
    memoryResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري الإضافة...</span>
            </div>
            <p class="mt-2">جاري إضافة المعرفة للذاكرة المتقدمة...</p>
        </div>
    `;
    
    fetch('/add-to-memory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            answer: answer,
            source: 'dashboard_user'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            memoryResults.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    تمت إضافة المعرفة الجديدة للذاكرة المتقدمة بنجاح!
                </div>
                <div class="card">
                    <div class="card-header bg-light">
                        <span class="fw-bold">معرفة جديدة</span>
                    </div>
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-primary">${question}</h6>
                        <p class="card-text">${answer}</p>
                    </div>
                </div>
            `;
            
            // تفريغ حقول الإدخال
            document.getElementById('memory-question').value = '';
            document.getElementById('memory-answer').value = '';
            
            // تحديث إحصائيات الذاكرة
            loadDashboardStats();
        } else {
            memoryResults.innerHTML = `<div class="alert alert-danger">فشل إضافة المعرفة: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        memoryResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة إضافة المعرفة للذاكرة</div>';
    });
}

/**
 * تنظيف الذاكرة المتقدمة
 */
function cleanupMemory() {
    const memoryResults = document.getElementById('memory-results');
    const maxAge = document.getElementById('memory-maintenance').value;
    
    memoryResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التنظيف...</span>
            </div>
            <p class="mt-2">جاري تنظيف الذاكرة المتقدمة (العناصر الأقدم من ${maxAge} يوم)...</p>
        </div>
    `;
    
    fetch('/cleanup-memory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            max_age_days: maxAge,
            min_access_count: 3
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            memoryResults.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    تم تنظيف الذاكرة المتقدمة بنجاح!
                </div>
                <div class="card">
                    <div class="card-body">
                        <p class="card-text">
                            <strong>العناصر المتبقية:</strong> ${data.remaining_count}<br>
                            <strong>العناصر المحذوفة:</strong> ${data.removed_count}<br>
                            <strong>نسبة تقليل الحجم:</strong> ${data.reduction_percent}%
                        </p>
                    </div>
                </div>
            `;
            
            // تحديث إحصائيات الذاكرة
            loadDashboardStats();
        } else {
            memoryResults.innerHTML = `<div class="alert alert-danger">فشل تنظيف الذاكرة: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        memoryResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة تنظيف الذاكرة</div>';
    });
}

// ----- وظائف الذكاء متعدد الوسائط -----

/**
 * معالجة تحميل الصورة
 */
function handleImageUpload(file) {
    if (!file.type.startsWith('image/')) {
        alert('يرجى تحميل ملف صورة فقط!');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        alert('حجم الصورة يتجاوز الحد الأقصى المسموح به (5 ميجابايت)!');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('image-preview');
        preview.src = e.target.result;
        
        document.getElementById('image-preview-container').style.display = 'block';
        document.getElementById('analyze-image-btn').removeAttribute('disabled');
    };
    
    reader.readAsDataURL(file);
}

/**
 * تحليل الصورة
 */
function analyzeImage() {
    const multimodalResults = document.getElementById('multimodal-results');
    const conceptsContainer = document.getElementById('concepts-container');
    const imagePreview = document.getElementById('image-preview');
    const query = document.getElementById('image-query').value.trim();
    
    if (!imagePreview.src) {
        multimodalResults.innerHTML = '<div class="alert alert-warning">يرجى تحميل صورة أولاً!</div>';
        return;
    }
    
    multimodalResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري تحليل الصورة...</span>
            </div>
            <p class="mt-2">جاري تحليل الصورة...</p>
        </div>
    `;
    
    conceptsContainer.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري استخراج المفاهيم...</span>
            </div>
            <p class="mt-2">جاري استخراج المفاهيم من الصورة...</p>
        </div>
    `;
    
    fetch('/analyze-image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_data: imagePreview.src,
            query: query
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            multimodalResults.innerHTML = `
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <i class="bi bi-image me-2"></i>
                        نتائج تحليل الصورة
                    </div>
                    <div class="card-body">
                        <p class="card-text">${data.description}</p>
                    </div>
                </div>
            `;
            
            // عرض المفاهيم المكتشفة
            if (data.concepts && data.concepts.length > 0) {
                let conceptsHtml = '<div class="d-flex flex-wrap">';
                
                data.concepts.forEach(concept => {
                    const confidencePercent = Math.round(concept.confidence * 100);
                    conceptsHtml += `
                        <div class="badge bg-info text-white m-1 p-2">
                            ${concept.concept}
                            <span class="badge bg-light text-dark ms-1">${confidencePercent}%</span>
                        </div>
                    `;
                });
                
                conceptsHtml += '</div>';
                conceptsContainer.innerHTML = conceptsHtml;
            } else {
                conceptsContainer.innerHTML = '<p class="text-center text-muted py-3">لم يتم اكتشاف مفاهيم محددة.</p>';
            }
        } else {
            multimodalResults.innerHTML = `<div class="alert alert-danger">فشل تحليل الصورة: ${data.message}</div>`;
            conceptsContainer.innerHTML = '<p class="text-center text-muted py-3">لم يتم اكتشاف مفاهيم.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        multimodalResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة تحليل الصورة</div>';
    });
}

/**
 * تحميل الأصوات المتاحة
 */
function loadAvailableVoices() {
    const voiceSelection = document.getElementById('voice-selection');
    
    fetch('/voices')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.voices.length > 0) {
            // إزالة الخيارات القديمة
            voiceSelection.innerHTML = '<option value="default">الصوت الافتراضي</option>';
            
            // إضافة الأصوات المتاحة
            data.voices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.voice_id;
                option.textContent = voice.name;
                voiceSelection.appendChild(option);
            });
        }
    })
    .catch(error => {
        console.error('Error loading voices:', error);
    });
}

/**
 * توليد كلام من نص
 */
function generateSpeech() {
    const multimodalResults = document.getElementById('multimodal-results');
    const audioPlayer = document.getElementById('audio-player');
    const audioContainer = document.getElementById('audio-player-container');
    const text = document.getElementById('text-to-speech').value.trim();
    const voiceId = document.getElementById('voice-selection').value;
    
    if (!text) {
        multimodalResults.innerHTML = '<div class="alert alert-warning">يرجى إدخال نص لتحويله إلى كلام!</div>';
        return;
    }
    
    multimodalResults.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري توليد الكلام...</span>
            </div>
            <p class="mt-2">جاري تحويل النص إلى كلام...</p>
        </div>
    `;
    
    fetch('/text-to-speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            voice_id: voiceId === 'default' ? null : voiceId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.audio_base64) {
            multimodalResults.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    تم تحويل النص إلى كلام بنجاح!
                </div>
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <i class="bi bi-volume-up me-2"></i>
                        النص المحول
                    </div>
                    <div class="card-body">
                        <p class="card-text">${text}</p>
                    </div>
                </div>
            `;
            
            // تشغيل الصوت
            audioPlayer.src = 'data:audio/mp3;base64,' + data.audio_base64;
            audioContainer.style.display = 'block';
            audioPlayer.play();
        } else {
            multimodalResults.innerHTML = `<div class="alert alert-danger">فشل تحويل النص إلى كلام: ${data.message}</div>`;
            audioContainer.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        multimodalResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء محاولة تحويل النص إلى كلام</div>';
    });
}

// ----- وظائف الوكيل المستقل -----

/**
 * تحميل بيانات الوكيل المستقل
 */
function loadAgentData() {
    loadAgentObjectives();
    loadAgentLog();
    loadCompletedObjectives();
    loadKnowledgeGained();
}

/**
 * تحديث بيانات الوكيل المستقل
 */
function refreshAgentData() {
    loadAgentLog();
    loadCompletedObjectives();
    loadKnowledgeGained();
}

/**
 * تحميل أهداف التعلم الحالية
 */
function loadAgentObjectives() {
    const objectivesContainer = document.getElementById('agent-objectives');
    
    fetch('/get-agent-objectives')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.objectives.length > 0) {
            let objectivesHtml = '';
            
            data.objectives.forEach((objective, index) => {
                objectivesHtml += `
                    <div class="d-flex justify-content-between align-items-center mb-2 p-2 border-bottom">
                        <div>
                            <span class="badge bg-primary me-2">${index + 1}</span>
                            ${objective}
                        </div>
                        <button class="btn btn-sm btn-danger remove-objective-btn" data-objective="${objective}">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                `;
            });
            
            objectivesContainer.innerHTML = objectivesHtml;
            
            // إضافة مستمعي أحداث لأزرار الحذف
            document.querySelectorAll('.remove-objective-btn').forEach(button => {
                button.addEventListener('click', function() {
                    removeObjective(this.getAttribute('data-objective'));
                });
            });
        } else {
            objectivesContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد أهداف تعلم حالية.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        objectivesContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل أهداف التعلم.</p>';
    });
}

/**
 * تحميل سجل نشاط الوكيل
 */
function loadAgentLog() {
    const logContainer = document.getElementById('agent-log');
    
    fetch('/get-agent-log')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.log.length > 0) {
            let logHtml = '';
            
            data.log.forEach(entry => {
                const timestamp = new Date(entry.timestamp).toLocaleString();
                let typeClass = 'text-secondary';
                
                switch (entry.type) {
                    case 'system':
                        typeClass = 'text-primary';
                        break;
                    case 'add_objective':
                    case 'complete':
                        typeClass = 'text-success';
                        break;
                    case 'failure':
                        typeClass = 'text-danger';
                        break;
                    case 'process':
                    case 'plan':
                    case 'step':
                        typeClass = 'text-info';
                        break;
                    case 'search':
                    case 'knowledge':
                        typeClass = 'text-warning';
                        break;
                }
                
                logHtml += `
                    <div class="log-entry mb-2">
                        <span class="timestamp text-muted">[${timestamp}]</span>
                        <span class="${typeClass} fw-bold">[${entry.type.toUpperCase()}]</span>
                        <span>${entry.description}</span>
                    </div>
                `;
            });
            
            logContainer.innerHTML = logHtml;
            logContainer.scrollTop = logContainer.scrollHeight;
        } else {
            logContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد سجلات نشاط متاحة.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        logContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل سجل النشاط.</p>';
    });
}

/**
 * تحميل الأهداف المكتملة
 */
function loadCompletedObjectives() {
    const completedContainer = document.getElementById('completed-objectives');
    
    fetch('/get-completed-objectives')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.completed.length > 0) {
            let completedHtml = '';
            
            data.completed.forEach(obj => {
                const status = obj.status || 'completed';
                const statusClass = status === 'completed' ? 'bg-success' : 'bg-danger';
                const date = obj.completed_at ? new Date(obj.completed_at).toLocaleDateString() : '';
                
                completedHtml += `
                    <div class="card mb-2">
                        <div class="card-header py-2 bg-light d-flex justify-content-between align-items-center">
                            <span class="fw-bold">${obj.objective}</span>
                            <span class="badge ${statusClass}">${status}</span>
                        </div>
                        <div class="card-body py-2">
                            <small class="text-muted">اكتمل في: ${date}</small>
                            ${obj.summary ? `<p class="card-text mt-2 small">${obj.summary}</p>` : ''}
                        </div>
                    </div>
                `;
            });
            
            completedContainer.innerHTML = completedHtml;
        } else {
            completedContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد أهداف مكتملة.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        completedContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل الأهداف المكتملة.</p>';
    });
}

/**
 * تحميل المعرفة المكتسبة
 */
function loadKnowledgeGained() {
    const knowledgeContainer = document.getElementById('knowledge-gained');
    
    fetch('/get-knowledge-gained')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && Object.keys(data.knowledge).length > 0) {
            let knowledgeHtml = '<div class="accordion" id="knowledge-accordion">';
            
            Object.entries(data.knowledge).forEach(([topic, knowledge], index) => {
                knowledgeHtml += `
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading-${index}">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${index}">
                                ${topic}
                            </button>
                        </h2>
                        <div id="collapse-${index}" class="accordion-collapse collapse" data-bs-parent="#knowledge-accordion">
                            <div class="accordion-body small">
                                ${knowledge}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            knowledgeHtml += '</div>';
            knowledgeContainer.innerHTML = knowledgeHtml;
        } else {
            knowledgeContainer.innerHTML = '<p class="text-center text-muted py-3">لا توجد معرفة مكتسبة.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        knowledgeContainer.innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء تحميل المعرفة.</p>';
    });
}

/**
 * إضافة هدف تعليمي جديد
 */
function addObjective() {
    const objective = document.getElementById('new-learning-objective').value.trim();
    
    if (!objective) {
        alert('يرجى إدخال هدف تعليمي!');
        return;
    }
    
    fetch('/add-objective', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            objective: objective
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('new-learning-objective').value = '';
            loadAgentObjectives();
        } else {
            alert(`فشل إضافة الهدف: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة إضافة الهدف!');
    });
}

/**
 * إزالة هدف تعليمي
 */
function removeObjective(objective) {
    if (!confirm(`هل تريد بالتأكيد إزالة الهدف: "${objective}"؟`)) {
        return;
    }
    
    fetch('/remove-objective', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            objective: objective
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadAgentObjectives();
        } else {
            alert(`فشل إزالة الهدف: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة إزالة الهدف!');
    });
}

/**
 * توليد أهداف تعليمية جديدة
 */
function generateObjectives() {
    const topic = document.getElementById('generate-objectives-topic').value.trim();
    
    if (!topic) {
        alert('يرجى إدخال موضوع لتوليد الأهداف!');
        return;
    }
    
    fetch('/generate-objectives', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic: topic,
            count: 3
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('generate-objectives-topic').value = '';
            loadAgentObjectives();
            
            // إظهار الأهداف التي تم توليدها
            if (data.objectives && data.objectives.length > 0) {
                let message = 'تم توليد الأهداف التالية:\n\n';
                data.objectives.forEach((obj, i) => {
                    message += `${i+1}. ${obj}\n`;
                });
                alert(message);
            }
        } else {
            alert(`فشل توليد الأهداف: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة توليد الأهداف!');
    });
}

/**
 * تشغيل الوكيل المستقل
 */
function startAgent() {
    fetch('/start-agent', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('تم تشغيل الوكيل المستقل بنجاح!');
            setTimeout(loadAgentData, 1000);
        } else {
            alert(`فشل تشغيل الوكيل: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة تشغيل الوكيل!');
    });
}

/**
 * إيقاف الوكيل المستقل مؤقتًا
 */
function pauseAgent() {
    fetch('/pause-agent', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('تم إيقاف الوكيل المستقل مؤقتًا بنجاح!');
            setTimeout(loadAgentData, 1000);
        } else {
            alert(`فشل إيقاف الوكيل: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة إيقاف الوكيل!');
    });
}

/**
 * تصدير المعرفة المكتسبة
 */
function exportKnowledge() {
    fetch('/export-knowledge', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            format: 'markdown'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.open('/download-knowledge', '_blank');
        } else {
            alert(`فشل تصدير المعرفة: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء محاولة تصدير المعرفة!');
    });
}

// ----- وظائف شبكة المعرفة -----

let networkInstance = null;

/**
 * استعلام شبكة المعرفة
 */
function queryKnowledgeNetwork() {
    const concept = document.getElementById('network-concept').value.trim();
    const depth = document.getElementById('relationship-depth').value;
    
    if (!concept) {
        alert('يرجى إدخال مفهوم للبحث في شبكة المعرفة!');
        return;
    }
    
    document.getElementById('network-empty').style.display = 'none';
    document.getElementById('network-loading').style.display = 'block';
    document.getElementById('knowledge-network-viz').style.display = 'none';
    document.getElementById('related-concepts').innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">جاري البحث في الشبكة...</p></div>';
    
    fetch('/query-knowledge-network', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            concept: concept,
            depth: depth,
            show_inferred: document.getElementById('show-inferred').checked
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('network-loading').style.display = 'none';
        
        if (data.status === 'success' && data.network && data.network.nodes && data.network.nodes.length > 0) {
            document.getElementById('knowledge-network-viz').style.display = 'block';
            createNetworkVisualization(data.network);
            displayRelatedConcepts(data.related_concepts);
        } else {
            document.getElementById('network-empty').style.display = 'block';
            document.getElementById('related-concepts').innerHTML = '<p class="text-center text-muted py-3">لم يتم العثور على مفاهيم مرتبطة.</p>';
            alert(`لم يتم العثور على "${concept}" في شبكة المعرفة.`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('network-loading').style.display = 'none';
        document.getElementById('network-empty').style.display = 'block';
        document.getElementById('related-concepts').innerHTML = '<p class="text-center text-danger py-3">حدث خطأ أثناء استعلام شبكة المعرفة.</p>';
        alert('حدث خطأ أثناء استعلام شبكة المعرفة!');
    });
}

/**
 * إنشاء رسم لشبكة المعرفة
 */
function createNetworkVisualization(networkData) {
    const container = document.getElementById('knowledge-network-viz');
    
    // تطبيق الخيارات المحددة
    const nodeSize = parseInt(document.getElementById('node-size').value);
    const showLabels = document.getElementById('show-labels').checked;
    const displayMode = document.getElementById('display-mode').value;
    
    // إعداد البيانات للعرض
    const nodes = new vis.DataSet(
        networkData.nodes.map(node => ({
            id: node.id,
            label: showLabels ? node.label : '',
            title: node.label,
            color: getNodeColor(node.type),
            size: node.main ? nodeSize * 1.5 : nodeSize,
            font: { size: 12 }
        }))
    );
    
    const edges = new vis.DataSet(
        networkData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            label: showLabels ? edge.label : '',
            title: edge.label,
            arrows: 'to',
            color: edge.inferred ? '#ff9800' : '#2196f3',
            dashes: edge.inferred,
            width: edge.inferred ? 1 : 2
        }))
    );
    
    // الخيارات
    const options = {
        nodes: {
            shape: 'dot',
            borderWidth: 1,
            borderWidthSelected: 3,
            shadow: true
        },
        edges: {
            shadow: true,
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            enabled: true,
            stabilization: true,
            solver: 'forceAtlas2Based'
        },
        interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            navigationButtons: true,
            hover: true
        }
    };
    
    // تطبيق وضع العرض المحدد
    if (displayMode === 'hierarchical') {
        options.layout = {
            hierarchical: {
                direction: 'UD',
                sortMethod: 'directed',
                levelSeparation: 100,
                nodeSpacing: 150
            }
        };
    } else if (displayMode === 'radial') {
        options.layout = {
            improvedLayout: true
        };
        options.physics = {
            enabled: true,
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 100,
                springConstant: 0.08
            },
            maxVelocity: 50,
            minVelocity: 0.1,
            solver: 'forceAtlas2Based',
            stabilization: {
                enabled: true,
                iterations: 1000,
                updateInterval: 100
            }
        };
    }
    
    // إنشاء الشبكة
    if (networkInstance) {
        networkInstance.destroy();
    }
    
    const data = {
        nodes: nodes,
        edges: edges
    };
    
    networkInstance = new vis.Network(container, data, options);
    
    // إضافة مستمع للنقر على العقد
    networkInstance.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeData = networkData.nodes.find(n => n.id === nodeId);
            if (nodeData) {
                highlightRelatedNodes(nodeData.id);
            }
        }
    });
    
    // إضافة مستمع لإعادة الضبط عند النقر على الخلفية
    networkInstance.on('click', function(params) {
        if (params.nodes.length === 0) {
            resetHighlights();
        }
    });
}

/**
 * الحصول على لون العقدة بناءً على النوع
 */
function getNodeColor(nodeType) {
    switch (nodeType) {
        case 'question':
            return { background: '#2196f3', border: '#1565c0' };
        case 'entity':
            return { background: '#4caf50', border: '#2e7d32' };
        case 'source':
            return { background: '#9c27b0', border: '#6a1b9a' };
        case 'concept':
            return { background: '#ff9800', border: '#e65100' };
        default:
            return { background: '#607d8b', border: '#37474f' };
    }
}

/**
 * تسليط الضوء على العقد المرتبطة
 */
function highlightRelatedNodes(nodeId) {
    if (!networkInstance) return;
    
    const connectedNodes = networkInstance.getConnectedNodes(nodeId);
    const allNodes = networkInstance.body.nodes;
    const allEdges = networkInstance.body.edges;
    
    // إعادة تعيين الألوان أولاً
    resetHighlights();
    
    // تسليط الضوء على العقدة المحددة وعقدها المتصلة
    for (const nodeKey in allNodes) {
        const node = allNodes[nodeKey];
        
        if (node.id === nodeId) {
            node.options.color.background = '#e91e63';
            node.options.color.border = '#880e4f';
            node.options.borderWidth = 3;
        } else if (connectedNodes.includes(node.id)) {
            node.options.opacity = 1.0;
            node.options.borderWidth = 2;
        } else {
            node.options.opacity = 0.3;
        }
    }
    
    // تسليط الضوء على الروابط
    for (const edgeKey in allEdges) {
        const edge = allEdges[edgeKey];
        
        if (edge.from.id === nodeId || edge.to.id === nodeId) {
            edge.options.opacity = 1.0;
            edge.options.width = 3;
        } else {
            edge.options.opacity = 0.3;
        }
    }
    
    networkInstance.redraw();
}

/**
 * إعادة تعيين تسليط الضوء
 */
function resetHighlights() {
    if (!networkInstance) return;
    
    const allNodes = networkInstance.body.nodes;
    const allEdges = networkInstance.body.edges;
    
    for (const nodeKey in allNodes) {
        const node = allNodes[nodeKey];
        node.options.opacity = 1.0;
        node.options.borderWidth = 1;
        node.options.color = getNodeColor(node.options.type || 'unknown');
    }
    
    for (const edgeKey in allEdges) {
        const edge = allEdges[edgeKey];
        edge.options.opacity = 1.0;
        edge.options.width = edge.options.dashes ? 1 : 2;
    }
    
    networkInstance.redraw();
}

/**
 * تحديث رسم شبكة المعرفة
 */
function updateNetworkVisualization() {
    if (networkInstance) {
        // إعادة استعلام شبكة المعرفة للحصول على بيانات محدثة
        queryKnowledgeNetwork();
    }
}

/**
 * عرض المفاهيم المرتبطة
 */
function displayRelatedConcepts(concepts) {
    const container = document.getElementById('related-concepts');
    
    if (!concepts || concepts.length === 0) {
        container.innerHTML = '<p class="text-center text-muted py-3">لم يتم العثور على مفاهيم مرتبطة.</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    concepts.forEach(concept => {
        const similarityPercent = Math.round(concept.similarity * 100);
        html += `
            <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center concept-link" data-concept="${concept.concept}">
                ${concept.concept}
                <span class="badge bg-primary rounded-pill">${similarityPercent}%</span>
            </a>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    // إضافة مستمع للنقر على المفاهيم
    document.querySelectorAll('.concept-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const concept = this.getAttribute('data-concept');
            document.getElementById('network-concept').value = concept;
            queryKnowledgeNetwork();
        });
    });
}
