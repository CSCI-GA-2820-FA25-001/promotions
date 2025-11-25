// API Base URL
const API_BASE_URL = 'http://localhost:8080';
const PROMOTIONS_ENDPOINT = `${API_BASE_URL}/promotions`;

// State management
let editingPromotionId = null;
let deletePromotionId = null;

// DOM Elements
const promotionForm = document.getElementById('promotionForm');
const formContainer = document.getElementById('formContainer');
const formTitle = document.getElementById('formTitle');
const submitBtn = document.getElementById('submitBtn');
const cancelBtn = document.getElementById('cancelBtn');
const promotionsTable = document.getElementById('promotionsTable');
const promotionsTableBody = document.getElementById('promotionsTableBody');
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const messageContainer = document.getElementById('messageContainer');
const deleteModal = document.getElementById('deleteModal');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const promotionTypeSelect = document.getElementById('promotion_type');
const discountFields = document.getElementById('discountFields');
const openCreateBtn = document.getElementById("openCreateBtn");
const toggleListBtn = document.getElementById('toggleListBtn');
const keywordSearchInput = document.getElementById('keywordSearch');
const keywordSearchBtn = document.getElementById('keywordSearchBtn');
const startDateSearchInput = document.getElementById('startDateSearch');
const endDateSearchInput = document.getElementById('endDateSearch');
const dateSearchBtn = document.getElementById('dateSearchBtn');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    promotionsTable.style.display = 'none';
    emptyState.style.display = 'none';
    loadingIndicator.style.display = 'none';
    setupEventListeners();
    handlePromotionTypeChange();
});

// ===== Show Create Form =====
openCreateBtn.addEventListener("click", () => {
    formContainer.style.display = "block";
    formTitle.textContent = "Create New Promotion";
    submitBtn.textContent = "Create Promotion";

    // Clear previous values
    promotionForm.reset();
    document.getElementById("promotionId").value = "";
});

function hideForm() {
    const formContainer = document.getElementById("formContainer");
    formContainer.style.display = "none";

    // 清空 form 内容
    const promotionForm = document.getElementById("promotionForm");
    promotionForm.reset();
}

cancelBtn.addEventListener("click", () => {
    hideForm();
});

// Setup event listeners
function setupEventListeners() {
    promotionForm.addEventListener('submit', handleFormSubmit);
    cancelBtn.addEventListener('click', resetForm);
    promotionTypeSelect.addEventListener('change', handlePromotionTypeChange);
    confirmDeleteBtn.addEventListener('click', confirmDelete);
    cancelDeleteBtn.addEventListener('click', hideDeleteModal);
    
    // Close modal when clicking outside
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) {
            hideDeleteModal();
        }
    });

    toggleListBtn.addEventListener('click', async () => {
        const collapsed =
            promotionsTable.style.display === 'none' &&
            emptyState.style.display === 'none';

        if (collapsed) {
            // EXPAND
            toggleListBtn.textContent = "List All Promotions ▼";
            loadingIndicator.style.display = 'block';
            await loadPromotions();   // fetch & display
            loadingIndicator.style.display = 'none';
        } else {
            // COLLAPSE
            toggleListBtn.textContent = "List All Promotions ▲";
            promotionsTable.style.display = 'none';
            emptyState.style.display = 'none';
        }
    });

    keywordSearchBtn.addEventListener('click', () => {
        const term = keywordSearchInput.value.trim();
        promotionsTableBody.innerHTML = "";
        promotionsTable.style.display = "none";
        emptyState.style.display = "none";
        // Call list_promotions with ?q=term
        loadPromotions({ keyword: term || null });
    });

    // Hit Enter in the keyword input to search
    keywordSearchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            keywordSearchBtn.click();
        }
    });

    // 📅 Date range search
    dateSearchBtn.addEventListener('click', () => {
        const startVal = startDateSearchInput.value;
        const endVal = endDateSearchInput.value;
        promotionsTableBody.innerHTML = "";
        promotionsTable.style.display = "none";
        emptyState.style.display = "none";

        if (!startVal || !endVal) {
            showMessage('Please provide both start and end dates.', 'error');
            return;
        }

        loadPromotions({
            startDate: startVal,
            endDate: endVal,
        });
    });
}

