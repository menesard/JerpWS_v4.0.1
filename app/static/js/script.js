/**
 * Kuyumcu Takip Sistemi - Ana JavaScript Dosyası
 * Güncellenen versiyon
 */

function getAuthToken() {
  return localStorage.getItem('jwt_token');
}

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

    // Tablolarda sıralama fonksiyonu
    const sortableTables = document.querySelectorAll('.table-sortable');
    sortableTables.forEach(table => {
        const headerCells = table.querySelectorAll('th');
        headerCells.forEach(th => {
            if (th.classList.contains('sortable')) {
                th.addEventListener('click', () => {
                    const tableBody = table.querySelector('tbody');
                    const rows = Array.from(tableBody.querySelectorAll('tr'));

                    // Sıralama sütunu indeksini al
                    const columnIndex = Array.from(th.parentNode.children).indexOf(th);

                    // Mevcut sıralama yönünü belirle
                    const isAscending = th.classList.contains('asc');

                    // Tüm başlıklardaki sıralama sınıflarını temizle
                    headerCells.forEach(cell => {
                        cell.classList.remove('asc', 'desc');
                    });

                    // Yeni sıralama yönünü belirle
                    th.classList.add(isAscending ? 'desc' : 'asc');

                    // Satırları sırala
                    rows.sort((a, b) => {
                        const aValue = a.children[columnIndex].textContent.trim();
                        const bValue = b.children[columnIndex].textContent.trim();

                        // Sayısal değerler için
                        if (!isNaN(parseFloat(aValue)) && !isNaN(parseFloat(bValue))) {
                            return isAscending
                                ? parseFloat(bValue) - parseFloat(aValue)
                                : parseFloat(aValue) - parseFloat(bValue);
                        }

                        // Metin değerleri için
                        return isAscending
                            ? bValue.localeCompare(aValue, 'tr')
                            : aValue.localeCompare(bValue, 'tr');
                    });

                    // DOM'u güncelle
                    rows.forEach(row => {
                        tableBody.appendChild(row);
                    });
                });

                // Sıralanabilir başlık olduğunu belirt
                th.classList.add('cursor-pointer');
                th.innerHTML += ' <i class="fas fa-sort text-muted ms-1"></i>';
            }
        });
    });

    // Arama filtreleme
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('input', () => {
            const searchTerm = input.value.trim().toLowerCase();
            const tableId = input.getAttribute('data-table');
            const table = document.getElementById(tableId);

            if (table) {
                const rows = table.querySelectorAll('tbody tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });

                // Sonuç sayısını göster
                const visibleRows = table.querySelectorAll('tbody tr[style=""]').length;
                const resultCount = table.querySelector('.search-result-count');

                if (resultCount) {
                    resultCount.textContent = `${visibleRows} sonuç bulundu`;
                }
            }
        });
    });

    // Tarih formatı kontrol ve düzeltme
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', () => {
            const dateValue = input.value;

            if (dateValue && !isValidDate(dateValue)) {
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });
    });

    // Dinamik input maskeleme
    const setupInputMasks = () => {
        // Telefon maskeleme
        document.querySelectorAll('input[type="tel"]').forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');

                if (value.length > 0) {
                    // Türkiye telefon numarası formatı: (5xx) xxx xx xx
                    if (value.length <= 3) {
                        value = `(${value}`;
                    } else if (value.length <= 6) {
                        value = `(${value.substring(0, 3)}) ${value.substring(3)}`;
                    } else if (value.length <= 8) {
                        value = `(${value.substring(0, 3)}) ${value.substring(3, 6)} ${value.substring(6)}`;
                    } else {
                        value = `(${value.substring(0, 3)}) ${value.substring(3, 6)} ${value.substring(6, 8)} ${value.substring(8, 10)}`;
                    }
                }

                e.target.value = value;
            });
        });

        // Para birimi formatı
        document.querySelectorAll('input[data-mask="currency"]').forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/[^\d.]/g, '');

                if (value) {
                    // Sayısal değeri formatla
                    const parts = value.split('.');
                    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');

                    if (parts.length > 1) {
                        // En fazla 2 ondalık basamak
                        parts[1] = parts[1].substring(0, 2);
                        value = parts.join('.');
                    }

                    e.target.value = '₺ ' + value;
                }
            });
        });
    };

    setupInputMasks();

    // Dinamik içerik yükleme için observer
    const setupDynamicContentObserver = () => {
        // DOM değişikliklerini izle
        const observer = new MutationObserver(mutations => {
            let contentChanged = false;

            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    contentChanged = true;
                }
            });

            if (contentChanged) {
                // Yeni eklenen içerik için maskeleme ve diğer işlevleri tekrar uygula
                setupInputMasks();

                // Mobile.js'den fonksiyonları çağır
                if (typeof prepareMobileTables === 'function') {
                    prepareMobileTables();
                }

                if (typeof optimizeFormElements === 'function') {
                    optimizeFormElements();
                }
            }
        });

        // Tüm DOM değişikliklerini izle
        observer.observe(document.body, { childList: true, subtree: true });
    };

    setupDynamicContentObserver();
});

/**
 * Tarih formatını düzenler
 * @param {Date} date - Formatlanacak tarih
 * @returns {string} - Formatlanmış tarih
 */
function formatDate(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }

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
 * Tarih formatının geçerli olup olmadığını kontrol eder
 * @param {string} dateString - Kontrol edilecek tarih
 * @returns {boolean} - Tarih geçerliyse true, değilse false
 */
