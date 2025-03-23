document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault(); // Impede o envio padrão do formulário

    const bethaFile = document.getElementById('bethaFile').files[0];
    const tceFile = document.getElementById('tceFile').files[0];
    const mode = document.getElementById('mode').value;

    if (!bethaFile || !tceFile) {
        alert("Por favor, selecione ambos os arquivos.");
        return;
    }

    const formData = new FormData();
    formData.append('bethaFile', bethaFile);
    formData.append('tceFile', tceFile);
    formData.append('mode', mode);

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Erro ao processar os arquivos.');
        }

        const data = await response.json();
        document.getElementById('output').innerText = data.output;
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('output').innerText = 'Erro ao processar os arquivos.';
    }
});