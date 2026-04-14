(async () => {
    console.log("Запуск. Остановка командой: stop()");
    const matchMap = new Map();
    window.isCollecting = true;
    window.stop = () => { window.isCollecting = false; };

    while (window.isCollecting) {
        let button = document.getElementById('load_more_button');
        if (!button || button.style.display === 'none') break;

        button.click();

        let rows = document.querySelectorAll('tr');
        rows.forEach(row => {
            let cells = row.querySelectorAll('td');
            if (cells.length >= 5) {
                let matchId = cells[0].innerText.trim();
                let mode = cells[4].innerText.trim();

                if (/^\d{10}$/.test(matchId)) {
                    matchMap.set(matchId, mode);
                }
            }
        });

        console.log(`Собрано уникальных ID: ${matchMap.size}. Для сохранения введи stop()`);
        await new Promise(r => setTimeout(r, 1200));
    }

    let csvContent = "Match_ID,GameMode\n";
    matchMap.forEach((mode, id) => {
        csvContent += `${id},${mode}\n`;
    });

    const blob = new Blob([csvContent], {type: 'text/csv'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'dota_ids_for_api.csv';
    a.click();
    console.log("Готово! Файл сохранен.");
})();