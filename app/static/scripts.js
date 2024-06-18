document.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOMContentLoaded event fired');
    const fileInput = document.querySelector('input[type="file"]');
    const uploadForm = document.querySelector('form');

    if (fileInput && uploadForm) {
        console.log('Input and form elements found.');

        fileInput.addEventListener('change', async (event) => {
            console.log('File input change event fired.');

            if (fileInput.files.length > 0) {
                console.log('File selected:', fileInput.files[0]);

                let formData = new FormData(uploadForm);

                try {
                    console.log('Submitting form data...');
                    let response = await fetch(uploadForm.action, {
                        method: 'POST',
                        body: formData,
                    });

                    // Получаем полный текст ответа
                    let responseText = await response.text();
                    console.log('Response text:', responseText);

                    // Проверка состояния ответа и типа содержимого
                    if (response.ok) {
                        console.log('Content-Type:', response.headers.get('content-type'));
                        if (response.headers.get('content-type').includes('application/json')) {
                            let data = JSON.parse(responseText);
                            let historicalFilename = data.historical_filename;
                            if (historicalFilename) {
                                console.log('Received historical filename:', historicalFilename);

                                localStorage.setItem('isUploading', 'true');
                                localStorage.setItem('historicalFilename', historicalFilename);
                                waitForCompletion(historicalFilename);
                            }
                        } else {
                            console.error('Expected JSON response, but received:', response.headers.get('content-type'));
                        }
                    } else {
                        console.error('HTTP error:', response.status);
                    }
                } catch (error) {
                    console.error('Error submitting the form:', error);
                }
            } else {
                console.log('No file selected.');
            }
        });

        uploadForm.addEventListener('submit', async (event) => {
            console.log('Form submit event fired.');
            event.preventDefault();
            if (fileInput.files.length > 0) {
                let formData = new FormData(uploadForm);
                try {
                    console.log('Submitting form data...');
                    let response = await fetch(uploadForm.action, {
                        method: 'POST',
                        body: formData,
                    });

                    // Получаем полный текст ответа
                    let responseText = await response.text();
                    console.log('Response text:', responseText);

                    // Проверка состояния ответа и типа содержимого
                    if (response.ok) {
                        console.log('Content-Type:', response.headers.get('content-type'));
                        if (response.headers.get('content-type').includes('application/json')) {
                            let data = JSON.parse(responseText);
                            let historicalFilename = data.historical_filename;
                            if (historicalFilename) {
                                waitForCompletion(historicalFilename);
                            }
                        } else {
                            console.error('Expected JSON response, but received:', response.headers.get('content-type'));
                        }
                    } else {
                        console.error('HTTP error:', response.status);
                    }
                } catch (error) {
                    console.error('Error submitting the form:', error);
                }
            } else {
                console.log('No file selected.');
            }
        });
    } else {
        console.error('Input or form elements not found.');
    }
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
            const response = await fetch(`status/${encodeURIComponent(historicalFilename)}`);
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
    fetch(`/delete/${filename}`, {method: 'DELETE'})
        .then(response => {
            if (response.ok) {
                window.location.reload(); // Перезагрузить страницу, чтобы обновить список файлов
            } else {
                alert('Ошибка при удалении файла');
            }
        })
        .catch(error => console.error('Ошибка удаления файла:', error));
}