// Show/hide discount fields based on promotion type
function handlePromotionTypeChange() {
    const promotionType = promotionTypeSelect.value;
    if (promotionType === 'discount') {
        discountFields.style.display = 'flex';
        document.getElementById('discount_value').required = false;
    } else {
        discountFields.style.display = 'none';
        document.getElementById('discount_value').value = '';
        document.getElementById('discount_type').value = '';
        document.getElementById('discount_value').required = false;
    }
}

// Load all promotions
async function loadPromotions(options = {}) {
    const { keyword = null, startDate = null, endDate = null } = options;
    showLoading();
    try {
        // Build query params to match list_promotions in routes.py
        const params = new URLSearchParams();

        if (keyword) {
            // list_promotions uses `q` or `keyword`
            params.append('q', keyword);
        }

        if (startDate && endDate) {
            // Backend expects ISO-like strings; reuse your formatter
            const startIso = formatDateTimeForAPI(startDate);
            const endIso = formatDateTimeForAPI(endDate);
            if (startIso && endIso) {
                params.append('start_date', startIso);
                params.append('end_date', endIso);
            }
        }

        let url = PROMOTIONS_ENDPOINT;
        const queryString = params.toString();
        if (queryString) {
            url += `?${queryString}`;
        }

        // Use 'manager' role to see all promotions including draft, active, expired
        const response = await fetch(PROMOTIONS_ENDPOINT, {
            headers: {
                'X-Role': 'manager'
            }
        });
        
        console.log('Load promotions response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }
        
        const promotions = await response.json();
        console.log('Loaded promotions:', promotions);
        console.log('Number of promotions:', Array.isArray(promotions) ? promotions.length : 0);
        
        // Always hide loading after getting response
        hideLoading();
        
        // Display promotions (could be empty array)
        displayPromotions(promotions);
    } catch (error) {
        console.error('Error loading promotions:', error);
        hideLoading();
        showMessage('Error loading promotions: ' + error.message, 'error');
        // Show empty state on error
        promotionsTable.style.display = 'none';
        emptyState.style.display = 'block';
        emptyState.innerHTML = '<p>Error loading promotions. Please refresh the page.</p>';
    }
}

// Display promotions in table
function displayPromotions(promotions) {
    promotionsTableBody.innerHTML = '';
    
    // Ensure promotions is an array
    if (!Array.isArray(promotions)) {
        console.error('Promotions is not an array:', promotions);
        promotions = [];
    }
    
    if (promotions.length === 0) {
        promotionsTable.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    promotionsTable.style.display = 'table';
    emptyState.style.display = 'none';
    
    promotions.forEach(promotion => {
        const row = createPromotionRow(promotion);
        promotionsTableBody.appendChild(row);
    });
}

// Create a table row for a promotion
function createPromotionRow(promotion) {
    const row = document.createElement('tr');
    
    const discountInfo = promotion.discount_type && promotion.discount_value 
        ? `${promotion.discount_value}${promotion.discount_type === 'percent' ? '%' : '$'}`
        : '-';
    
    const expirationDate = promotion.expiration_date 
        ? new Date(promotion.expiration_date).toLocaleDateString() 
        : '-';
    
    row.innerHTML = `
        <td>${promotion.id}</td>
        <td>${escapeHtml(promotion.product_name)}</td>
        <td>$${promotion.original_price.toFixed(2)}</td>
        <td>${discountInfo}</td>
        <td>$${promotion.discounted_price.toFixed(2)}</td>
        <td><span class="status-badge status-${promotion.status}">${promotion.status}</span></td>
        <td>${expirationDate}</td>
        <td class="actions">
            <button class="btn btn-small btn-primary" onclick="editPromotion(${promotion.id})">Edit</button>
            <button class="btn btn-small btn-primary" onclick="duplicatePromotion(${promotion.id})">Duplicate</button>
            <button class="btn btn-small btn-danger" onclick="showDeleteModal(${promotion.id})">Delete</button>
        </td>
    `;
    
    return row;
}

// Handle form submission (Create or Update)
async function handleFormSubmit(e) {
    e.preventDefault();
    clearErrors();
    
    const formData = new FormData(promotionForm);
    const promotionData = {
        product_name: formData.get('product_name'),
        description: formData.get('description') || null,
        original_price: parseFloat(formData.get('original_price')),
        promotion_type: formData.get('promotion_type'),
        expiration_date: formatDateTimeForAPI(formData.get('expiration_date')),
        status: formData.get('status') || 'draft'
    };
    
    // Add discount fields only if promotion type is discount
    if (promotionData.promotion_type === 'discount') {
        const discountValue = formData.get('discount_value');
        const discountType = formData.get('discount_type');
        if (discountValue) {
            promotionData.discount_value = parseFloat(discountValue);
            promotionData.discount_type = discountType || null;
        }
    }
    
    // Add start_date if provided
    const startDate = formData.get('start_date');
    if (startDate) {
        promotionData.start_date = formatDateTimeForAPI(startDate);
    }
    
    try {
        if (editingPromotionId) {
            await updatePromotion(editingPromotionId, promotionData);
        } else {
            await createPromotion(promotionData);
        }
    } catch (error) {
        console.error('Form submission error:', error);
    }
}

// Create a new promotion
async function createPromotion(promotionData) {
    showLoading();
    try {
        console.log('Creating promotion with data:', promotionData);
        const response = await fetch(PROMOTIONS_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promotionData)
        });
        
        const data = await response.json();
        console.log('Create promotion response:', response.status, data);
        
        if (!response.ok) {
            hideLoading();
            handleApiError(data, response.status);
            return;
        }
        
        showMessage('Promotion created successfully!', 'success');
        resetForm();
        // Reload promotions after a short delay
        setTimeout(async () => {
            await loadPromotions();
        }, 300);
    } catch (error) {
        hideLoading();
        showMessage('Error creating promotion: ' + error.message, 'error');
        console.error('Error creating promotion:', error);
    }
}

