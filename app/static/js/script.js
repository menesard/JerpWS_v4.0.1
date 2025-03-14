/**
 * Ana JavaScript dosyası
 */

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    // Otomatik kapanan uyarılar
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // 5 saniye sonra kapat
    });

    // Ağırlık göstergesini güncelleme (dashboard ve operations sayfalarında)
    const weightDisplay = document.getElementById('weight-display');
    if (weightDisplay) {
        // Her sayfa kendi ağırlık yenileme kodunu içerir
    }

    // Yazdırma fonksiyonu
    const printButtons = document.querySelectorAll('[data-action="print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Form doğrulama
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Tooltip'ler
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
});

/**
 * Tarih formatını düzenler
 * @param {Date} date - Formatlanacak tarih
 * @returns {string} - Formatlanmış tarih
 */
function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${day}-${month}-${year} ${hours}:${minutes}`;
}

/**
 * Gram değerini formatlar
 * @param {number} value - Formatlanacak gram değeri
 * @returns {string} - Formatlanmış gram değeri
 */
function formatGram(value) {
    return parseFloat(value).toFixed(2);
}

/**
 * Terazi API'sinden ağırlık verisi alır
 * @returns {Promise} - Ağırlık verisi Promise'i
 */
async function fetchWeight() {
    try {
        const response = await fetch('/api/weight');
        if (!response.ok) {
            throw new Error('Ağırlık verisi alınamadı');
        }
        return await response.json();
    } catch (error) {
        console.error('Terazi verisi alınamadı:', error);
        return { weight: 0, is_valid: false };
    }
}