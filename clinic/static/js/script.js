        // Fonction pour mettre à jour l'heure
        function updateTime() {
            const now = new Date();
            
            // Format simple (HH:MM:SS)
            const timeString = now.toLocaleTimeString('fr-FR');
            document.getElementById('current-time').textContent = timeString;
            document.getElementById('current-time-2').textContent = timeString;
            document.getElementById('current-time-3').textContent = timeString;
            
            // Format avec date complète
            const dateTimeString = now.toLocaleString('fr-FR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            document.getElementById('current-datetime').textContent = dateTimeString;
            
            // Vérifier si ouvert ou fermé
            const hour = now.getHours();
            const day = now.getDay(); // 0 = dimanche, 1 = lundi, etc.
            const statusElement = document.getElementById('status');
            
            if (day >= 1 && day <= 5 && hour >= 9 && hour < 21) {
                statusElement.textContent = 'OUVERT';
                statusElement.className = 'fw-bold text-success';
            } else {
                statusElement.textContent = 'FERMÉ';
                statusElement.className = 'fw-bold text-danger';
            }
        }
        
        // Mettre à jour immédiatement
        updateTime();
        
        // Mettre à jour toutes les secondes
        setInterval(updateTime, 1000);
        
        // Version alternative : mettre à jour seulement toutes les minutes
        // setInterval(updateTime, 60000);
    