// Update an existing promotion
async function updatePromotion(id, promotionData) {
    showLoading();
    try {
        const response = await fetch(`${PROMOTIONS_ENDPOINT}/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promotionData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            hideLoading();
            handleApiError(data, response.status);
            return;
        }
        
        showMessage('Promotion updated successfully!', 'success');
        resetForm();
        await loadPromotions();
    } catch (error) {
        hideLoading();
        showMessage('Error updating promotion: ' + error.message, 'error');
        console.error('Error updating promotion:', error);
    }
}

// Edit a promotion
async function editPromotion(id) {
    showLoading();
    try {
        // show container
        const formContainer = document.getElementById("formContainer");
        formContainer.style.display = "block";
        const response = await fetch(`${PROMOTIONS_ENDPOINT}/${id}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const promotion = await response.json();
        populateForm(promotion);
        editingPromotionId = id;
        formTitle.textContent = 'Edit Promotion';
        submitBtn.textContent = 'Update Promotion';
        
        // Scroll to form
        formContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showMessage('Error loading promotion: ' + error.message, 'error');
        console.error('Error loading promotion:', error);
    } finally {
        hideLoading();
    }
}

// Populate form with promotion data
function populateForm(promotion) {
    document.getElementById('promotionId').value = promotion.id;
    document.getElementById('product_name').value = promotion.product_name || '';
    document.getElementById('description').value = promotion.description || '';
    document.getElementById('original_price').value = promotion.original_price || '';
    document.getElementById('promotion_type').value = promotion.promotion_type || '';
    document.getElementById('discount_value').value = promotion.discount_value || '';
    document.getElementById('discount_type').value = promotion.discount_type || '';
    document.getElementById('status').value = promotion.status || 'draft';
    
    // Format dates for datetime-local input
    const startDateValue = promotion.start_date ? formatDateTimeForInput(promotion.start_date) : '';
    const expirationDateValue = promotion.expiration_date ? formatDateTimeForInput(promotion.expiration_date) : '';
    
    document.getElementById('start_date').value = startDateValue;
    document.getElementById('expiration_date').value = expirationDateValue;
    
    // Handle discount fields visibility
    handlePromotionTypeChange();
}

// Show delete confirmation modal
function showDeleteModal(id) {
    deletePromotionId = id;
    deleteModal.style.display = 'flex';
}

// Hide delete confirmation modal
function hideDeleteModal() {
    deleteModal.style.display = 'none';
    deletePromotionId = null;
}

// Confirm and delete promotion
async function confirmDelete() {
    if (!deletePromotionId) return;
    
    showLoading();
    try {
        const response = await fetch(`${PROMOTIONS_ENDPOINT}/${deletePromotionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok && response.status !== 204) {
            const data = await response.json().catch(() => ({}));
            hideLoading();
            handleApiError(data, response.status);
            hideDeleteModal();
            return;
        }
        
        showMessage('Promotion deleted successfully!', 'success');
        hideDeleteModal();
        await loadPromotions();
    } catch (error) {
        hideLoading();
        showMessage('Error deleting promotion: ' + error.message, 'error');
        console.error('Error deleting promotion:', error);
        hideDeleteModal();
    }
}

// Duplicate an existing promotion
async function duplicatePromotion(id) {
    showLoading();
    try {
        console.log('Duplicating promotion with id:', id);

        const response = await fetch(`${PROMOTIONS_ENDPOINT}/${id}/duplicate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Role': 'administrator'   // required by duplicate_promotion route
            },
            body: JSON.stringify({})        // route requires JSON, even though it doesn't use it
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            hideLoading();
            handleApiError(data, response.status);
            return;
        }

        showMessage('Promotion duplicated successfully!', 'success');

        // Reload the promotions list so the new one appears
        await loadPromotions();  // or loadPromotions(currentSearchTerm) if you track it
    } catch (error) {
        hideLoading();
        showMessage('Error duplicating promotion: ' + error.message, 'error');
        console.error('Error duplicating promotion:', error);
    } finally {
        hideLoading();
    }
}


