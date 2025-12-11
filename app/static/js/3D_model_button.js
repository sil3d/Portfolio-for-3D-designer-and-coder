// main_3D_model.js
document.addEventListener('DOMContentLoaded', () => {
    const modelId = window.location.pathname.split('/').pop(); // Récupère l'ID du modèle depuis l'URL
    fetch(`/api/model/${modelId}`)
        .then(response => response.json())
        .then(model => {
            if (model.error) {
                console.error('Model not found');
                return;
            }
            
            // Met à jour le nom du modèle et les compteurs
            document.getElementById('model-name').textContent = model.name;
            document.getElementById('like-count').textContent = model.like_count;
            document.getElementById('download-count').textContent = model.download_count;
            
            // Met à jour le lien de téléchargement
            const downloadButton = document.getElementById('download-button');
            downloadButton.href = `/download/${model.id}`;
        })
        .catch(error => console.error('Error fetching model details:', error));
});
