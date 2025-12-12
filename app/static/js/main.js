// 全局JavaScript函数
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏提示消息
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // 表格行点击效果
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('click', function(e) {
            // 如果点击的是按钮或链接，不触发行点击
            if (e.target.closest('button') || e.target.closest('a')) {
                return;
            }
            
            // 查找详情链接
            const detailLink = row.querySelector('a[href*="/projects/detail/"]');
            if (detailLink) {
                window.location.href = detailLink.href;
            }
        });
    });
    
    // 表单验证增强
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // 滚动到第一个错误字段
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    });
    
    // 文件上传预览
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                const fileName = file.name;
                
                // 显示文件信息
                let fileInfo = document.getElementById('file-info');
                if (!fileInfo) {
                    fileInfo = document.createElement('div');
                    fileInfo.id = 'file-info';
                    fileInfo.className = 'mt-2 text-muted small';
                    input.parentNode.appendChild(fileInfo);
                }
                fileInfo.textContent = `已选择: ${fileName} (${fileSize} MB)`;
            }
        });
    });
    
    // 动态表格列显示/隐藏
    const toggleColumnsBtn = document.getElementById('toggleColumnsBtn');
    if (toggleColumnsBtn) {
        toggleColumnsBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('columnsModal'));
            modal.show();
        });
    }
    
    // 应用列显示设置
    const applyColumnsBtn = document.getElementById('applyColumnsBtn');
    if (applyColumnsBtn) {
        applyColumnsBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('#columnsModal input[type="checkbox"]');
            const table = document.getElementById('projectsTable');
            
            if (table) {
                const headers = table.querySelectorAll('thead th');
                const rows = table.querySelectorAll('tbody tr');
                
                checkboxes.forEach(function(checkbox, index) {
                    const isVisible = checkbox.checked;
                    
                    // 显示/隐藏表头
                    if (headers[index]) {
                        headers[index].style.display = isVisible ? '' : 'none';
                    }
                    
                    // 显示/隐藏列数据
                    rows.forEach(function(row) {
                        const cells = row.querySelectorAll('td');
                        if (cells[index]) {
                            cells[index].style.display = isVisible ? '' : 'none';
                        }
                    });
                });
            }
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('columnsModal'));
            modal.hide();
        });
    }
    
    // 确认删除对话框
    window.confirmDelete = function(projectId) {
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        
        if (confirmBtn) {
            confirmBtn.href = '/projects/delete/' + projectId;
        }
        
        modal.show();
    };
    
    // 分步表单导航
    const nextSteps = document.querySelectorAll('.next-step');
    const prevSteps = document.querySelectorAll('.prev-step');
    const steps = document.querySelectorAll('.step');
    const progressBar = document.querySelector('.progress-bar');
    let currentStep = 0;
    
    function updateProgress() {
        const progress = ((currentStep + 1) / steps.length) * 100;
        if (progressBar) {
            progressBar.style.width = progress + '%';
            progressBar.textContent = `第${currentStep + 1}步 (${currentStep + 1}/${steps.length})`;
        }
    }
    
    function validateStep(stepIndex) {
        const step = steps[stepIndex];
        const inputs = step.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(function(input) {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }
    
    nextSteps.forEach(function(button) {
        button.addEventListener('click', function() {
            if (validateStep(currentStep)) {
                steps[currentStep].classList.add('d-none');
                currentStep++;
                steps[currentStep].classList.remove('d-none');
                updateProgress();
            }
        });
    });
    
    prevSteps.forEach(function(button) {
        button.addEventListener('click', function() {
            steps[currentStep].classList.add('d-none');
            currentStep--;
            steps[currentStep].classList.remove('d-none');
            updateProgress();
        });
    });
    
    // 初始化进度条
    if (progressBar && steps.length > 0) {
        updateProgress();
    }
});
// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY'
    }).format(amount);
}
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // 自动关闭
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}