// Reset form to create mode
function resetForm() {
    promotionForm.reset();
    editingPromotionId = null;
    formTitle.textContent = 'Create New Promotion';
    submitBtn.textContent = 'Create Promotion';
    clearErrors();
    discountFields.style.display = 'none';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Handle API errors
function handleApiError(data, statusCode) {
    let errorMessage = 'An error occurred';
    
    if (data && data.message) {
        errorMessage = data.message;
    } else if (data && data.error) {
        errorMessage = data.error;
    }
    
    // Display field-specific errors if available
    if (data && data.errors) {
        Object.keys(data.errors).forEach(field => {
            const errorField = document.getElementById(`${field}_error`);
            if (errorField) {
                errorField.textContent = data.errors[field];
                errorField.style.display = 'block';
            }
        });
    }
    
    showMessage(errorMessage, 'error');
}

// Clear all error messages
function clearErrors() {
    const errorMessages = document.querySelectorAll('.error-message');
    errorMessages.forEach(error => {
        error.textContent = '';
        error.style.display = 'none';
    });
}

// Show message
function showMessage(message, type = 'info') {
    messageContainer.innerHTML = `<div class="message message-${type}">${escapeHtml(message)}</div>`;
    messageContainer.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageContainer.style.display = 'none';
        }, 5000);
    }
}

// Show loading indicator
function showLoading() {
    loadingIndicator.style.display = 'block';
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.style.display = 'none';
}

// Format datetime for API (ISO 8601)
function formatDateTimeForAPI(dateTimeString) {
    if (!dateTimeString) return null;
    
    try {
        // datetime-local input gives us format: YYYY-MM-DDTHH:mm (local time)
        // We need to convert to ISO format with timezone
        let dateStr = dateTimeString.trim();
        
        // Ensure we have the full format
        if (dateStr.length === 10) {
            // Only date, no time - add default time
            dateStr += 'T00:00';
        } else if (dateStr.length === 16) {
            // Has date and time but no seconds - add seconds
            dateStr += ':00';
        }
        
        // Parse as local time and convert to ISO string (UTC)
        // datetime-local values are in local time, so we parse them directly
        const date = new Date(dateStr);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.error('Invalid date format:', dateTimeString);
            return null;
        }
        
        // Return ISO string (will be in UTC)
        return date.toISOString();
    } catch (error) {
        console.error('Error formatting date for API:', dateTimeString, error);
        return null;
    }
}

// Format datetime for input field (datetime-local format)
function formatDateTimeForInput(isoString) {
    if (!isoString) return '';
    try {
        // Parse ISO string - backend sends ISO format dates
        // Handle formats like: "2025-11-21T12:00:00", "2025-11-21T12:00:00.000000", or with timezone
        const date = new Date(isoString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.error('Invalid ISO date string:', isoString);
            return '';
        }
        
        // Convert to local time for display (datetime-local uses local timezone)
        // Format: YYYY-MM-DDTHH:mm (datetime-local format requires exactly this)
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        // Return in format required by datetime-local input
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    } catch (error) {
        console.error('Error formatting date:', isoString, error);
        return '';
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally accessible
window.editPromotion = editPromotion;
window.duplicatePromotion = duplicatePromotion;
window.showDeleteModal = showDeleteModal;