function isValidDate(dateString) {
    const date = new Date(dateString);
    return !isNaN(date.getTime());
}

/**
 * Terazi API'sinden ağırlık verisi alır ve hata durumunda yeniden dener
 * @param {number} maxRetries - Maksimum yeniden deneme sayısı
 * @param {number} retryDelay - Yeniden denemeler arası bekleme süresi (ms)
 * @returns {Promise} - Ağırlık verisi Promise'i
 */
async function fetchWeight(maxRetries = 3, retryDelay = 1000) {
    let retries = 0;

    while (retries < maxRetries) {
        try {
            const response = await fetch('/api/weight');

            if (!response.ok) {
                throw new Error('Ağırlık verisi alınamadı');
            }

            return await response.json();
        } catch (error) {
            retries++;

            if (retries === maxRetries) {
                console.error('Terazi verisi alınamadı:', error);
                // Custom event tetikle
                document.dispatchEvent(new CustomEvent('weightFetchError', { detail: error }));
                return { weight: 0, is_valid: false };
            }

            // Yeniden denemeden önce bekle
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }
}

/**
 * Belirli bir aralıkla terazi verisini güncelleyen fonksiyon
 * @param {string} displayElementId - Ağırlık gösterge elementinin ID'si
 * @param {string} statusElementId - Durum gösterge elementinin ID'si
 * @param {number} interval - Güncelleme aralığı (ms)
 * @returns {number} - Interval ID
 */
function startWeightUpdater(displayElementId, statusElementId, interval = 500) {
    const updateWeight = async () => {
        try {
            const data = await fetchWeight();

            const displayElement = document.getElementById(displayElementId);
            const statusElement = document.getElementById(statusElementId);

            if (displayElement && data) {
                displayElement.textContent = data.weight.toFixed(2);

                // Ağırlık değişimi animasyonu
                displayElement.classList.add('weight-updated');
                setTimeout(() => {
                    displayElement.classList.remove('weight-updated');
                }, 300);
            }

            if (statusElement && data) {
                if (data.is_valid) {
                    statusElement.textContent = 'Geçerli Okuma';
                    statusElement.classList.remove('bg-warning');
                    statusElement.classList.add('bg-success');
                } else {
                    statusElement.textContent = 'Son Bilinen Değer';
                    statusElement.classList.remove('bg-success');
                    statusElement.classList.add('bg-warning');
                }
            }
        } catch (error) {
            console.error('Terazi güncelleme hatası:', error);
        }
    };

    // İlk güncelleme
    updateWeight();

    // Periyodik güncelleme
    return setInterval(updateWeight, interval);
}

/**
 * Terazi sıfırlama işlemi
 * @returns {Promise} - Sıfırlama sonucu Promise'i
 */
async function tareScale() {
    try {
        // JWT token'ı localStorage'dan al
        const token = localStorage.getItem('jwt_token');

        const response = await fetch('/api/tare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            }
        });

        if (!response.ok) {
            throw new Error('Terazi sıfırlama hatası');
        }

        const result = await response.json();

        // Başarılı işlem bildirimi
        if (result.message) {
            showNotification(result.message, 'success');
        }

        return result;
    } catch (error) {
        console.error('Terazi sıfırlama hatası:', error);
        showNotification('Terazi sıfırlanamadı', 'danger');
        return { error: error.message };
    }
}

/**
 * Bildirim gösterme fonksiyonu
 * @param {string} message - Bildirim metni
 * @param {string} type - Bildirim tipi (success, danger, warning, info)
 * @param {number} duration - Bildirim süresi (ms)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Bildirim container'ı oluştur veya mevcut olanı al
    let container = document.querySelector('.notification-container');

    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    // Bildirim elementi oluştur
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} fade-in`;

    // İkon ekle
    let icon = '';
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'danger':
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
            break;
    }

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-message">${message}</div>
        <button class="notification-close"><i class="fas fa-times"></i></button>
    `;

    // Container'a ekle
    container.appendChild(notification);

    // Kapatma butonunu etkinleştir
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.classList.add('fade-out');

        setTimeout(() => {
            notification.remove();
        }, 300);
    });

    // Belirli süre sonra otomatik kapat
    setTimeout(() => {
        notification.classList.add('fade-out');

        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

// API isteklerini işleme yardımcı fonksiyonu
async function apiRequest(url, method = 'GET', data = null, includeToken = true) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        // Token ekle
        if (includeToken) {
            const token = getAuthToken(); // Burada getAuthToken kullanılmalı
            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
        }

        // POST, PUT veya PATCH istekleri için veri ekle
        if (['POST', 'PUT', 'PATCH'].includes(method) && data) {
            options.body = JSON.stringify(data);
        }

        // Ajax başlangıç olayını tetikle
        document.dispatchEvent(new Event('ajaxStart'));

        const response = await fetch(url, options);

        // Ajax tamamlanma olayını tetikle
        document.dispatchEvent(new Event('ajaxComplete'));

        // Yetkilendirme hatası kontrolü
        if (response.status === 401) {
            // Oturum sonlandığında giriş sayfasına yönlendir
            window.location.href = "/login";
            return null;
        }

        return await response.json();
    } catch (error) {
        // Ajax hata olayını tetikle
        document.dispatchEvent(new Event('ajaxComplete'));
        console.error('API isteği hatası:', error);
        return { error: error.message };
    }
}