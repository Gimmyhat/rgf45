document.addEventListener('DOMContentLoaded', (event) => {
    // Получаем элементы форму загрузки файла
    const fileInput = document.querySelector('input[type="file"]');
    const uploadForm = document.querySelector('form');
    // Проверяем состояние процесса загрузки
    const isUploading = localStorage.getItem('isUploading');
    const historicalFilename = localStorage.getItem('historicalFilename');

    if (isUploading === 'true' && historicalFilename) {
        // Если процесс был активен, отображаем индикатор и продолжаем проверку статуса
        showLoadingIndicator();
        waitForCompletion(historicalFilename);
    }

    fileInput.addEventListener('change', async (event) => {
        if (fileInput.files.length > 0) {
            // Создаем объект FormData
            let formData = new FormData(uploadForm);
            // Сохраняем состояние в LocalStorage
            localStorage.setItem('isUploading', 'true');
            try {
                let response = await fetch(uploadForm.action, {
                    method: 'POST',
                    body: formData,
                });
                if (response.ok) {
                    let data = await response.json();
                    let historicalFilename = data.historical_filename;
                    if (historicalFilename) {
                        // Сохраняем имя файла в LocalStorage
                        localStorage.setItem('historicalFilename', historicalFilename);
                        waitForCompletion(historicalFilename);
                    }
                } else {
                    console.error("Ошибка HTTP: " + response.status);
                }
            } catch(error) {
                console.error("Ошибка при отправке файла:", error);
            }
        }
    });

    uploadForm.addEventListener('submit', async (event) => { // async добавлено здесь
        event.preventDefault();
        if (fileInput.files.length > 0) {
            uploadButton.classList.remove('upload-animate');
            // Создаем объект FormData
            let formData = new FormData(uploadForm);
            try {
                let response = await fetch(uploadForm.action, {
                    method: 'POST',
                    body: formData,
                });
                if (response.ok) {
                    let data = await response.json();
                    let historicalFilename = data.historical_filename;
                    if (historicalFilename) {
                        waitForCompletion(historicalFilename);
                    }
                } else {
                    console.error("Ошибка HTTP: " + response.status);
                }
            } catch(error) {
                console.error("Ошибка при отправке файла:", error);
            }
        }
    });
});

function showLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block'; // Показать индикатор
    }
}

function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none'; // Скрыть индикатор
    }
}

function waitForCompletion(historicalFilename) {
    showLoadingIndicator(); // Показать индикатор загрузки

    // Запрос на сервер для проверки статуса
    const checkStatusInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${encodeURIComponent(historicalFilename)}`);
            if (response.ok) {
                const status = await response.json();
                if (status.finished) {
                    clearInterval(checkStatusInterval);
                    hideLoadingIndicator(); // Скрыть индикатор загрузки
                    // Очистка LocalStorage
                    localStorage.removeItem('isUploading');
                    localStorage.removeItem('historicalFilename');
                    location.reload();
                }
            } else {
                console.error("Ошибка HTTP: " + response.status);
            }
        } catch (error) {
            clearInterval(checkStatusInterval);
            hideLoadingIndicator(); // Скрыть индикатор загрузки в случае ошибки
            console.error("Ошибка при запросе статуса:", error);
        }
    }, 5000);
}

function deleteFile(filename) {
    fetch(`/delete/${filename}`, { method: 'DELETE' })
    .then(response => {
        if (response.ok) {
            window.location.reload(); // Перезагрузить страницу, чтобы обновить список файлов
        } else {
            alert('Ошибка при удалении файла');
        }
    })
    .catch(error => console.error('Ошибка удаления файла:', error));
}