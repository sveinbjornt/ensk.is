document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const targetWord = urlParams.get('word');

  // If no word is specified, we don't fetch or highlight anything.
  if (!targetWord) return;

  const imgElement = document.getElementById('dictionary-page-image');
  if (!imgElement) return;

  const pageNum = imgElement.getAttribute('data-page');
  const container = document.getElementById('page-image-container');

  if (!pageNum || !container) return;

  fetch(`/api/grounding/${pageNum}`)
    .then(response => response.json())
    .then(data => {
      if (!data || data.length === 0) return;

      let found = false;

      data.forEach(item => {
        // Case-insensitive comparison
        if (item.word.toLowerCase() !== targetWord.toLowerCase()) return;

        found = true;
        // Data format: [ymin, xmin, ymax, xmax] normalized to 1000
        const [ymin, xmin, ymax, xmax] = item.bbox;

        const overlay = document.createElement('div');
        overlay.classList.add('grounding-box');
        
        // Calculate percentages with a slight padding (0.5%)
        const padding = 0.5;
        const top = ((ymin / 1000) * 100) - padding;
        const left = ((xmin / 1000) * 100) - padding;
        const height = (((ymax - ymin) / 1000) * 100) + (padding * 2);
        const width = (((xmax - xmin) / 1000) * 100) + (padding * 2);

        overlay.style.position = 'absolute';
        overlay.style.top = `${top}%`;
        overlay.style.left = `${left}%`;
        overlay.style.width = `${width}%`;
        overlay.style.height = `${height}%`;
        overlay.style.backgroundColor = 'rgba(255, 255, 0, 0.2)'; // Yellow transparent
        overlay.style.border = '1px solid rgba(255, 255, 0, 0.5)';
        overlay.style.pointerEvents = 'none'; // Click through to the image
        overlay.title = item.word;

        container.appendChild(overlay);
      });

      // Scroll to the first highlighted element if any were found
      if (found) {
        const firstBox = container.querySelector('.grounding-box');
        if (firstBox) {
            // Use setTimeout to ensure the DOM update has rendered before scrolling
            setTimeout(() => {
                firstBox.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            }, 100);
        }
      }
    })
    .catch(err => console.error('Error fetching grounding data:', err));
});