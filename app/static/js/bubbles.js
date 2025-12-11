document.addEventListener('mousemove', function(e) {
    var bubblesContainer = document.getElementById('bubbles');
    var bubble = document.createElement('div');
    bubble.classList.add('bubble');
    var size = Math.random() * 20 + 10; // Taille des bulles
    bubble.style.width = size + 'px';
    bubble.style.height = size + 'px';
    bubble.style.left = e.pageX - size / 2 + 'px';
    bubble.style.top = e.pageY - size / 2 + 'px';
    bubblesContainer.appendChild(bubble);
    
    // Retirer la bulle après l'animation
    bubble.addEventListener('animationend', function() {
        bubblesContainer.removeChild(bubble);
    });
});
