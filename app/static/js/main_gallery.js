document.addEventListener('DOMContentLoaded', () => {
    const galleryContainer = document.getElementById('gallery-container');
    const galleryImage = document.getElementById('gallery-image');
    const prevButton = document.getElementById('prev-button');
    const nextButton = document.getElementById('next-button');
    
    let images = [];
    let currentIndex = 0;

    // Fonction pour obtenir les images de la galerie depuis le serveur
    async function loadGalleryImages() {
        try {
            const modelId = localStorage.getItem('modelId');
            if (!modelId) {
                throw new Error('Aucun ID de modèle trouvé dans le localStorage');
            }
            const response = await fetch(`/api/gallery-images/${modelId}`);
            if (!response.ok) {
                throw new Error('Erreur de chargement des images de la galerie');
            }
            
            // Recevoir les données des images
            const imageDataList = await response.json();
            images = imageDataList.map(data => data.data);
            
            // Afficher la première image si disponible
            if (images.length > 0) {
                galleryImage.src = images[currentIndex];
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    // Fonction pour mettre à jour l'image affichée
    function updateImage() {
        if (images.length > 0) {
            galleryImage.src = images[currentIndex];
        }
    }

    // Événements pour les boutons de navigation
    prevButton.addEventListener('click', function() {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        updateImage();
    });

    nextButton.addEventListener('click', function() {
        currentIndex = (currentIndex + 1) % images.length;
        updateImage();
    });

    // Charger les images lorsque la page est prête
    loadGalleryImages();
});
