(function () {
    const PIECE_UNICODE = {
        'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
        'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
    };
    const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

    const boardEl = document.getElementById('board');
    if (!boardEl) return;

    const gameId = boardEl.dataset.gameId;
    let fen = boardEl.dataset.fen;
    const userColor = boardEl.dataset.userColor;
    let status = boardEl.dataset.status;
    const isBot = boardEl.dataset.isBot === 'true';
    let selected = null;
    let legalTargets = [];
    let lastMoveSquares = [];
    let flipped = userColor === 'black';
    let knownMoveCount = document.querySelectorAll('#move-list > div').length;

    function getCookie(name) {
        const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? match.pop() : '';
    }
    const csrftoken = getCookie('csrftoken');

    function parseFenBoard(fenStr) {
        const rows = fenStr.split(' ')[0].split('/');
        const grid = {};
        rows.forEach((row, rIdx) => {
            const rank = 8 - rIdx;
            let file = 0;
            for (const ch of row) {
                if (/\d/.test(ch)) {
                    file += parseInt(ch, 10);
                } else {
                    const sq = FILES[file] + rank;
                    grid[sq] = ch;
                    file += 1;
                }
            }
        });
        return grid;
    }

    function squareId(file, rank) { return FILES[file] + rank; }

    function render() {
        const grid = parseFenBoard(fen);
        boardEl.innerHTML = '';
        const rankOrder = flipped ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1];
        const fileOrder = flipped ? [7,6,5,4,3,2,1,0] : [0,1,2,3,4,5,6,7];

        rankOrder.forEach(rank => {
            fileOrder.forEach(fileIdx => {
                const sq = squareId(fileIdx, rank);
                const isLight = (fileIdx + rank) % 2 === 1;
                const div = document.createElement('div');
                div.className = 'square ' + (isLight ? 'light' : 'dark');
                div.dataset.square = sq;
                if (grid[sq]) {
                    const isWhitePiece = grid[sq] === grid[sq].toUpperCase();
                    const colorClass = isWhitePiece ? 'piece-white' : 'piece-black';
                    div.innerHTML = `<span class="piece ${colorClass}">${PIECE_UNICODE[grid[sq]]}</span>`;
                }
                if (selected === sq) div.classList.add('selected');
                if (lastMoveSquares.includes(sq)) div.classList.add('last-move');
                if (legalTargets.includes(sq)) {
                    div.classList.add(grid[sq] ? 'legal-capture' : 'legal-target');
                }
                div.addEventListener('click', () => onSquareClick(sq, grid));
                boardEl.appendChild(div);
            });
        });
    }

    function isOwnPiece(piece) {
        if (!piece) return false;
        const isWhitePiece = piece === piece.toUpperCase();
        return (userColor === 'white' && isWhitePiece) || (userColor === 'black' && !isWhitePiece);
    }

    async function onSquareClick(sq, grid) {
        if (status !== 'active' || !userColor) return;
        const turnColor = fen.split(' ')[1] === 'w' ? 'white' : 'black';
        if (turnColor !== userColor) return;

        if (selected && legalTargets.includes(sq)) {
            const piece = grid[selected];
            const isPromotion = piece && piece.toLowerCase() === 'p' && (sq[1] === '8' || sq[1] === '1');
            if (isPromotion) {
                const promoPiece = await askPromotion();
                await sendMove(selected + sq + promoPiece);
            } else {
                await sendMove(selected + sq);
            }
            selected = null;
            legalTargets = [];
            return;
        }

        if (grid[sq] && isOwnPiece(grid[sq])) {
            selected = sq;
            const resp = await fetch(`/${gameId}/legal-moves/?square=${sq}`);
            const data = await resp.json();
            legalTargets = data.ok ? data.moves.map(m => m.slice(2, 4)) : [];
            render();
        } else {
            selected = null;
            legalTargets = [];
            render();
        }
    }

    function askPromotion() {
        return new Promise(resolve => {
            const modal = document.getElementById('promotion-modal');
            modal.style.display = 'flex';
            const buttons = modal.querySelectorAll('button');
            function handler(e) {
                modal.style.display = 'none';
                buttons.forEach(b => b.removeEventListener('click', handler));
                resolve(e.target.dataset.piece);
            }
            buttons.forEach(b => b.addEventListener('click', handler));
        });
    }

    async function sendMove(uci) {
        const resp = await fetch(`/${gameId}/move/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken,
            },
            body: `move=${encodeURIComponent(uci)}`,
        });
        const data = await resp.json();
        if (!data.ok) {
            alert(data.error || 'Yurish rad etildi');
            return;
        }
        fen = data.fen;
        lastMoveSquares = [data.uci.slice(0, 2), data.uci.slice(2, 4)];
        appendMove(data.san);
        knownMoveCount += 1;
        if (data.bot_move) {
            fen = data.bot_move.fen;
            lastMoveSquares = [data.bot_move.uci.slice(0, 2), data.bot_move.uci.slice(2, 4)];
            appendMove(data.bot_move.san);
            knownMoveCount += 1;
        }
        render();
        if (data.game_over) {
            status = 'finished';
            setTimeout(() => window.location.reload(), 600);
        }
    }

    function appendMove(san) {
        const list = document.getElementById('move-list');
        if (!list) return;
        const row = document.createElement('div');
        const n = list.children.length + 1;
        row.innerHTML = `<span>${n}.</span><span>${san}</span>`;
        list.appendChild(row);
        list.scrollTop = list.scrollHeight;
    }

    const resignBtn = document.getElementById('resign-btn');
    if (resignBtn) {
        resignBtn.addEventListener('click', async () => {
            if (!confirm('Rostdan ham taslim bo\'lasizmi?')) return;
            await fetch(`/${gameId}/resign/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
            });
            window.location.reload();
        });
    }

    render();

    function formatTime(ms) {
        const totalSec = Math.max(0, Math.floor(ms / 1000));
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    }
    const whiteTimerEl = document.getElementById('white-timer');
    const blackTimerEl = document.getElementById('black-timer');
    if (whiteTimerEl) whiteTimerEl.textContent = formatTime(parseInt(whiteTimerEl.textContent, 10) || 0);
    if (blackTimerEl) blackTimerEl.textContent = formatTime(parseInt(blackTimerEl.textContent, 10) || 0);

    async function pollOpponentMoves() {
        if (status !== 'active') return;
        try {
            const resp = await fetch(`/${gameId}/state/`);
            const data = await resp.json();
            if (!data.ok) return;

            if (data.moves.length > knownMoveCount) {
                for (let i = knownMoveCount; i < data.moves.length; i++) {
                    appendMove(data.moves[i].san);
                }
                const last = data.moves[data.moves.length - 1];
                fen = data.fen;
                lastMoveSquares = [last.uci.slice(0, 2), last.uci.slice(2, 4)];
                selected = null;
                legalTargets = [];
                knownMoveCount = data.moves.length;
                render();
            }

            if (data.status === 'finished' && status !== 'finished') {
                window.location.reload();
            }
        } catch (e) {
            // transient network hiccup — try again on the next tick
        }
    }

    if (status === 'active' && !isBot) {
        setInterval(pollOpponentMoves, 1500);
    }

    if (status === 'waiting') {
        setInterval(() => window.location.reload(), 4000);
    }
})();
