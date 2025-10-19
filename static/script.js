document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const uploadForm = document.getElementById('uploadForm');
    const submitButton = document.getElementById('submitButton');
    const statusMessage = document.getElementById('statusMessage');
    const downloadLink = document.getElementById('downloadLink');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const dropZoneText = document.getElementById('dropZoneText');

    // --- Drag and Drop Logic ---
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault(); // Prevent default browser behavior
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // --- Click to Browse Logic ---
    dropZone.addEventListener('click', () => {
        fileInput.click(); // Trigger hidden file input
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    function handleFile(file) {
        if (file && file.name.toLowerCase().endsWith('.json')) {
            fileInput.files = createFileList(file); // Set file for form submission
            fileNameDisplay.textContent = `Selected: ${file.name}`;
            dropZoneText.textContent = 'File selected. Drop another to replace.';
            clearStatus();
        } else {
            fileInput.value = ''; // Clear input
            fileNameDisplay.textContent = '';
            dropZoneText.textContent = 'Drop JSON file here';
            showStatus('Error: Please select or drop a .json file.', 'error');
        }
    }

    // Helper to set FileList programmatically
    function createFileList(file) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      return dataTransfer.files;
    }


    // --- Form Submission Logic ---
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default page reload

        if (!fileInput.files || fileInput.files.length === 0) {
            showStatus('Error: No file selected.', 'error');
            return;
        }

        const formData = new FormData(uploadForm);
        clearStatus();
        showProgress('Processing...');
        submitButton.disabled = true;

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData,
                // No 'Content-Type' header needed for FormData; browser sets it
            });

            const result = await response.json(); // Always expect JSON back

            hideProgress();
            submitButton.disabled = false;

            if (response.ok) {
                showStatus(result.message, 'success');
                // Create and show download link
                downloadLink.href = `/download/${result.download_filename}`;
                downloadLink.textContent = `Download ${result.download_filename}`;
                downloadLink.style.display = 'block';
                 // Clear file input after successful processing
                fileInput.value = '';
                fileNameDisplay.textContent = '';
                dropZoneText.textContent = 'Drop JSON file here';

            } else {
                // Handle HTTP errors (like 400, 500) which also return JSON
                showStatus(`Error (${response.status}): ${result.detail || 'Processing failed.'}`, 'error');
                downloadLink.style.display = 'none';
            }

        } catch (error) {
            console.error('Fetch error:', error);
            hideProgress();
            submitButton.disabled = false;
            showStatus('An unexpected network or server error occurred. Check console for details.', 'error');
            downloadLink.style.display = 'none';
        }
    });

    // --- Status and Progress Bar Functions ---
    function showStatus(message, type = 'info') { // type can be 'info', 'success', 'error'
        statusMessage.textContent = message;
        statusMessage.className = type; // Use classes for styling
        statusMessage.style.display = 'block';
    }

    function clearStatus() {
        statusMessage.textContent = 'Waiting for input file...';
        statusMessage.className = 'info';
         // statusMessage.style.display = 'none'; // Hide instead of clearing if preferred
        downloadLink.style.display = 'none'; // Hide download link
    }

    function showProgress(text = 'Processing...') {
        progressBar.style.width = '100%'; // Simple indeterminate progress
        progressText.textContent = text;
        progressBarContainer.style.display = 'block';
        statusMessage.style.display = 'none'; // Hide normal status
        downloadLink.style.display = 'none';
    }

    function hideProgress() {
        progressBarContainer.style.display = 'none';
        progressBar.style.width = '0%';
        statusMessage.style.display = 'block'; // Show status area again
    }

    // Initial state
    clearStatus();
    hideProgress();

});