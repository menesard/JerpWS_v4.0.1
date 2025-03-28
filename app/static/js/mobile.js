/**
 * Kuyumcu Takip Sistemi - Mobil Uyumlu JavaScript
 *
 * Bu dosya, mobil cihazlar için geliştirilmiş kullanıcı deneyimi
 * özelliklerini içerir.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobil menü modalını bağla
    const mobileMenuMore = document.getElementById('mobileMenuMore');
    if (mobileMenuMore) {
        const mobileMenuModal = new bootstrap.Modal(document.getElementById('mobileMenuModal'));
        mobileMenuMore.addEventListener('click', function (e) {
            e.preventDefault();
            mobileMenuModal.show();
        });
    }

    // Mobil cihazlarda tablo veri etiketlerini otomatik oluştur
    const prepareMobileTables = function () {
        document.querySelectorAll('.table-mobile').forEach(table => {
            const headerCells = table.querySelectorAll('thead th');
            const headerTexts = [];

            // Başlık metinlerini topla
            headerCells.forEach(th => {
                headerTexts.push(th.textContent.trim());
            });

            // Her satırın hücrelerine data-label özniteliği ekle
            table.querySelectorAll('tbody tr').forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    if (index < headerTexts.length) {
                        cell.setAttribute('data-label', headerTexts[index]);
                    }
                });
            });
        });
    };

    prepareMobileTables();

    // Kaydırma yönünü algılama
    let touchStartX = 0;
    let touchEndX = 0;

    const handleSwipe = function () {
        if (touchEndX < touchStartX - 100) {
            // Sağdan sola kaydırma (ileri)
            const activeTab = document.querySelector('.mobile-nav-item.active');
            if (activeTab && activeTab.nextElementSibling) {
                activeTab.nextElementSibling.click();
            }
        }

        if (touchEndX > touchStartX + 100) {
            // Soldan sağa kaydırma (geri)
            const activeTab = document.querySelector('.mobile-nav-item.active');
            if (activeTab && activeTab.previousElementSibling) {
                activeTab.previousElementSibling.click();
            }
        }
    };

    document.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    });

    document.addEventListener('touchend', function (e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });

    // Mobil cihazlar için tablo adaptasyonu
    const adaptTables = function () {
        const tables = document.querySelectorAll('table');
        if (window.innerWidth <= 768) {
            tables.forEach(table => {
                if (!table.classList.contains('table-mobile')) {
                    table.classList.add('table-mobile');
                    prepareMobileTables();
                }
            });
        } else {
            tables.forEach(table => {
                table.classList.remove('table-mobile');
            });
        }
    };

    adaptTables();
    window.addEventListener('resize', adaptTables);

    // Mobil için hızlı işlem butonları
    const createQuickActions = function () {
        // Mevcut sayfaya göre hızlı işlem butonları ekle
        const currentPath = window.location.pathname;

        // Eğer böyle bir element zaten varsa kaldır
        const existingActions = document.querySelector('.quick-actions');
        if (existingActions) {
            existingActions.remove();
        }

        // Hızlı işlem container'ı oluştur
        const quickActions = document.createElement('div');
        quickActions.className = 'quick-actions d-lg-none';

        // Genel sayfalar için hızlı işlemler
        if (currentPath.includes('/customers')) {
            // Müşteri sayfalarında yeni müşteri ekleme butonu
            const addCustomerBtn = document.createElement('a');
            addCustomerBtn.href = '/customers/add';
            addCustomerBtn.className = 'quick-action-btn btn btn-success';
            addCustomerBtn.innerHTML = '<i class="fas fa-user-plus"></i>';
            addCustomerBtn.title = 'Yeni Müşteri Ekle';

            quickActions.appendChild(addCustomerBtn);
        } else if (currentPath.includes('/dashboard') || currentPath === '/') {
            // Ana sayfada terazi sıfırlama butonu
            const tareBtn = document.createElement('a');
            tareBtn.href = '/tare_scale';
            tareBtn.className = 'quick-action-btn btn btn-primary';
            tareBtn.innerHTML = '<i class="fas fa-balance-scale"></i>';
            tareBtn.title = 'Teraziyi Sıfırla';

            quickActions.appendChild(tareBtn);
        }

        // Tüm sayfalarda kullanılabilecek genel işlem butonu
        const operationBtn = document.createElement('a');
        operationBtn.href = '/operations';
        operationBtn.className = 'quick-action-btn btn btn-info';
        operationBtn.innerHTML = '<i class="fas fa-exchange-alt"></i>';
        operationBtn.title = 'İşlem Yap';

        quickActions.appendChild(operationBtn);

        // Sayfaya ekle
        if (quickActions.children.length > 0) {
            document.body.appendChild(quickActions);
        }
    };

    createQuickActions();

    // Mobil cihazlarda tablo içeriğini optimize et
    const optimizeTableContent = function () {
        if (window.innerWidth <= 576) {
            document.querySelectorAll('table td').forEach(cell => {
                // Tüm hücrelerin içeriğinin tam görünmesini sağla
                cell.style.whiteSpace = 'normal';
                cell.style.wordBreak = 'break-word';
            });
        }
    };

    optimizeTableContent();
    window.addEventListener('resize', optimizeTableContent);

    // Form elemanlarını mobil için optimize et
    const optimizeFormElements = function () {
        // Input alanlarını daha dokunmatik dostu yap
        document.querySelectorAll('input, select, textarea').forEach(input => {
            input.classList.add('mobile-friendly');
        });

        // Sayı inputlarına artırma/azaltma butonları ekle
        document.querySelectorAll('input[type="number"]').forEach(input => {
            const wrapper = document.createElement('div');
            wrapper.className = 'mobile-number-input';

            const decreaseBtn = document.createElement('button');
            decreaseBtn.type = 'button';
            decreaseBtn.className = 'btn btn-outline-secondary btn-sm';
            decreaseBtn.innerHTML = '<i class="fas fa-minus"></i>';
            decreaseBtn.addEventListener('click', function () {
                const step = parseFloat(input.getAttribute('step') || 1);
                input.value = (parseFloat(input.value) - step) || 0;
                // Değişikliği tetikle
                input.dispatchEvent(new Event('input', {bubbles: true}));
            });

            const increaseBtn = document.createElement('button');
            increaseBtn.type = 'button';
            increaseBtn.className = 'btn btn-outline-secondary btn-sm';
            increaseBtn.innerHTML = '<i class="fas fa-plus"></i>';
            increaseBtn.addEventListener('click', function () {
                const step = parseFloat(input.getAttribute('step') || 1);
                input.value = (parseFloat(input.value) + step) || step;
                // Değişikliği tetikle
                input.dispatchEvent(new Event('input', {bubbles: true}));
            });

            // Sayfa yüklendiğinde elemanları yerleştirme
            if (window.innerWidth <= 768 && !input.closest('.input-group')?.querySelector('.mobile-number-buttons')) {
                if (input.closest('.input-group')) {
                    const buttonGroup = document.createElement('div');
                    buttonGroup.className = 'input-group-text mobile-number-buttons';
                    buttonGroup.appendChild(decreaseBtn);
                    buttonGroup.appendChild(increaseBtn);

                    input.closest('.input-group').appendChild(buttonGroup);
                }
            }
        });
    };

    // Sayfa yüklendiğinde ve pencere boyutu değiştiğinde optimize et
    optimizeFormElements();
    window.addEventListener('resize', optimizeFormElements);

    // Mobil uyumlu bir loading göstergesi ekle
    const createLoadingIndicator = function () {
        const loader = document.createElement('div');
        loader.className = 'mobile-loader';
        loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Yükleniyor...</span></div>';

        // Sayfaya ekle
        document.body.appendChild(loader);

        // Sayfa yüklendiğinde gizle
        window.addEventListener('load', function () {
            loader.style.display = 'none';
        });

        // Ajax istekleri sırasında göster
        document.addEventListener('ajaxStart', function () {
            loader.style.display = 'flex';
        });

        document.addEventListener('ajaxComplete', function () {
            loader.style.display = 'none';
        });
    };

    createLoadingIndicator();
});