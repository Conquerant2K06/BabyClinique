// Optionnel : Afficher des informations supplémentaires selon le mode de paiement
document.getElementById('payment_method').addEventListener('change', function() {
    const paymentInfo = document.getElementById('payment-info');
    if (paymentInfo) paymentInfo.remove();
    
    const selectedValue = this.value;
    let infoText = '';
    
    switch(selectedValue) {
        case 'mobile_money':
            infoText = 'Vous recevrez les instructions de paiement Mobile Money après confirmation.';
            break;
        case 'bank_transfer':
            infoText = 'Les détails du compte bancaire vous seront envoyés par email.';
            break;
        case 'cash_on_delivery':
            infoText = 'Vous paierez en espèces à la livraison.';
            break;
        case 'credit_card':
            infoText = 'Vous serez redirigé vers la page de paiement sécurisé.';
            break;
    }
    
    if (infoText) {
        const infoDiv = document.createElement('div');
        infoDiv.id = 'payment-info';
        infoDiv.className = 'alert alert-info mt-2';
        infoDiv.innerHTML = '<i class="fas fa-info-circle"></i> ' + infoText;
        this.parentNode.appendChild(infoDiv);
    }
});
