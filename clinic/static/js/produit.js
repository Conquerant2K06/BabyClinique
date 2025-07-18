document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const prescriptionFilter = document.getElementById('prescriptionFilter');
    const noPrescriptionFilter = document.getElementById('noPrescriptionFilter');
    const clearFilters = document.getElementById('clearFilters');
    const gridView = document.getElementById('gridView');
    const listView = document.getElementById('listView');
    const resultCount = document.getElementById('resultCount');
    const noResults = document.getElementById('noResults');
    const medicationContainer = document.getElementById('medicationContainer');

    // Fonction de recherche
    function performSearch() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedCategory = categoryFilter.value;
        const needsPrescription = prescriptionFilter.checked;
        const noPrescription = noPrescriptionFilter.checked;
        
        const medicationItems = document.querySelectorAll('.medication-item');
        const categorySection = document.querySelectorAll('.category-section');
        let visibleCount = 0;
        
        // Cacher toutes les sections de catégorie d'abord
        categorySection.forEach(section => {
            section.classList.add('hidden');
        });
        
        medicationItems.forEach(item => {
            const name = item.dataset.name || '';
            const description = item.dataset.description || '';
            const category = item.dataset.category || '';
            const prescription = item.dataset.prescription === 'true';
            
            let isVisible = true;
            
            // Filtre par terme de recherche
            if (searchTerm && !name.includes(searchTerm) && !description.includes(searchTerm)) {
                isVisible = false;
            }
            
            // Filtre par catégorie
            if (selectedCategory && category !== selectedCategory) {
                isVisible = false;
            }
            
            // Filtre par ordonnance
            if (needsPrescription && !prescription) {
                isVisible = false;
            }
            
            if (noPrescription && prescription) {
                isVisible = false;
            }
            
            // Empêcher la sélection des deux filtres d'ordonnance
            if (needsPrescription && noPrescription) {
                isVisible = false;
            }
            
            if (isVisible) {
                item.classList.remove('hidden');
                visibleCount++;
                
                // Afficher la section de catégorie parente
                const parentSection = item.closest('.category-section');
                if (parentSection) {
                    parentSection.classList.remove('hidden');
                }
            } else {
                item.classList.add('hidden');
            }
        });
        
        // Mettre à jour le compteur de résultats
        resultCount.textContent = `${visibleCount} médicament${visibleCount !== 1 ? 's' : ''} trouvé${visibleCount !== 1 ? 's' : ''}`;
        
        // Afficher/cacher le message "Aucun résultat"
        if (visibleCount === 0) {
            noResults.style.display = 'block';
            medicationContainer.style.display = 'none';
        } else {
            noResults.style.display = 'none';
            medicationContainer.style.display = 'block';
        }
    }
    
    // Événements de recherche
    searchInput.addEventListener('input', performSearch);
    categoryFilter.addEventListener('change', performSearch);
    prescriptionFilter.addEventListener('change', function() {
        if (this.checked) {
            noPrescriptionFilter.checked = false;
        }
        performSearch();
    });
    noPrescriptionFilter.addEventListener('change', function() {
        if (this.checked) {
            prescriptionFilter.checked = false;
        }
        performSearch();
    });
    
    // Effacer les filtres
    clearFilters.addEventListener('click', function() {
        searchInput.value = '';
        categoryFilter.value = '';
        prescriptionFilter.checked = false;
        noPrescriptionFilter.checked = false;
        performSearch();
    });
    
    // Basculer entre vue grille et liste
    gridView.addEventListener('click', function() {
        document.querySelectorAll('.medication-grid').forEach(grid => {
            grid.classList.remove('list-view');
        });
        gridView.classList.add('active');
        listView.classList.remove('active');
    });
    
    listView.addEventListener('click', function() {
        document.querySelectorAll('.medication-grid').forEach(grid => {
            grid.classList.add('list-view');
        });
        listView.classList.add('active');
        gridView.classList.remove('active');
    });
    
    // Recherche en temps réel avec délai
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 300);
    });
});
