document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dropArea = document.querySelector('.drop-area');
    const loading = document.getElementById('loading');

    // Drag and drop handlers
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('hover');
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('hover');
    });

    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('hover');
        fileInput.files = e.dataTransfer.files;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        loading.style.display = 'flex';
        
        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }

            if (data.type === 'image') {
                showImageResult(data);
            } else if (data.type === 'video') {
                showVideoResult(data.results);
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during processing');
        } finally {
            loading.style.display = 'none';
        }
    });

    function showImageResult(data) {
        document.getElementById('imageResult').style.display = 'grid';
        document.getElementById('videoResult').style.display = 'none';
        document.getElementById('resultImage').src = data.path;
        document.getElementById('imageCaption').textContent = data.caption;
    }

    function showVideoResult(results) {
        document.getElementById('imageResult').style.display = 'none';
        document.getElementById('videoResult').style.display = 'block';
        const grid = document.getElementById('keyframesGrid');
        grid.innerHTML = '';

        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'keyframe-item';
            item.innerHTML = `
                <img src="${result.frame}" alt="Keyframe">
                <div class="keyframe-caption">${result.caption}</div>
            `;
            grid.appendChild(item);
        });
    }
});

document.getElementById("fileInput").addEventListener("change", function(event) {
    const file = event.target.files[0];
    const resultsContainer = document.getElementById("resultsContainer");
    const imageResult = document.getElementById("imageResult");
    const videoResult = document.getElementById("videoResult");
    const resultImage = document.getElementById("resultImage");
    const keyframesGrid = document.getElementById("keyframesGrid");

    if (file) {
        const fileType = file.type;
        const fileURL = URL.createObjectURL(file);
        
        if (fileType.startsWith("image")) {
            imageResult.style.display = "block";
            videoResult.style.display = "none";
            resultImage.src = fileURL;
        } else if (fileType.startsWith("video")) {
            imageResult.style.display = "none";
            videoResult.style.display = "block";
            
            keyframesGrid.innerHTML = `<video controls width="100%"><source src="${fileURL}" type="${fileType}"></video>`;
        }

        resultsContainer.style.display = "block";
    }
});