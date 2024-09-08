function showNPSPopup() {
    var popupHtml = `
        <div id="nps-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 9999;">
            <div id="nps-popup" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);">
                <h2 style="font-size: 16px; margin-top: 0;">How likely are you to recommend us?</h2>
                <div id="nps-scale">
                    ${[0,1,2,3,4,5,6,7,8,9,10].map(num => 
                        `<button class="nps-btn" data-score="${num}">${num}</button>`
                    ).join('')}
                </div>
                <textarea id="nps-feedback" placeholder="What's the primary reason for your score?" style="width: 100%; margin-top: 10px;"></textarea>
                <button id="nps-submit" style="margin-top: 10px;">Submit</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', popupHtml);

    document.querySelectorAll('.nps-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.nps-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    document.getElementById('nps-submit').addEventListener('click', function() {
        var selectedBtn = document.querySelector('.nps-btn.selected');
        var score = selectedBtn ? selectedBtn.dataset.score : undefined;
        var feedback = document.getElementById('nps-feedback').value;
        if (score !== undefined) {
            window.npsResult = { score: score, feedback: feedback };
            document.getElementById('nps-popup').remove();
            document.getElementById('nps-overlay').remove(); // Remove the overlay
        } else {
            alert('Please select a score');
        }
    });
}