/**
 * ============================================================================
 * DocuMind AI - Modern Document Intelligence Client
 * Vanilla JavaScript (ES6+), Modular Architecture
 * Connected to FastAPI Backend (port 8000)
 * ============================================================================
 */

(function () {
  'use strict';

  // ==========================================================================
  // 1. CONFIGURATION & STATE
  // ==========================================================================
  const CONFIG = {
    DEFAULT_API_BASE_URL: 'http://127.0.0.1:8000/api',
    PROCESS_ENDPOINT: '/documents/process',
    HEALTH_ENDPOINT: '/health',
    EVALUATION_ENDPOINT: '/evaluation',
    MAX_FILE_SIZE_BYTES: 15 * 1024 * 1024, // 15MB
    LOW_CONFIDENCE_THRESHOLD: 0.85, // 85%
    SUPPORTED_EXTENSIONS: ['pdf', 'png', 'jpg', 'jpeg'],
    SUPPORTED_MIME_TYPES: [
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/jpg'
    ]
  };

  function getInitialApiBaseUrl() {
    let saved = localStorage.getItem('documind_api_base_url');
    // Auto-migrate legacy 5000 port to 8000 for FastAPI
    if (!saved || saved.includes(':5000')) {
      saved = CONFIG.DEFAULT_API_BASE_URL;
      localStorage.setItem('documind_api_base_url', saved);
    }
    return saved;
  }

  // Central Application State
  const state = {
    apiBaseUrl: getInitialApiBaseUrl(),
    isApiConnected: false,
    mockMode: localStorage.getItem('documind_mock_mode') === 'true',
    currentFile: null,
    currentPreviewUrl: null,
    isProcessing: false,
    extractionResult: null,
    evaluationData: null,
    activeSectionId: 'sectionDashboard',
    currentFilterMode: 'all',
    chartInstance: null
  };

  // ==========================================================================
  // 2. DOM ELEMENT REFERENCES
  // ==========================================================================
  const elements = {
    // Navigation
    sidebar: document.getElementById('sidebar'),
    sidebarNav: document.getElementById('sidebarNav'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    currentSectionTitle: document.getElementById('currentSectionTitle'),
    navItems: document.querySelectorAll('.nav-item'),
    viewSections: document.querySelectorAll('.view-section'),
    resultsCountBadge: document.getElementById('resultsCountBadge'),
    
    // API Status & Mock Banner
    apiStatusWidget: document.getElementById('apiStatusWidget'),
    apiStatusDot: document.getElementById('apiStatusDot'),
    apiStatusText: document.getElementById('apiStatusText'),
    apiEndpointText: document.getElementById('apiEndpointText'),
    btnCheckApiHealth: document.getElementById('btnCheckApiHealth'),
    mockModeToggle: document.getElementById('mockModeToggle'),
    mockBanner: document.getElementById('mockBanner'),
    btnDisableMockMode: document.getElementById('btnDisableMockMode'),

    // Dashboard Overview KPIs
    kpiCardStatus: document.getElementById('kpiCardStatus'),
    kpiDocStatus: document.getElementById('kpiDocStatus'),
    kpiDocStatusDesc: document.getElementById('kpiDocStatusDesc'),
    kpiIconStatus: document.getElementById('kpiIconStatus'),
    kpiFieldsExtracted: document.getElementById('kpiFieldsExtracted'),
    kpiExtractedSubtitle: document.getElementById('kpiExtractedSubtitle'),
    kpiFieldsReview: document.getElementById('kpiFieldsReview'),
    kpiReviewSubtitle: document.getElementById('kpiReviewSubtitle'),
    kpiFieldsMissing: document.getElementById('kpiFieldsMissing'),
    kpiMissingSubtitle: document.getElementById('kpiMissingSubtitle'),
    btnWorkflowUpload: document.getElementById('btnWorkflowUpload'),
    btnWorkflowResults: document.getElementById('btnWorkflowResults'),
    btnWorkflowEval: document.getElementById('btnWorkflowEval'),
    btnTopQuickUpload: document.getElementById('btnTopQuickUpload'),

    // Document Upload & Preview
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('fileInput'),
    selectedFileCard: document.getElementById('selectedFileCard'),
    selectedFileName: document.getElementById('selectedFileName'),
    selectedFileSize: document.getElementById('selectedFileSize'),
    fileTypeIcon: document.getElementById('fileTypeIcon'),
    btnReplaceFile: document.getElementById('btnReplaceFile'),
    btnRemoveFile: document.getElementById('btnRemoveFile'),
    btnLoadSampleInvoice: document.getElementById('btnLoadSampleInvoice'),
    uploadErrorAlert: document.getElementById('uploadErrorAlert'),
    uploadErrorMessage: document.getElementById('uploadErrorMessage'),
    btnExtractValidate: document.getElementById('btnExtractValidate'),
    btnExtractText: document.getElementById('btnExtractText'),
    btnResetDocument: document.getElementById('btnResetDocument'),
    documentStatusBadge: document.getElementById('documentStatusBadge'),
    previewSubtitle: document.getElementById('previewSubtitle'),
    previewEmptyState: document.getElementById('previewEmptyState'),
    previewImageWrapper: document.getElementById('previewImageWrapper'),
    previewImage: document.getElementById('previewImage'),
    previewPdfWrapper: document.getElementById('previewPdfWrapper'),
    previewPdfFrame: document.getElementById('previewPdfFrame'),
    previewControls: document.getElementById('previewControls'),
    btnZoomPreview: document.getElementById('btnZoomPreview'),
    processingOverlay: document.getElementById('processingOverlay'),

    // Results & Validation
    resDocType: document.getElementById('resDocType'),
    resDocId: document.getElementById('resDocId'),
    resThresholdText: document.getElementById('resThresholdText'),
    resultsSearchInput: document.getElementById('resultsSearchInput'),
    btnFilterAll: document.getElementById('btnFilterAll'),
    btnFilterReview: document.getElementById('btnFilterReview'),
    btnFilterMissing: document.getElementById('btnFilterMissing'),
    btnFilterInvalid: document.getElementById('btnFilterInvalid'),
    resultsTableBody: document.getElementById('resultsTableBody'),
    valTotalFields: document.getElementById('valTotalFields'),
    valPassedChecks: document.getElementById('valPassedChecks'),
    valLowConfFields: document.getElementById('valLowConfFields'),
    valMissingFields: document.getElementById('valMissingFields'),
    valReviewRequired: document.getElementById('valReviewRequired'),
    validationWarningsList: document.getElementById('validationWarningsList'),
    btnDownloadCSV: document.getElementById('btnDownloadCSV'),
    btnDownloadJSON: document.getElementById('btnDownloadJSON'),
    btnCopyJSON: document.getElementById('btnCopyJSON'),
    exportStatusNote: document.getElementById('exportStatusNote'),

    // Evaluation Dashboard
    evalLastUpdated: document.getElementById('evalLastUpdated'),
    btnRefreshEvaluation: document.getElementById('btnRefreshEvaluation'),
    evalDocsCount: document.getElementById('evalDocsCount'),
    evalOverallAccuracy: document.getElementById('evalOverallAccuracy'),
    evalTotalFieldsCount: document.getElementById('evalTotalFieldsCount'),
    evalReviewFieldsCount: document.getElementById('evalReviewFieldsCount'),
    evaluationGrid: document.getElementById('evaluationGrid'),
    evaluationTableBody: document.getElementById('evaluationTableBody'),
    evalUnavailableBanner: document.getElementById('evalUnavailableBanner'),
    btnRetryEvaluation: document.getElementById('btnRetryEvaluation'),
    accuracyChartCanvas: document.getElementById('accuracyChart'),

    // About & Settings
    apiBaseUrlInput: document.getElementById('apiBaseUrlInput'),
    btnSaveApiUrl: document.getElementById('btnSaveApiUrl'),
    btnTestApiConnection: document.getElementById('btnTestApiConnection'),
    apiTestResult: document.getElementById('apiTestResult'),

    // Lightbox & Toasts
    imageZoomModal: document.getElementById('imageZoomModal'),
    zoomModalImage: document.getElementById('zoomModalImage'),
    zoomModalTitle: document.getElementById('zoomModalTitle'),
    btnCloseZoomModal: document.getElementById('btnCloseZoomModal'),
    toastContainer: document.getElementById('toastContainer')
  };

  // ==========================================================================
  // 3. INITIALIZATION
  // ==========================================================================
  function initializeApp() {
    // 1. Setup API Base URL input value
    if (elements.apiBaseUrlInput) {
      elements.apiBaseUrlInput.value = state.apiBaseUrl;
      updateApiDisplayHost();
    }

    // 2. Setup Mock Mode UI state
    if (elements.mockModeToggle) {
      elements.mockModeToggle.checked = state.mockMode;
      updateMockModeBanner();
    }

    // 3. Bind all event listeners
    setupEventListeners();

    // 4. Initial Lucide icon generation
    refreshIcons();

    // 5. Check API Health
    checkApiHealth();

    // 6. Load evaluation benchmark report
    loadEvaluationReport(true);
  }

  function setupEventListeners() {
    // Navigation items
    elements.navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetSection = item.getAttribute('data-section');
        if (targetSection) {
          switchSection(targetSection);
        }
      });
    });

    // Mobile Hamburger
    if (elements.mobileMenuBtn) {
      elements.mobileMenuBtn.addEventListener('click', () => {
        elements.sidebar.classList.toggle('open');
      });
    }

    // Quick Jump Buttons
    if (elements.btnWorkflowUpload) {
      elements.btnWorkflowUpload.addEventListener('click', () => switchSection('sectionExtract'));
    }
    if (elements.btnWorkflowResults) {
      elements.btnWorkflowResults.addEventListener('click', () => switchSection('sectionResults'));
    }
    if (elements.btnWorkflowEval) {
      elements.btnWorkflowEval.addEventListener('click', () => switchSection('sectionEvaluation'));
    }
    if (elements.btnTopQuickUpload) {
      elements.btnTopQuickUpload.addEventListener('click', () => {
        switchSection('sectionExtract');
        if (elements.fileInput) elements.fileInput.click();
      });
    }

    // File Dropzone & Selection
    if (elements.dropzone) {
      elements.dropzone.addEventListener('click', () => {
        if (elements.fileInput) elements.fileInput.click();
      });

      ['dragenter', 'dragover'].forEach(eventName => {
        elements.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          elements.dropzone.classList.add('drag-over');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        elements.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          elements.dropzone.classList.remove('drag-over');
        });
      });

      elements.dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          handleFileSelection(dt.files[0]);
        }
      });
    }

    // File Input change
    if (elements.fileInput) {
      elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          handleFileSelection(e.target.files[0]);
        }
      });
    }

    // Replace and Remove Buttons
    if (elements.btnReplaceFile) {
      elements.btnReplaceFile.addEventListener('click', () => {
        if (elements.fileInput) elements.fileInput.click();
      });
    }
    if (elements.btnRemoveFile) {
      elements.btnRemoveFile.addEventListener('click', resetDocument);
    }
    if (elements.btnResetDocument) {
      elements.btnResetDocument.addEventListener('click', resetDocument);
    }

    // Sample Invoice loader
    if (elements.btnLoadSampleInvoice) {
      elements.btnLoadSampleInvoice.addEventListener('click', loadSampleInvoice);
    }

    // Extract & Validate Primary Button
    if (elements.btnExtractValidate) {
      elements.btnExtractValidate.addEventListener('click', extractDocument);
    }

    // Zoom Lightbox
    if (elements.btnZoomPreview) {
      elements.btnZoomPreview.addEventListener('click', openZoomModal);
    }
    if (elements.btnCloseZoomModal) {
      elements.btnCloseZoomModal.addEventListener('click', closeZoomModal);
    }
    if (elements.imageZoomModal) {
      elements.imageZoomModal.addEventListener('click', (e) => {
        if (e.target === elements.imageZoomModal) closeZoomModal();
      });
    }

    // Export buttons
    if (elements.btnDownloadCSV) {
      elements.btnDownloadCSV.addEventListener('click', downloadCSV);
    }
    if (elements.btnDownloadJSON) {
      elements.btnDownloadJSON.addEventListener('click', downloadJSON);
    }
    if (elements.btnCopyJSON) {
      elements.btnCopyJSON.addEventListener('click', copyJSONToClipboard);
    }

    // Evaluation Dashboard
    if (elements.btnRefreshEvaluation) {
      elements.btnRefreshEvaluation.addEventListener('click', () => loadEvaluationReport(false));
    }
    if (elements.btnRetryEvaluation) {
      elements.btnRetryEvaluation.addEventListener('click', () => loadEvaluationReport(false));
    }

    // Mock Mode Toggle
    if (elements.mockModeToggle) {
      elements.mockModeToggle.addEventListener('change', (e) => {
        state.mockMode = e.target.checked;
        localStorage.setItem('documind_mock_mode', state.mockMode ? 'true' : 'false');
        updateMockModeBanner();
        showToast(state.mockMode ? 'Mock Demo Mode enabled' : 'Mock Mode disabled (Live FastAPI API mode)', 'info');
        checkApiHealth();
      });
    }
    if (elements.btnDisableMockMode) {
      elements.btnDisableMockMode.addEventListener('click', () => {
        state.mockMode = false;
        elements.mockModeToggle.checked = false;
        localStorage.setItem('documind_mock_mode', 'false');
        updateMockModeBanner();
        showToast('Switched to live FastAPI backend', 'info');
        checkApiHealth();
      });
    }

    // API Configuration Settings
    if (elements.btnSaveApiUrl) {
      elements.btnSaveApiUrl.addEventListener('click', saveApiBaseUrl);
    }
    if (elements.btnTestApiConnection) {
      elements.btnTestApiConnection.addEventListener('click', testApiConnection);
    }
    if (elements.btnCheckApiHealth) {
      elements.btnCheckApiHealth.addEventListener('click', () => {
        showToast('Checking API connection...', 'info');
        checkApiHealth();
      });
    }

    // Results Search & Filter
    if (elements.resultsSearchInput) {
      elements.resultsSearchInput.addEventListener('input', () => filterResultsTable('search'));
    }
    if (elements.btnFilterAll) {
      elements.btnFilterAll.addEventListener('click', () => {
        if (elements.resultsSearchInput) elements.resultsSearchInput.value = '';
        filterResultsTable('all');
      });
    }
    if (elements.btnFilterReview) {
      elements.btnFilterReview.addEventListener('click', () => filterResultsTable('review'));
    }
    if (elements.btnFilterMissing) {
      elements.btnFilterMissing.addEventListener('click', () => filterResultsTable('missing'));
    }
    if (elements.btnFilterInvalid) {
      elements.btnFilterInvalid.addEventListener('click', () => filterResultsTable('invalid'));
    }

    // Keyboard support: ESC closes modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && elements.imageZoomModal && elements.imageZoomModal.classList.contains('open')) {
        closeZoomModal();
      }
    });
  }

  // ==========================================================================
  // 4. NAVIGATION & SECTION SWITCHING
  // ==========================================================================
  function switchSection(sectionId) {
    state.activeSectionId = sectionId;

    // Update active nav items
    elements.navItems.forEach(item => {
      if (item.getAttribute('data-section') === sectionId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Update visible view sections
    elements.viewSections.forEach(sec => {
      if (sec.id === sectionId) {
        sec.classList.add('active');
      } else {
        sec.classList.remove('active');
      }
    });

    // Close mobile drawer if open
    if (elements.sidebar && elements.sidebar.classList.contains('open')) {
      elements.sidebar.classList.remove('open');
    }

    // Update header title
    updateHeaderTitle(sectionId);

    // If switching to evaluation, resize chart to prevent distortion
    if (sectionId === 'sectionEvaluation' && state.chartInstance) {
      setTimeout(() => state.chartInstance.resize(), 100);
    }

    // Refresh icons
    refreshIcons();
  }

  function updateHeaderTitle(sectionId) {
    if (!elements.currentSectionTitle) return;
    const titleMap = {
      sectionDashboard: { text: 'Dashboard Overview', icon: 'layout-dashboard' },
      sectionExtract: { text: 'Document Intelligence Workspace', icon: 'file-up' },
      sectionResults: { text: 'Extraction Results & Validation', icon: 'table' },
      sectionEvaluation: { text: 'Held-Out Model Accuracy Evaluation', icon: 'bar-chart-3' },
      sectionAbout: { text: 'About DocuMind AI & API Settings', icon: 'settings' }
    };

    const info = titleMap[sectionId] || { text: 'DocuMind AI', icon: 'file-text' };
    elements.currentSectionTitle.innerHTML = `
      <i data-lucide="${info.icon}" style="width: 20px; height: 20px; color: var(--primary);"></i>
      <span>${escapeHtml(info.text)}</span>
    `;
    refreshIcons();
  }

  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // ==========================================================================
  // 5. API HEALTH & STATUS MANAGEMENT
  // ==========================================================================
  function updateApiDisplayHost() {
    try {
      const url = new URL(state.apiBaseUrl);
      if (elements.apiEndpointText) {
        elements.apiEndpointText.textContent = `${url.hostname}:${url.port || (url.protocol === 'https:' ? '443' : '80')}`;
      }
    } catch (e) {
      if (elements.apiEndpointText) elements.apiEndpointText.textContent = state.apiBaseUrl;
    }
  }

  function setApiStatus(status, text) {
    if (!elements.apiStatusDot || !elements.apiStatusText) return;
    elements.apiStatusDot.className = `status-dot ${status}`;
    elements.apiStatusText.textContent = text;
    state.isApiConnected = (status === 'connected');
  }

  async function checkApiHealth() {
    updateApiDisplayHost();

    // If Mock Mode is enabled, show Mock Status
    if (state.mockMode) {
      setApiStatus('connected', 'Mock Mode Active');
      return;
    }

    setApiStatus('connecting', 'Checking...');

    const healthUrl = `${state.apiBaseUrl.replace(/\/+$/, '')}${CONFIG.HEALTH_ENDPOINT}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    try {
      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        setApiStatus('connected', 'Connected');
      } else {
        setApiStatus('disconnected', `Error ${response.status}`);
      }
    } catch (err) {
      clearTimeout(timeoutId);
      setApiStatus('disconnected', 'Disconnected');
    }
  }

  function updateMockModeBanner() {
    if (!elements.mockBanner) return;
    if (state.mockMode) {
      elements.mockBanner.classList.add('active');
    } else {
      elements.mockBanner.classList.remove('active');
    }
  }

  function saveApiBaseUrl() {
    if (!elements.apiBaseUrlInput) return;
    const newUrl = elements.apiBaseUrlInput.value.trim();
    if (!newUrl) {
      showToast('API Base URL cannot be empty', 'error');
      return;
    }
    state.apiBaseUrl = newUrl;
    localStorage.setItem('documind_api_base_url', newUrl);
    showToast('API Base URL saved successfully', 'success');
    checkApiHealth();
    loadEvaluationReport(false);
  }

  async function testApiConnection() {
    if (!elements.apiTestResult) return;
    elements.apiTestResult.style.display = 'block';
    elements.apiTestResult.style.backgroundColor = '#F8FAFC';
    elements.apiTestResult.style.border = '1px solid var(--border)';
    elements.apiTestResult.style.color = 'var(--text-secondary)';
    elements.apiTestResult.textContent = `Pinging ${state.apiBaseUrl}${CONFIG.HEALTH_ENDPOINT}...`;

    const start = performance.now();
    try {
      const response = await fetch(`${state.apiBaseUrl.replace(/\/+$/, '')}${CONFIG.HEALTH_ENDPOINT}`, {
        method: 'GET'
      });
      const duration = Math.round(performance.now() - start);
      const text = await response.text();

      if (response.ok) {
        elements.apiTestResult.style.backgroundColor = '#F0FDF4';
        elements.apiTestResult.style.borderColor = '#86EFAC';
        elements.apiTestResult.style.color = '#166534';
        elements.apiTestResult.innerHTML = `
          <strong>Status: 200 OK (${duration}ms)</strong><br>
          Response: ${escapeHtml(text)}
        `;
        showToast('Backend is reachable!', 'success');
        setApiStatus('connected', 'Connected');
      } else {
        elements.apiTestResult.style.backgroundColor = '#FEF2F2';
        elements.apiTestResult.style.borderColor = '#FCA5A5';
        elements.apiTestResult.style.color = '#991B1B';
        elements.apiTestResult.innerHTML = `
          <strong>Status: ${response.status} ${response.statusText} (${duration}ms)</strong><br>
          Response: ${escapeHtml(text)}
        `;
        setApiStatus('disconnected', `Error ${response.status}`);
      }
    } catch (err) {
      elements.apiTestResult.style.backgroundColor = '#FEF2F2';
      elements.apiTestResult.style.borderColor = '#FCA5A5';
      elements.apiTestResult.style.color = '#991B1B';
      elements.apiTestResult.innerHTML = `
        <strong>Connection Failed:</strong> ${escapeHtml(err.message)}<br>
        <span style="font-size: 0.75rem; color: var(--text-secondary);">
          Ensure FastAPI is running on ${escapeHtml(state.apiBaseUrl)} with CORS enabled.
        </span>
      `;
      setApiStatus('disconnected', 'Disconnected');
    }
  }

  // ==========================================================================
  // 6. FILE SELECTION & CLIENT-SIDE VALIDATION
  // ==========================================================================
  function handleFileSelection(file) {
    hideUploadError();

    const validation = validateSelectedFile(file);
    if (!validation.valid) {
      displayError(validation.message);
      return;
    }

    state.currentFile = file;

    // Display selected file info
    if (elements.selectedFileName) elements.selectedFileName.textContent = file.name;
    if (elements.selectedFileSize) elements.selectedFileSize.textContent = formatBytes(file.size);
    if (elements.selectedFileCard) elements.selectedFileCard.classList.add('visible');

    // Update file type icon
    const ext = getFileExtension(file.name);
    if (elements.fileTypeIcon) {
      if (ext === 'pdf') {
        elements.fileTypeIcon.className = 'file-type-icon pdf';
        elements.fileTypeIcon.innerHTML = '<i data-lucide="file-text"></i>';
      } else {
        elements.fileTypeIcon.className = 'file-type-icon';
        elements.fileTypeIcon.innerHTML = '<i data-lucide="image"></i>';
      }
    }

    // Update document status badge
    if (elements.documentStatusBadge) {
      elements.documentStatusBadge.className = 'status-badge valid';
      elements.documentStatusBadge.textContent = 'Ready to Extract';
    }

    // Enable Extract button
    if (elements.btnExtractValidate) {
      elements.btnExtractValidate.disabled = false;
    }

    // Update Dashboard KPI card
    updateDashboardStatusKPI('Document Ready', 'File loaded & verified', 'valid', 'file-check');

    // Render local preview
    renderDocumentPreview(file);

    refreshIcons();
    showToast(`Loaded: ${file.name}`, 'info');
  }

  function validateSelectedFile(file) {
    if (!file) {
      return { valid: false, message: 'No file was provided.' };
    }

    // 1. File Size Check
    if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) {
      const maxMb = Math.round(CONFIG.MAX_FILE_SIZE_BYTES / (1024 * 1024));
      return {
        valid: false,
        message: `File size exceeds the ${maxMb}MB limit. (Current: ${formatBytes(file.size)})`
      };
    }

    if (file.size === 0) {
      return { valid: false, message: 'The selected file is empty (0 bytes).' };
    }

    // 2. Extension Check
    const ext = getFileExtension(file.name);
    if (!CONFIG.SUPPORTED_EXTENSIONS.includes(ext)) {
      return {
        valid: false,
        message: `Unsupported file type (.${ext}). Supported formats: PDF, PNG, JPG, JPEG.`
      };
    }

    // 3. MIME type check if present
    if (file.type && !CONFIG.SUPPORTED_MIME_TYPES.includes(file.type.toLowerCase()) && ext !== 'pdf') {
      return {
        valid: false,
        message: `Invalid MIME type (${file.type}). Please upload a valid image or PDF.`
      };
    }

    return { valid: true };
  }

  // ==========================================================================
  // 7. DOCUMENT PREVIEW (URL.createObjectURL Lifecycle)
  // ==========================================================================
  function renderDocumentPreview(file) {
    // Release existing Object URL to prevent memory leaks
    revokePreviewUrl();

    if (!file) {
      resetPreviewUI();
      return;
    }

    try {
      state.currentPreviewUrl = URL.createObjectURL(file);
    } catch (e) {
      displayError('Failed to generate local preview URL.');
      return;
    }

    const ext = getFileExtension(file.name);

    // Hide empty state
    if (elements.previewEmptyState) elements.previewEmptyState.style.display = 'none';

    if (ext === 'pdf') {
      // PDF Preview
      if (elements.previewImageWrapper) elements.previewImageWrapper.style.display = 'none';
      if (elements.previewPdfWrapper) {
        elements.previewPdfWrapper.style.display = 'block';
        elements.previewPdfFrame.src = state.currentPreviewUrl;
      }
      if (elements.previewControls) elements.previewControls.classList.remove('visible');
      if (elements.previewSubtitle) elements.previewSubtitle.textContent = `PDF Document Viewer: ${file.name}`;
    } else {
      // Image Preview (PNG, JPG, JPEG, SVG)
      if (elements.previewPdfWrapper) elements.previewPdfWrapper.style.display = 'none';
      if (elements.previewImageWrapper) {
        elements.previewImageWrapper.style.display = 'flex';
        elements.previewImage.src = state.currentPreviewUrl;
      }
      if (elements.previewControls) elements.previewControls.classList.add('visible');
      if (elements.previewSubtitle) elements.previewSubtitle.textContent = `Image Inspector: ${file.name}`;
    }
  }

  function revokePreviewUrl() {
    if (state.currentPreviewUrl) {
      URL.revokeObjectURL(state.currentPreviewUrl);
      state.currentPreviewUrl = null;
    }
  }

  function resetPreviewUI() {
    if (elements.previewEmptyState) elements.previewEmptyState.style.display = 'flex';
    if (elements.previewImageWrapper) {
      elements.previewImageWrapper.style.display = 'none';
      if (elements.previewImage) elements.previewImage.src = '';
    }
    if (elements.previewPdfWrapper) {
      elements.previewPdfWrapper.style.display = 'none';
      if (elements.previewPdfFrame) elements.previewPdfFrame.src = '';
    }
    if (elements.previewControls) elements.previewControls.classList.remove('visible');
    if (elements.previewSubtitle) elements.previewSubtitle.textContent = 'Inspect document details prior to processing';
  }

  function resetDocument() {
    revokePreviewUrl();
    state.currentFile = null;
    if (elements.fileInput) elements.fileInput.value = '';

    if (elements.selectedFileCard) elements.selectedFileCard.classList.remove('visible');
    if (elements.btnExtractValidate) elements.btnExtractValidate.disabled = true;

    if (elements.documentStatusBadge) {
      elements.documentStatusBadge.className = 'status-badge unavailable';
      elements.documentStatusBadge.textContent = 'No File Selected';
    }

    hideUploadError();
    resetPreviewUI();

    updateDashboardStatusKPI('No Document', 'Awaiting document upload', 'primary', 'file-text');
    showToast('Document cleared', 'info');
  }

  async function loadSampleInvoice() {
    try {
      // Load real valid sample PDF from dataset with valid magic bytes
      const response = await fetch('assets/sample_invoice.pdf');
      if (!response.ok) {
        // Fallback to PNG sample if PDF unavailable
        const pngRes = await fetch('assets/sample_invoice.png');
        if (!pngRes.ok) throw new Error('Sample invoice asset could not be loaded.');
        const blob = await pngRes.blob();
        const sampleFile = new File([blob], 'inv_03_summit_cloud.png', { type: 'image/png' });
        handleFileSelection(sampleFile);
        showToast('Loaded sample invoice (inv_03_summit_cloud.png)!', 'success');
        return;
      }

      const blob = await response.blob();
      const sampleFile = new File([blob], 'inv_01_techcorp.pdf', { type: 'application/pdf' });
      handleFileSelection(sampleFile);
      showToast('Loaded sample invoice (inv_01_techcorp.pdf) ready for extraction!', 'success');
    } catch (e) {
      displayError('Could not load sample invoice: ' + e.message);
    }
  }

  // ==========================================================================
  // 8. DOCUMENT EXTRACTION & PROCESSING
  // ==========================================================================
  async function extractDocument() {
    if (state.isProcessing) return; // Prevent duplicate clicks

    if (!state.currentFile) {
      displayError('Please select or drop a document before extracting.');
      return;
    }

    // Set processing state
    setProcessingState(true);
    hideUploadError();

    // In Mock Mode, provide simulated response for local testing
    if (state.mockMode) {
      setTimeout(() => {
        const mockResponse = getMockExtractionResponse(state.currentFile.name);
        handleExtractionSuccess(mockResponse);
        setProcessingState(false);
      }, 1200);
      return;
    }

    // Live Mode: POST /api/documents/process using FormData
    const extractUrl = `${state.apiBaseUrl.replace(/\/+$/, '')}${CONFIG.PROCESS_ENDPOINT}`;
    const formData = new FormData();
    formData.append('file', state.currentFile);

    try {
      const response = await fetch(extractUrl, {
        method: 'POST',
        body: formData
        // Note: Do NOT manually set Content-Type header with FormData;
        // the browser automatically sets multipart/form-data with boundary.
      });

      if (!response.ok) {
        let errDetail = `Server responded with HTTP ${response.status} (${response.statusText})`;
        try {
          const errJson = await response.json();
          if (errJson && errJson.detail) {
            errDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          } else if (errJson && errJson.message) {
            errDetail = errJson.message;
          }
        } catch (_) {}
        throw new Error(errDetail);
      }

      const data = await response.json();
      
      // Validate response structure
      if (typeof data !== 'object' || data === null) {
        throw new Error('Invalid response format: Expected JSON object.');
      }

      handleExtractionSuccess(data);
      showToast('Document extracted and validated successfully!', 'success');

    } catch (err) {
      console.error('DocuMind extraction error:', err);
      handleExtractionFailure(err);
    } finally {
      setProcessingState(false);
    }
  }

  function setProcessingState(isBusy) {
    state.isProcessing = isBusy;
    if (elements.btnExtractValidate) {
      elements.btnExtractValidate.disabled = isBusy;
      if (elements.btnExtractText) {
        elements.btnExtractText.textContent = isBusy ? 'Analyzing Document...' : 'Extract & Validate';
      }
    }
    if (elements.processingOverlay) {
      if (isBusy) {
        elements.processingOverlay.classList.add('visible');
      } else {
        elements.processingOverlay.classList.remove('visible');
      }
    }
  }

  function handleExtractionSuccess(data) {
    state.extractionResult = data;
    state.currentFilterMode = 'all';
    if (elements.resultsSearchInput) elements.resultsSearchInput.value = '';
    updateFilterButtonsUI('all');

    // Render results table & validation
    renderExtractionResults(data);
    renderValidationSummary(data);

    // Update document status badge based on FastAPI validation.overall_status or issues
    const validation = data.validation || {};
    const overallStatus = validation.overall_status || 'valid';
    const hasIssues = (Array.isArray(validation.issues) && validation.issues.length > 0) ||
                      (Array.isArray(validation.warnings) && validation.warnings.length > 0);

    let badgeClass = 'status-badge verified';
    let badgeText = 'Extracted & Verified';

    if (overallStatus === 'invalid') {
      badgeClass = 'status-badge failed';
      badgeText = 'Validation Failed';
    } else if (overallStatus === 'needs_review' || hasIssues) {
      badgeClass = 'status-badge warning';
      badgeText = 'Extracted (Warnings)';
    }

    if (elements.documentStatusBadge) {
      elements.documentStatusBadge.className = badgeClass;
      elements.documentStatusBadge.textContent = badgeText;
    }

    // Enable exports
    if (elements.btnDownloadCSV) elements.btnDownloadCSV.disabled = false;
    if (elements.btnDownloadJSON) elements.btnDownloadJSON.disabled = false;
    if (elements.btnCopyJSON) elements.btnCopyJSON.disabled = false;
    if (elements.exportStatusNote) {
      elements.exportStatusNote.textContent = 'Structured data is ready for CSV or JSON download.';
    }

    // Switch view to Results tab so user sees findings
    setTimeout(() => {
      switchSection('sectionResults');
    }, 400);
  }

  function handleExtractionFailure(err) {
    displayError(`Extraction failed: ${err.message}`);

    if (elements.documentStatusBadge) {
      elements.documentStatusBadge.className = 'status-badge failed';
      elements.documentStatusBadge.textContent = 'Extraction Failed';
    }

    updateDashboardStatusKPI('Extraction Failed', err.message, 'danger', 'alert-circle');
    showToast('Document extraction failed. Review error message.', 'error');
  }

  // ==========================================================================
  // 9. EXTRACTION RESULTS TABLE RENDERING (Safe DOM methods)
  // ==========================================================================
  function renderExtractionResults(data) {
    if (!elements.resultsTableBody) return;
    elements.resultsTableBody.innerHTML = '';

    const fieldsObj = data.fields || {};
    const fieldKeys = Object.keys(fieldsObj);

    // Update Metadata Chips
    if (elements.resDocType) {
      elements.resDocType.textContent = (data.document_type || 'invoice').toUpperCase();
    }
    if (elements.resDocId) {
      elements.resDocId.textContent = data.document_id || generateDocId();
    }
    if (elements.resultsCountBadge) {
      elements.resultsCountBadge.textContent = fieldKeys.length;
    }

    if (fieldKeys.length === 0) {
      const emptyRow = document.createElement('tr');
      emptyRow.innerHTML = `
        <td colspan="5">
          <div class="empty-table-state">
            <i data-lucide="file-question"></i>
            <span style="font-weight: 600; color: var(--text-secondary);">No fields detected</span>
            <span style="font-size: 0.8rem;">The backend returned zero extracted fields for this document.</span>
          </div>
        </td>
      `;
      elements.resultsTableBody.appendChild(emptyRow);
      refreshIcons();
      return;
    }

    // Counters for dashboard KPIs
    let extractedCount = 0;
    let reviewCount = 0;
    let missingCount = 0;
    let invalidCount = 0;

    fieldKeys.forEach(fieldKey => {
      const fieldData = fieldsObj[fieldKey];
      const isObject = typeof fieldData === 'object' && fieldData !== null;
      
      const rawValue = isObject ? fieldData.value : fieldData;
      const confidence = isObject ? fieldData.confidence : null;
      const rawStatus = (isObject && fieldData.status) ? fieldData.status : deriveFieldStatus(rawValue, confidence);
      const normalizedStatus = (rawStatus || 'extracted').toLowerCase();
      const validationNote = (isObject && fieldData.validation_message) ? fieldData.validation_message : '';
      const isUserCorrected = normalizedStatus === 'user_corrected' || (isObject && fieldData.user_corrected === true);

      const isMissing = (rawValue === null || rawValue === undefined || rawValue === '' || normalizedStatus === 'missing');
      const isOcrFailure = (normalizedStatus === 'needs_review' && (rawValue === null || rawValue === undefined || rawValue === ''));
      const isLowConf = (normalizedStatus === 'low_confidence') || (!isMissing && typeof confidence === 'number' && confidence < CONFIG.LOW_CONFIDENCE_THRESHOLD);
      const isInvalid = normalizedStatus === 'invalid' || normalizedStatus === 'failed';
      const isNeedsReview = isOcrFailure || isLowConf || isInvalid || normalizedStatus === 'needs_review' || normalizedStatus === 'warning';

      if (isMissing) {
        missingCount++;
      } else {
        extractedCount++;
      }

      if (isInvalid) {
        invalidCount++;
        reviewCount++;
      } else if (isNeedsReview || isOcrFailure) {
        reviewCount++;
      }

      // Build Row using safe DOM APIs
      const tr = document.createElement('tr');
      if (isMissing) {
        tr.className = 'row-missing';
      } else if (isInvalid) {
        tr.className = 'row-invalid';
      } else if (isUserCorrected) {
        tr.className = 'row-corrected';
      } else if (isNeedsReview || isLowConf) {
        tr.className = 'row-warning';
      } else {
        tr.className = 'row-extracted';
      }

      tr.setAttribute('data-field-name', fieldKey.toLowerCase());
      tr.setAttribute('data-status', isMissing ? 'missing' : (isInvalid ? 'invalid' : normalizedStatus));
      tr.setAttribute('data-requires-review', (isMissing || isNeedsReview || isInvalid || isLowConf) ? 'true' : 'false');

      // 1. Field Name Cell
      const tdName = document.createElement('td');
      const nameDiv = document.createElement('div');
      nameDiv.className = 'field-name-cell';
      
      const nameText = document.createElement('span');
      nameText.textContent = formatFieldLabel(fieldKey);
      
      const codeSpan = document.createElement('span');
      codeSpan.className = 'field-code';
      codeSpan.textContent = `(${fieldKey})`;

      nameDiv.appendChild(nameText);
      nameDiv.appendChild(codeSpan);
      tdName.appendChild(nameDiv);

      // 2. Extracted Value Cell with Inline Edit Controls
      const tdValue = document.createElement('td');
      const valBox = document.createElement('div');
      
      let boxClass = 'extracted-value-box';
      if (isMissing) boxClass += ' missing';
      else if (isInvalid) boxClass += ' invalid';
      else if (isUserCorrected) boxClass += ' user_corrected';
      else if (isNeedsReview || isLowConf) boxClass += ' warning';
      valBox.className = boxClass;
      
      const displayVal = formatFieldValue(fieldKey, rawValue);
      const valTextSpan = document.createElement('span');
      valTextSpan.style.overflow = 'hidden';
      valTextSpan.style.textOverflow = 'ellipsis';
      valTextSpan.style.flex = '1';

      if (isMissing) {
        valTextSpan.textContent = 'Absent from Document';
      } else if (isOcrFailure) {
        valTextSpan.textContent = 'Unparseable / OCR Failure';
        valTextSpan.style.color = '#B45309';
        valTextSpan.style.fontStyle = 'italic';
      } else {
        valTextSpan.textContent = displayVal;
      }

      valBox.appendChild(valTextSpan);

      // Mini action buttons group
      const btnGroup = document.createElement('div');
      btnGroup.style.display = 'inline-flex';
      btnGroup.style.alignItems = 'center';
      btnGroup.style.gap = '4px';

      // Copy Button
      if (!isMissing && rawValue !== null) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-mini-btn';
        copyBtn.title = 'Copy value';
        copyBtn.innerHTML = '<i data-lucide="copy"></i>';
        copyBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(String(rawValue));
          showToast(`Copied ${formatFieldLabel(fieldKey)}`, 'info');
        });
        btnGroup.appendChild(copyBtn);
      }

      // Inline Edit / Add Button
      const editBtn = document.createElement('button');
      editBtn.className = 'btn-action-edit';
      editBtn.title = isMissing ? 'Add missing value manually' : 'Edit or correct value';
      editBtn.innerHTML = `<i data-lucide="${isMissing ? 'plus' : 'edit-3'}"></i><span>${isMissing ? 'Add' : 'Edit'}</span>`;
      editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        startInlineEditing(fieldKey, tr, tdValue, rawValue);
      });
      btnGroup.appendChild(editBtn);

      valBox.appendChild(btnGroup);
      tdValue.appendChild(valBox);

      // 3. Confidence Cell
      const tdConfidence = document.createElement('td');
      tdConfidence.appendChild(renderConfidenceStatus(confidence, normalizedStatus, isMissing, isUserCorrected));

      // 4. Status Cell
      const tdStatus = document.createElement('td');
      tdStatus.appendChild(renderStatusBadge(normalizedStatus, isOcrFailure, isMissing, isUserCorrected));

      // 5. Validation / Note Cell
      const tdNote = document.createElement('td');
      tdNote.className = 'validation-cell';
      if (validationNote) {
        tdNote.textContent = validationNote;
        if (isInvalid) tdNote.classList.add('has-error');
        else if (isNeedsReview || isLowConf) tdNote.classList.add('has-warning');
      } else if (isMissing) {
        tdNote.textContent = 'Field absent from document layout.';
        tdNote.style.color = 'var(--text-tertiary)';
      } else if (isOcrFailure) {
        tdNote.textContent = 'Field label detected, but OCR failed to recognize value.';
        tdNote.classList.add('has-warning');
      } else if (isUserCorrected) {
        tdNote.textContent = 'Manually entered / verified by user.';
        tdNote.style.color = 'var(--primary)';
      } else if (isInvalid) {
        tdNote.textContent = 'Field value failed validation rule.';
        tdNote.classList.add('has-error');
      } else if (isLowConf) {
        tdNote.textContent = 'Confidence below threshold. Verify against document.';
        tdNote.classList.add('has-warning');
      } else {
        tdNote.textContent = 'Verified';
      }

      tr.appendChild(tdName);
      tr.appendChild(tdValue);
      tr.appendChild(tdConfidence);
      tr.appendChild(tdStatus);
      tr.appendChild(tdNote);

      elements.resultsTableBody.appendChild(tr);
    });

    // Update Dashboard KPIs
    if (elements.kpiFieldsExtracted) elements.kpiFieldsExtracted.textContent = extractedCount;
    if (elements.kpiExtractedSubtitle) elements.kpiExtractedSubtitle.textContent = `${fieldKeys.length} total fields configured`;
    
    if (elements.kpiFieldsReview) elements.kpiFieldsReview.textContent = reviewCount;
    if (elements.kpiReviewSubtitle) elements.kpiReviewSubtitle.textContent = reviewCount === 0 ? 'All checks verified' : 'Manual verification recommended';

    if (elements.kpiFieldsMissing) elements.kpiFieldsMissing.textContent = missingCount;
    if (elements.kpiMissingSubtitle) elements.kpiMissingSubtitle.textContent = missingCount === 0 ? 'All expected fields present' : `${missingCount} absent from layout`;

    const overallStatus = invalidCount > 0 ? 'Invalid Totals' : (reviewCount > 0 ? 'Review Needed' : 'Verified');
    const overallColor = invalidCount > 0 ? 'danger' : (reviewCount > 0 ? 'warning' : 'success');
    updateDashboardStatusKPI(overallStatus, `${extractedCount} extracted, ${missingCount} absent, ${reviewCount} review`, overallColor, 'check-circle');

    // Reapply active filter and refresh icons
    filterResultsTable(state.currentFilterMode || 'all');
    refreshIcons();
  }

  function startInlineEditing(fieldKey, tr, tdValue, currentRawValue) {
    tdValue.innerHTML = '';

    const container = document.createElement('div');
    container.className = 'inline-edit-container';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'inline-edit-input';
    input.value = currentRawValue !== null && currentRawValue !== undefined ? String(currentRawValue) : '';
    input.placeholder = `Enter ${formatFieldLabel(fieldKey)}`;

    const btnSave = document.createElement('button');
    btnSave.className = 'btn-xs btn-primary';
    btnSave.title = 'Save correction';
    btnSave.innerHTML = '<i data-lucide="check" style="width: 12px; height: 12px;"></i>';

    const btnCancel = document.createElement('button');
    btnCancel.className = 'btn-xs btn-secondary';
    btnCancel.title = 'Cancel';
    btnCancel.innerHTML = '<i data-lucide="x" style="width: 12px; height: 12px;"></i>';

    const doSave = () => {
      const rawInput = input.value.trim();
      saveManualCorrection(fieldKey, rawInput);
    };

    const doCancel = () => {
      renderExtractionResults(state.extractionResult);
    };

    btnSave.addEventListener('click', (e) => {
      e.stopPropagation();
      doSave();
    });

    btnCancel.addEventListener('click', (e) => {
      e.stopPropagation();
      doCancel();
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        doSave();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        doCancel();
      }
    });

    container.appendChild(input);
    container.appendChild(btnSave);
    container.appendChild(btnCancel);
    tdValue.appendChild(container);
    refreshIcons();
    input.focus();
    input.select();
  }

  function saveManualCorrection(fieldKey, rawInput) {
    if (!state.extractionResult || !state.extractionResult.fields) return;

    const isNumericField = ['subtotal', 'tax', 'grand_total', 'total'].some(k => fieldKey.toLowerCase().includes(k));
    let parsedValue = rawInput;
    let newStatus = 'user_corrected';
    let validationMsg = 'Manually entered / verified by user';

    if (rawInput === '') {
      parsedValue = null;
      newStatus = 'missing';
      validationMsg = 'Marked as absent by user';
    } else if (isNumericField) {
      const cleanNum = rawInput.replace(/[^0-9.-]/g, '');
      const num = parseFloat(cleanNum);
      if (!isNaN(num)) {
        parsedValue = Math.round(num * 100) / 100;
      } else {
        showToast(`Invalid numeric value for ${formatFieldLabel(fieldKey)}`, 'warning');
        return;
      }
    }

    state.extractionResult.fields[fieldKey] = {
      value: parsedValue,
      confidence: parsedValue !== null ? 1.0 : null,
      status: newStatus,
      validation_message: validationMsg,
      user_corrected: true
    };

    recalculateClientValidation();
    renderExtractionResults(state.extractionResult);
    renderValidationSummary(state.extractionResult);
    showToast(`Updated ${formatFieldLabel(fieldKey)} successfully!`, 'success');
  }

  function recalculateClientValidation() {
    if (!state.extractionResult) return;
    const fields = state.extractionResult.fields || {};
    const validation = state.extractionResult.validation || { issues: [], warnings: [], passed: true, overall_status: 'valid' };

    const getVal = (k) => {
      const f = fields[k];
      return (f && typeof f === 'object') ? f.value : f;
    };

    const subtotalVal = getVal('subtotal');
    const taxVal = getVal('tax');
    const grandTotalVal = getVal('grand_total');

    let newIssues = Array.isArray(validation.issues) ? [...validation.issues] : [];
    // Clear arithmetic mismatch issues to recalculate
    newIssues = newIssues.filter(iss => !(iss.code && iss.code.includes('TOTAL_MISMATCH')));

    // Only apply arithmetic validation when required numeric values are available
    if (typeof subtotalVal === 'number' && typeof taxVal === 'number' && typeof grandTotalVal === 'number') {
      const expected = subtotalVal + taxVal;
      const diff = Math.abs(expected - grandTotalVal);
      if (diff > 0.05) {
        newIssues.push({
          field: 'grand_total',
          code: 'TOTAL_MISMATCH',
          message: `Sum mismatch: Subtotal ($${subtotalVal.toFixed(2)}) + Tax ($${taxVal.toFixed(2)}) = $${expected.toFixed(2)}, but Grand Total is $${grandTotalVal.toFixed(2)}.`
        });
      }
    }

    // Remove missing field issues for fields that now have values
    newIssues = newIssues.filter(iss => {
      if (iss.code && iss.code.includes('MISSING') && iss.field) {
        const val = getVal(iss.field);
        return val === null || val === undefined;
      }
      return true;
    });

    validation.issues = newIssues;

    const hasHardErrors = newIssues.some(iss => iss.code && (iss.code.includes('MISMATCH') || iss.code.includes('INVALID')));
    const hasWarnings = newIssues.length > 0;

    if (hasHardErrors) {
      validation.overall_status = 'invalid';
      validation.passed = false;
    } else if (hasWarnings) {
      validation.overall_status = 'needs_review';
      validation.passed = true;
    } else {
      validation.overall_status = 'valid';
      validation.passed = true;
    }

    state.extractionResult.validation = validation;
  }

  function formatFieldValue(fieldKey, val) {
    if (val === null || val === undefined || val === '') return '';
    if (typeof val === 'number') {
      const isMoney = ['subtotal', 'tax', 'grand_total', 'total'].some(k => fieldKey.toLowerCase().includes(k));
      if (isMoney) {
        return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      }
      return String(val);
    }
    return String(val);
  }

  function renderStatusBadge(status, isOcrFailure, isMissing, isUserCorrected) {
    const badge = document.createElement('span');
    const normalized = (status || 'extracted').toLowerCase();

    let icon = 'check';
    let text = 'Extracted';
    let badgeClass = 'status-badge extracted';

    if (isMissing || normalized === 'missing') {
      icon = 'minus-circle';
      text = 'Absent';
      badgeClass = 'status-badge missing';
    } else if (isUserCorrected || normalized === 'user_corrected') {
      icon = 'user-check';
      text = 'Corrected';
      badgeClass = 'status-badge user_corrected';
    } else if (normalized === 'invalid' || normalized === 'failed') {
      icon = 'x-circle';
      text = 'Invalid';
      badgeClass = 'status-badge invalid';
    } else if (isOcrFailure) {
      icon = 'alert-triangle';
      text = 'Review (OCR)';
      badgeClass = 'status-badge needs_review';
    } else if (normalized === 'low_confidence') {
      icon = 'shield-alert';
      text = 'Low Conf';
      badgeClass = 'status-badge low_confidence';
    } else if (normalized === 'needs_review' || normalized === 'warning' || normalized === 'review') {
      icon = 'alert-triangle';
      text = 'Review';
      badgeClass = 'status-badge needs_review';
    } else {
      icon = 'check';
      text = 'Extracted';
      badgeClass = 'status-badge extracted';
    }

    badge.className = badgeClass;
    badge.innerHTML = `<i data-lucide="${icon}"></i><span>${escapeHtml(text)}</span>`;
    return badge;
  }

  function renderConfidenceStatus(score, status, isMissing, isUserCorrected) {
    const wrap = document.createElement('div');
    wrap.className = 'confidence-wrapper';

    if (isMissing || status === 'missing' || score === null || score === undefined) {
      const unavail = document.createElement('span');
      unavail.className = 'confidence-text unavailable';
      unavail.textContent = isMissing ? 'Absent' : 'Unavailable';
      wrap.appendChild(unavail);
      return wrap;
    }

    if (isUserCorrected || status === 'user_corrected') {
      const barBg = document.createElement('div');
      barBg.className = 'confidence-bar-bg';
      const barFill = document.createElement('div');
      barFill.className = 'confidence-bar-fill high';
      barFill.style.width = '100%';
      barBg.appendChild(barFill);

      const text = document.createElement('span');
      text.className = 'confidence-text';
      text.style.color = '#1D4ED8';
      text.textContent = '100%';

      wrap.appendChild(barBg);
      wrap.appendChild(text);
      return wrap;
    }

    if (typeof score !== 'number' || isNaN(score) || score < 0 || score > 1) {
      const unavail = document.createElement('span');
      unavail.className = 'confidence-text unavailable';
      unavail.textContent = 'Unavailable';
      wrap.appendChild(unavail);
      return wrap;
    }

    const percentage = Math.round(score * 100);
    let level = 'high';
    if (percentage < 70) level = 'low';
    else if (percentage < (CONFIG.LOW_CONFIDENCE_THRESHOLD * 100)) level = 'medium';

    const barBg = document.createElement('div');
    barBg.className = 'confidence-bar-bg';

    const barFill = document.createElement('div');
    barFill.className = `confidence-bar-fill ${level}`;
    barFill.style.width = `${percentage}%`;

    barBg.appendChild(barFill);

    const text = document.createElement('span');
    text.className = 'confidence-text';
    text.textContent = `${percentage}%`;

    wrap.appendChild(barBg);
    wrap.appendChild(text);

    return wrap;
  }

  function deriveFieldStatus(value, confidence) {
    if (value === null || value === undefined || value === '') {
      return 'missing';
    }
    if (typeof confidence === 'number' && confidence < CONFIG.LOW_CONFIDENCE_THRESHOLD) {
      return 'low_confidence';
    }
    return 'extracted';
  }

  // ==========================================================================
  // 10. VALIDATION SUMMARY PANEL
  // ==========================================================================
  function renderValidationSummary(data) {
    const validation = data.validation || {};
    const fieldsObj = data.fields || {};

    const issues = Array.isArray(validation.issues) ? validation.issues : [];
    const legacyWarnings = Array.isArray(validation.warnings) ? validation.warnings : [];

    let totalFields = Object.keys(fieldsObj).length;
    let missingFields = 0;
    let lowConfFields = 0;
    let invalidFields = 0;
    let userCorrectedFields = 0;

    Object.values(fieldsObj).forEach(f => {
      const val = typeof f === 'object' && f !== null ? f.value : f;
      const conf = typeof f === 'object' && f !== null ? f.confidence : null;
      const st = typeof f === 'object' && f !== null ? f.status : null;
      if (val === null || val === undefined || val === '' || st === 'missing') missingFields++;
      if (st === 'low_confidence' || (typeof conf === 'number' && conf < CONFIG.LOW_CONFIDENCE_THRESHOLD && val !== null)) lowConfFields++;
      if (st === 'invalid') invalidFields++;
      if (st === 'user_corrected') userCorrectedFields++;
    });

    const errorIssues = issues.filter(iss => iss.code && (iss.code.includes('MISMATCH') || iss.code.includes('INVALID')));
    const warningIssues = issues.filter(iss => !iss.code || (!iss.code.includes('MISMATCH') && !iss.code.includes('INVALID')));

    const totalProblems = errorIssues.length + warningIssues.length + invalidFields;
    const passedChecks = Math.max(0, totalFields - missingFields - lowConfFields - totalProblems + userCorrectedFields);
    const reviewRequired = lowConfFields + invalidFields + issues.length + legacyWarnings.length;

    if (elements.valTotalFields) elements.valTotalFields.textContent = totalFields;
    if (elements.valPassedChecks) elements.valPassedChecks.textContent = passedChecks;
    if (elements.valLowConfFields) elements.valLowConfFields.textContent = lowConfFields;
    if (elements.valMissingFields) elements.valMissingFields.textContent = missingFields;
    if (elements.valReviewRequired) elements.valReviewRequired.textContent = reviewRequired;

    // Render Warnings / Issues List
    if (!elements.validationWarningsList) return;
    elements.validationWarningsList.innerHTML = '';

    const isDocumentValid = validation.overall_status === 'valid' && errorIssues.length === 0;

    if (isDocumentValid && issues.length === 0 && legacyWarnings.length === 0) {
      const goodItem = document.createElement('div');
      goodItem.className = 'warning-item green';
      goodItem.innerHTML = `
        <i data-lucide="check-circle-2"></i>
        <span><strong>All business validation rules passed.</strong> Extracted vendor, dates, and arithmetic totals verified with zero discrepancies.</span>
      `;
      elements.validationWarningsList.appendChild(goodItem);
      refreshIcons();
      return;
    }

    // Critical Error Issues
    errorIssues.forEach(issue => {
      const item = document.createElement('div');
      item.className = 'warning-item red';
      const fieldNotice = issue.field ? ` <span style="font-family: var(--font-mono); font-size: 0.75rem; background: rgba(0,0,0,0.06); padding: 2px 6px; border-radius: 4px;">[${escapeHtml(issue.field)}]</span>` : '';
      const codeNotice = issue.code ? `<strong>${escapeHtml(issue.code)}:</strong> ` : '';
      item.innerHTML = `
        <i data-lucide="alert-octagon"></i>
        <div>${codeNotice}${escapeHtml(issue.message)}${fieldNotice}</div>
      `;
      elements.validationWarningsList.appendChild(item);
    });

    // Warning / Adjustment Issues
    warningIssues.forEach(issue => {
      const item = document.createElement('div');
      item.className = 'warning-item amber';
      const fieldNotice = issue.field ? ` <span style="font-family: var(--font-mono); font-size: 0.75rem; background: rgba(0,0,0,0.06); padding: 2px 6px; border-radius: 4px;">[${escapeHtml(issue.field)}]</span>` : '';
      const codeNotice = issue.code ? `<strong>${escapeHtml(issue.code)}:</strong> ` : '';
      item.innerHTML = `
        <i data-lucide="alert-triangle"></i>
        <div>${codeNotice}${escapeHtml(issue.message)}${fieldNotice}</div>
      `;
      elements.validationWarningsList.appendChild(item);
    });

    // Legacy Warnings
    legacyWarnings.forEach(warnText => {
      const item = document.createElement('div');
      const isMismatch = warnText.toLowerCase().includes('mismatch');
      item.className = isMismatch ? 'warning-item red' : 'warning-item amber';
      const iconName = isMismatch ? 'alert-octagon' : 'alert-triangle';
      item.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <div>${escapeHtml(warnText)}</div>
      `;
      elements.validationWarningsList.appendChild(item);
    });

    // Informational note for absent fields - distinct from errors!
    if (missingFields > 0) {
      const item = document.createElement('div');
      item.className = 'warning-item info';
      item.innerHTML = `
        <i data-lucide="info"></i>
        <div><strong>${missingFields} expected field(s) absent:</strong> Document layout does not contain all standard fields. Use the "Add" button to supply manual values if needed.</div>
      `;
      elements.validationWarningsList.appendChild(item);
    }

    // Low confidence notification
    if (lowConfFields > 0) {
      const item = document.createElement('div');
      item.className = 'warning-item amber';
      item.innerHTML = `
        <i data-lucide="shield-alert"></i>
        <div><strong>${lowConfFields} field(s) flagged for review:</strong> Confidence score is below threshold (${Math.round(CONFIG.LOW_CONFIDENCE_THRESHOLD * 100)}%).</div>
      `;
      elements.validationWarningsList.appendChild(item);
    }

    refreshIcons();
  }

  function updateFilterButtonsUI(activeMode) {
    const filterBtns = {
      all: elements.btnFilterAll,
      review: elements.btnFilterReview,
      missing: elements.btnFilterMissing,
      invalid: elements.btnFilterInvalid
    };
    Object.entries(filterBtns).forEach(([mode, btn]) => {
      if (!btn) return;
      if (mode === activeMode) {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
      } else {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
      }
    });
  }

  function filterResultsTable(mode) {
    if (mode && mode !== 'search') {
      state.currentFilterMode = mode;
      updateFilterButtonsUI(mode);
    }

    const currentMode = state.currentFilterMode || 'all';
    const query = elements.resultsSearchInput ? elements.resultsSearchInput.value.toLowerCase().trim() : '';
    const rows = elements.resultsTableBody ? elements.resultsTableBody.querySelectorAll('tr[data-field-name]') : [];

    rows.forEach(row => {
      const fieldName = row.getAttribute('data-field-name') || '';
      const text = row.textContent.toLowerCase();
      const status = row.getAttribute('data-status') || '';
      const requiresReview = row.getAttribute('data-requires-review') === 'true';

      const matchesSearch = !query || text.includes(query) || fieldName.includes(query);

      let matchesFilter = true;
      if (currentMode === 'review') {
        matchesFilter = requiresReview;
      } else if (currentMode === 'missing') {
        matchesFilter = (status === 'missing');
      } else if (currentMode === 'invalid') {
        matchesFilter = (status === 'invalid');
      }

      row.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    });
  }

  function filterReviewOnly() {
    filterResultsTable('review');
    showToast('Showing fields requiring review', 'info');
  }

  // ==========================================================================
  // 11. CSV & JSON EXPORT ENGINES
  // ==========================================================================
  async function downloadCSV() {
    if (!state.extractionResult) {
      showToast('No extraction results available to export.', 'warning');
      return;
    }

    const docId = state.extractionResult.document_id || 'documind_document';
    const filename = `documind_export_${docId}_${Date.now()}.csv`;

    // Attempt backend export endpoint first if available
    if (!state.mockMode) {
      try {
        const exportUrl = `${state.apiBaseUrl.replace(/\/+$/, '')}/export/csv`;
        const response = await fetch(exportUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(state.extractionResult)
        });

        if (response.ok) {
          const blob = await response.blob();
          triggerDownload(blob, filename);
          showToast('CSV downloaded from backend endpoint', 'success');
          return;
        }
      } catch (err) {
        // Fallback to client generator
      }
    }

    // Client-side RFC-4180 CSV Generation Fallback
    const csvContent = generateClientCSV(state.extractionResult);
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    triggerDownload(blob, filename);
    showToast('CSV exported successfully!', 'success');
  }

  function generateClientCSV(data) {
    const headers = ['document_id', 'document_type', 'field_name', 'value', 'confidence', 'status', 'validation_message'];
    const rows = [headers.join(',')];

    const docId = data.document_id || 'N/A';
    const docType = data.document_type || 'invoice';
    const fields = data.fields || {};

    Object.keys(fields).forEach(key => {
      const f = fields[key];
      const isObj = typeof f === 'object' && f !== null;
      const value = isObj ? (f.value !== null && f.value !== undefined ? String(f.value) : '') : String(f || '');
      const confidence = isObj && typeof f.confidence === 'number' ? `${Math.round(f.confidence * 100)}%` : 'Unavailable';
      const status = isObj && f.status ? f.status : (value === '' ? 'missing' : 'extracted');
      const valMsg = isObj && f.validation_message ? f.validation_message : '';

      const row = [
        escapeCsvCell(docId),
        escapeCsvCell(docType),
        escapeCsvCell(key),
        escapeCsvCell(value),
        escapeCsvCell(confidence),
        escapeCsvCell(status),
        escapeCsvCell(valMsg)
      ];
      rows.push(row.join(','));
    });

    return rows.join('\r\n');
  }

  function escapeCsvCell(cell) {
    const str = String(cell || '');
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }

  async function downloadJSON() {
    if (!state.extractionResult) {
      showToast('No extraction results available to export.', 'warning');
      return;
    }

    const docId = state.extractionResult.document_id || 'documind_document';
    const filename = `documind_export_${docId}_${Date.now()}.json`;

    // Attempt backend JSON export endpoint first if available
    if (!state.mockMode) {
      try {
        const exportUrl = `${state.apiBaseUrl.replace(/\/+$/, '')}/export/json`;
        const response = await fetch(exportUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(state.extractionResult)
        });

        if (response.ok) {
          const blob = await response.blob();
          triggerDownload(blob, filename);
          showToast('JSON downloaded from backend endpoint', 'success');
          return;
        }
      } catch (err) {
        // Fallback to client generator
      }
    }

    // Client-side JSON export
    const jsonString = JSON.stringify(state.extractionResult, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8;' });
    triggerDownload(blob, filename);
    showToast('JSON exported successfully!', 'success');
  }

  function copyJSONToClipboard() {
    if (!state.extractionResult) return;
    const jsonString = JSON.stringify(state.extractionResult, null, 2);
    navigator.clipboard.writeText(jsonString).then(() => {
      showToast('Full JSON response copied to clipboard!', 'success');
    }).catch(() => {
      showToast('Failed to copy to clipboard', 'error');
    });
  }

  function triggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // ==========================================================================
  // 12. ACCURACY EVALUATION DASHBOARD & CHART.JS
  // ==========================================================================
  async function loadEvaluationReport(isSilent = false) {
    if (!isSilent) showToast('Fetching model evaluation benchmark...', 'info');

    // In Mock Mode, return illustrative sample data
    if (state.mockMode) {
      const mockEval = getMockEvaluationResponse();
      renderEvaluationDashboard(mockEval);
      if (elements.evalLastUpdated) {
        elements.evalLastUpdated.textContent = `Last checked: ${new Date().toLocaleTimeString()} (Mock)`;
      }
      return;
    }

    // Live Mode: Fetch from GET /api/evaluation
    const evalUrl = `${state.apiBaseUrl.replace(/\/+$/, '')}${CONFIG.EVALUATION_ENDPOINT}`;

    try {
      const response = await fetch(evalUrl, { method: 'GET' });
      if (!response.ok) {
        throw new Error(`Endpoint returned HTTP ${response.status}`);
      }

      const evalData = await response.json();
      
      // Check if report is explicitly marked unavailable by backend
      if (evalData.status === 'unavailable') {
        showEvaluationUnavailable(evalData.message || 'Evaluation report has not been generated yet.');
        return;
      }

      // Normalize field accuracy: Map FastAPI field_metrics dictionary or legacy field_accuracy array
      let fieldAccuracy = [];
      if (evalData.field_metrics && typeof evalData.field_metrics === 'object') {
        fieldAccuracy = Object.entries(evalData.field_metrics).map(([field, metrics]) => ({
          field: field,
          correct: metrics.correct_count ?? 0,
          total: metrics.evaluated_count ?? 0,
          missing: metrics.missing_count ?? 0,
          accuracy: metrics.accuracy_percentage ?? 0
        }));
      } else if (Array.isArray(evalData.field_accuracy)) {
        fieldAccuracy = evalData.field_accuracy;
      }

      if (fieldAccuracy.length === 0) {
        throw new Error('Evaluation data empty or incomplete.');
      }

      evalData.normalized_field_accuracy = fieldAccuracy;
      state.evaluationData = evalData;
      renderEvaluationDashboard(evalData);

      if (elements.evalLastUpdated) {
        if (evalData.evaluated_at) {
          elements.evalLastUpdated.textContent = `Evaluated: ${new Date(evalData.evaluated_at).toLocaleString()}`;
        } else {
          elements.evalLastUpdated.textContent = `Last checked: ${new Date().toLocaleTimeString()}`;
        }
      }

      if (!isSilent) showToast('Evaluation report loaded successfully!', 'success');

    } catch (err) {
      console.warn('Evaluation report unavailable:', err.message);
      showEvaluationUnavailable(err.message);
      if (!isSilent) showToast('Evaluation report is not available yet.', 'warning');
    }
  }

  function renderEvaluationDashboard(data) {
    if (elements.evalUnavailableBanner) elements.evalUnavailableBanner.style.display = 'none';
    if (elements.evaluationGrid) elements.evaluationGrid.style.display = 'grid';

    const docsEvaluated = data.total_documents || data.documents_evaluated || 30;
    const fieldAccuracy = data.normalized_field_accuracy || data.field_accuracy || [];

    // Calculate metrics
    let totalCorrect = 0;
    let totalEvaluated = 0;
    let reviewCount = 0;

    fieldAccuracy.forEach(item => {
      totalCorrect += item.correct || 0;
      totalEvaluated += item.total || 0;
      const acc = item.accuracy !== undefined ? item.accuracy : (item.total > 0 ? (item.correct / item.total) * 100 : 0);
      if (acc < 90) reviewCount++;
    });

    const overallAcc = (typeof data.overall_accuracy_percentage === 'number')
      ? data.overall_accuracy_percentage.toFixed(2)
      : (totalEvaluated > 0 ? ((totalCorrect / totalEvaluated) * 100).toFixed(2) : '0.00');

    if (elements.evalDocsCount) elements.evalDocsCount.textContent = docsEvaluated;
    if (elements.evalOverallAccuracy) elements.evalOverallAccuracy.textContent = `${overallAcc}%`;
    if (elements.evalTotalFieldsCount) elements.evalTotalFieldsCount.textContent = totalEvaluated;
    if (elements.evalReviewFieldsCount) elements.evalReviewFieldsCount.textContent = reviewCount;

    // Render Table
    renderEvaluationTable(fieldAccuracy);

    // Render Chart.js
    renderAccuracyChart(fieldAccuracy);
  }

  function renderEvaluationTable(fieldAccuracy) {
    if (!elements.evaluationTableBody) return;
    elements.evaluationTableBody.innerHTML = '';

    fieldAccuracy.forEach(item => {
      const tr = document.createElement('tr');
      const acc = item.accuracy !== undefined ? Number(item.accuracy).toFixed(2) : ((item.correct / item.total) * 100).toFixed(2);
      
      const badgeClass = acc >= 90 ? 'status-badge verified' : (acc >= 75 ? 'status-badge warning' : 'status-badge failed');

      tr.innerHTML = `
        <td style="font-weight: 600;">
          ${escapeHtml(formatFieldLabel(item.field))}
          <span style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-tertiary); display: block;">${escapeHtml(item.field)}</span>
        </td>
        <td style="font-family: var(--font-mono);">${item.correct}</td>
        <td style="font-family: var(--font-mono);">${item.total}</td>
        <td>
          <span class="${badgeClass}">${acc}%</span>
        </td>
      `;
      elements.evaluationTableBody.appendChild(tr);
    });
  }

  function renderAccuracyChart(fieldAccuracy) {
    if (!elements.accuracyChartCanvas || !window.Chart) return;

    const labels = fieldAccuracy.map(item => formatFieldLabel(item.field));
    const dataValues = fieldAccuracy.map(item => item.accuracy !== undefined ? item.accuracy : Math.round((item.correct / item.total) * 100));

    // Dynamic background colors according to accuracy benchmarks
    const backgroundColors = dataValues.map(val => {
      if (val >= 90) return 'rgba(22, 163, 74, 0.85)'; // Green
      if (val >= 80) return 'rgba(37, 99, 235, 0.85)'; // Blue
      if (val >= 70) return 'rgba(217, 119, 6, 0.85)'; // Amber
      return 'rgba(220, 38, 38, 0.85)'; // Red
    });

    const borderColors = dataValues.map(val => {
      if (val >= 90) return '#16A34A';
      if (val >= 80) return '#2563EB';
      if (val >= 70) return '#D97706';
      return '#DC2626';
    });

    // Destroy previous instance if exists
    if (state.chartInstance) {
      state.chartInstance.destroy();
      state.chartInstance = null;
    }

    const ctx = elements.accuracyChartCanvas.getContext('2d');
    state.chartInstance = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Extraction Accuracy (%)',
          data: dataValues,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 45
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `Accuracy: ${context.parsed.y}%`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              stepSize: 20,
              callback: function (val) { return val + '%'; },
              font: { family: 'Inter', size: 11 }
            },
            grid: { color: '#E2E8F0' }
          },
          x: {
            ticks: {
              font: { family: 'Inter', size: 11, weight: '500' }
            },
            grid: { display: false }
          }
        }
      }
    });
  }

  function showEvaluationUnavailable(reason = '') {
    if (elements.evalUnavailableBanner) elements.evalUnavailableBanner.style.display = 'flex';
    if (elements.evaluationGrid) elements.evaluationGrid.style.display = 'none';

    if (elements.evalDocsCount) elements.evalDocsCount.textContent = '-';
    if (elements.evalOverallAccuracy) elements.evalOverallAccuracy.textContent = '-';
    if (elements.evalTotalFieldsCount) elements.evalTotalFieldsCount.textContent = '-';
    if (elements.evalReviewFieldsCount) elements.evalReviewFieldsCount.textContent = '-';

    if (elements.evaluationTableBody) {
      elements.evaluationTableBody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align: center; padding: 24px; color: var(--text-tertiary);">
            Evaluation report is not available yet.
          </td>
        </tr>
      `;
    }

    if (state.chartInstance) {
      state.chartInstance.destroy();
      state.chartInstance = null;
    }
  }

  // ==========================================================================
  // 13. MODAL & LIGHTBOX FOR IMAGE ZOOM
  // ==========================================================================
  function openZoomModal() {
    if (!state.currentPreviewUrl) return;
    if (elements.zoomModalImage) elements.zoomModalImage.src = state.currentPreviewUrl;
    if (elements.zoomModalTitle && state.currentFile) {
      elements.zoomModalTitle.textContent = `Document Inspection: ${state.currentFile.name}`;
    }
    if (elements.imageZoomModal) elements.imageZoomModal.classList.add('open');
  }

  function closeZoomModal() {
    if (elements.imageZoomModal) elements.imageZoomModal.classList.remove('open');
  }

  // ==========================================================================
  // 14. TOAST NOTIFICATIONS & ERROR DISPLAY
  // ==========================================================================
  function showToast(message, type = 'info') {
    if (!elements.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'info';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'alert-circle';
    if (type === 'warning') icon = 'alert-triangle';

    toast.innerHTML = `
      <i data-lucide="${icon}" style="width: 16px; height: 16px; flex-shrink: 0;"></i>
      <span>${escapeHtml(message)}</span>
    `;

    elements.toastContainer.appendChild(toast);
    refreshIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 200ms ease';
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 200);
    }, 3800);
  }

  function displayError(message) {
    if (!elements.uploadErrorAlert || !elements.uploadErrorMessage) return;
    elements.uploadErrorMessage.textContent = message;
    elements.uploadErrorAlert.style.display = 'flex';
    refreshIcons();
  }

  function hideUploadError() {
    if (elements.uploadErrorAlert) {
      elements.uploadErrorAlert.style.display = 'none';
    }
  }

  function updateDashboardStatusKPI(statusText, descText, colorClass = 'primary', iconName = 'file-text') {
    if (elements.kpiDocStatus) elements.kpiDocStatus.textContent = statusText;
    if (elements.kpiDocStatusDesc) {
      elements.kpiDocStatusDesc.innerHTML = `
        <i data-lucide="${iconName}" style="width: 12px; height: 12px;"></i>
        <span>${escapeHtml(descText)}</span>
      `;
    }
    if (elements.kpiCardStatus) {
      elements.kpiCardStatus.className = `kpi-card status-${colorClass}`;
    }
    if (elements.kpiIconStatus) {
      elements.kpiIconStatus.setAttribute('data-lucide', iconName);
    }
    refreshIcons();
  }

  // ==========================================================================
  // 15. UTILITIES & FORMATTERS
  // ==========================================================================
  function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  function getFileExtension(filename) {
    if (!filename) return '';
    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  }

  function formatFieldLabel(key) {
    if (!key) return '';
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function generateDocId() {
    return 'DOC-' + Math.random().toString(36).substring(2, 8).toUpperCase();
  }

  // ==========================================================================
  // 16. MOCK DEMO RESPONSES (Isolated & Clearly Labeled)
  // ==========================================================================
  function getMockExtractionResponse(filename) {
    return {
      document_id: 'INV-2026-MOCK',
      filename: filename || 'inv_01_techcorp.pdf',
      document_type: 'invoice',
      fields: {
        vendor_name: {
          value: 'TechCorp Solutions Inc',
          confidence: 0.98,
          status: 'extracted'
        },
        invoice_number: {
          value: 'TC-2026-881',
          confidence: 0.99,
          status: 'extracted'
        },
        invoice_date: {
          value: '2026-05-14',
          confidence: 0.97,
          status: 'extracted'
        },
        subtotal: {
          value: 1250.00,
          confidence: 0.99,
          status: 'extracted'
        },
        tax: {
          value: 125.00,
          confidence: 0.96,
          status: 'extracted'
        },
        grand_total: {
          value: 1375.00,
          confidence: 0.99,
          status: 'extracted'
        }
      },
      validation: {
        overall_status: 'valid',
        issues: []
      },
      metadata: {
        ocr_applied: false,
        text_length: 500,
        source_format: 'pdf'
      }
    };
  }

  function getMockEvaluationResponse() {
    return {
      status: 'completed',
      total_documents: 32,
      successfully_processed: 32,
      failed_processing: 0,
      overall_accuracy_percentage: 100.0,
      field_metrics: {
        vendor_name: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 },
        invoice_number: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 },
        invoice_date: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 },
        subtotal: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 },
        tax: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 },
        grand_total: { evaluated_count: 32, correct_count: 32, missing_count: 0, accuracy_percentage: 100.0 }
      },
      normalization_rules: {
        dates: 'Normalized to ISO YYYY-MM-DD',
        monetary: 'Parsed to numeric float with 2 decimal places'
      },
      evaluated_at: new Date().toISOString()
    };
  }

  // ==========================================================================
  // 17. APP ENTRY POINT
  // ==========================================================================
  document.addEventListener('DOMContentLoaded', initializeApp);

})();
