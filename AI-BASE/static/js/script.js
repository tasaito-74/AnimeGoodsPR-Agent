document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('articleForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const resultMessage = document.getElementById('resultMessage');
    const errorMessage = document.getElementById('errorMessage');
    const docsLink = document.getElementById('docsLink');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // フォームデータを取得
        const formData = new FormData(form);
        const url = formData.get('url');
        const formatType = formData.get('format_type');

        // バリデーション
        if (!url) {
            showError('URLを入力してください');
            return;
        }

        // ローディング状態を開始
        startLoading();

        try {
            // APIリクエスト
            const response = await fetch('/generate-article', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showResult(data.message, data.docs_url);
            } else {
                showError(data.detail || '記事の生成に失敗しました');
            }

        } catch (error) {
            console.error('エラー:', error);
            showError('ネットワークエラーが発生しました。再度お試しください。');
        } finally {
            stopLoading();
        }
    });

    function startLoading() {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        hideMessages();
    }

    function stopLoading() {
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoading.style.display = 'none';
    }

    function showResult(message, docsUrl) {
        resultMessage.textContent = message;
        docsLink.href = docsUrl;

        resultDiv.style.display = 'block';
        errorDiv.style.display = 'none';

        // 結果までスクロール
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(message) {
        errorMessage.textContent = message;

        errorDiv.style.display = 'block';
        resultDiv.style.display = 'none';

        // エラーまでスクロール
        errorDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function hideMessages() {
        resultDiv.style.display = 'none';
        errorDiv.style.display = 'none';
    }

    // URL入力フィールドのバリデーション
    const urlInput = document.getElementById('url');
    urlInput.addEventListener('input', function () {
        const url = this.value;
        if (url && !isValidUrl(url)) {
            this.setCustomValidity('有効なURLを入力してください');
        } else {
            this.setCustomValidity('');
        }
    });

    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    // トグルボタンのアニメーション
    const toggles = document.querySelectorAll('.toggle input[type="radio"]');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', function () {
            // 他のトグルをリセット
            const group = this.name;
            document.querySelectorAll(`input[name="${group}"]`).forEach(other => {
                if (other !== this) {
                    other.checked = false;
                }
            });
        });
    });

    // フォームのリセット機能
    function resetForm() {
        form.reset();
        hideMessages();

        // デフォルト選択を復元
        document.querySelector('input[name="format_type"][value="popup"]').checked = true;
    }

    // 新しい記事生成ボタンを追加（結果表示後に表示）
    function addNewArticleButton() {
        if (!document.getElementById('newArticleBtn')) {
            const newBtn = document.createElement('button');
            newBtn.id = 'newArticleBtn';
            newBtn.className = 'submit-btn';
            newBtn.style.marginTop = '20px';
            newBtn.textContent = '新しい記事を生成';
            newBtn.addEventListener('click', function () {
                resetForm();
                this.remove();
            });

            resultDiv.appendChild(newBtn);
        }
    }

    // 結果表示後に新しい記事生成ボタンを追加
    const originalShowResult = showResult;
    showResult = function (message, docsUrl) {
        originalShowResult(message, docsUrl);
        setTimeout(addNewArticleButton, 1000);
    };
}); 