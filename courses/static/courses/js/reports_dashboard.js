document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const classSearch = document.getElementById('classSearch');
    const sessionFilter = document.getElementById('sessionFilter');
    const sortBy = document.getElementById('sortBy');
    const classesContainer = document.getElementById('classesContainer');
    const classItems = document.querySelectorAll('.class-item');

    function filterAndSortClasses() {
        const searchTerm = classSearch.value.toLowerCase();
        const sessionFilterValue = sessionFilter.value;
        const sortValue = sortBy.value;

        let visibleItems = [];

        classItems.forEach(item => {
            const className = item.getAttribute('data-class-name');
            const sessionsCount = parseInt(item.getAttribute('data-sessions-count'));
            const startDate = parseInt(item.getAttribute('data-start-date'));
            
            // Search filter
            const matchesSearch = className.includes(searchTerm);
            
            // Session filter
            let matchesSession = true;
            if (sessionFilterValue === 'with-sessions') {
                matchesSession = sessionsCount > 0;
            } else if (sessionFilterValue === 'no-sessions') {
                matchesSession = sessionsCount === 0;
            }
            
            if (matchesSearch && matchesSession) {
                item.style.display = 'block';
                visibleItems.push({item, sessionsCount, startDate, className});
            } else {
                item.style.display = 'none';
            }
        });

        // Sort functionality
        visibleItems.sort((a, b) => {
            switch(sortValue) {
                case 'newest':
                    return b.startDate - a.startDate;
                case 'oldest':
                    return a.startDate - b.startDate;
                case 'name':
                    return a.className.localeCompare(b.className);
                case 'sessions':
                    return b.sessionsCount - a.sessionsCount;
                default:
                    return 0;
            }
        });

        // Reorder DOM
        visibleItems.forEach(({item}) => {
            classesContainer.appendChild(item);
        });
    }

    // Event listeners
    if (classSearch) {
        classSearch.addEventListener('input', filterAndSortClasses);
    }
    if (sessionFilter) {
        sessionFilter.addEventListener('change', filterAndSortClasses);
    }
    if (sortBy) {
        sortBy.addEventListener('change', filterAndSortClasses);
    }

    // Auto-collapse other sessions when one is opened
    document.querySelectorAll('.toggle-sessions').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-bs-target');
            document.querySelectorAll('.collapse').forEach(collapse => {
                if (collapse.id !== targetId.replace('#', '')) {
                    const collapseInstance = bootstrap.Collapse.getInstance(collapse);
                    if (collapseInstance) {
                        collapseInstance.hide();
                    }
                }
            });
        });
    });

    // Initialize filter on page load
    filterAndSortClasses();
});