let playerTurn = true;

// 創建15x15棋盤
function createBoard() {

    const board = document.getElementById('board');

    for (let i = 0; i < 15; i++) {
        for (let j = 0; j < 15; j++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.addEventListener('click', handleClick);
            board.appendChild(cell);
        }
    }
}

// 處理玩家落子
function handleClick(event) {

    const cell = event.target;
    const row = parseInt(cell.dataset.row);
    const col = parseInt(cell.dataset.col);

    cell.setAttribute("data-player", "1");
    cell.removeEventListener('click', handleClick);

    playerTurn = false;
    updateHoverStyle();

    fetch('/api/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row, col })
    })
    .then(response => response.json())
    .then(data => {

        setTimeout(()=>{
            if (data) {
                updateBoard(data.board);

                if (data.game_over) {
                    surrenderBtn.removeEventListener('click', surrender);
                    highlightWinningCells(data.winning_cells);
                    setTimeout(() => {
                        showResult(data.winner === 1 ? '你贏了' : data.winner === 0 ? '平手' : '你輸了');
                    },3000)
                } else{
                    playerTurn = data.player_turn;
                    updateHoverStyle();
                }

            } else {
                alert('error occur')
            }
        }, 700);

    });
}

// 認輸
function surrender() {
    // TODO: 通知後端玩家認輸
    setTimeout(() => {
        showResult('你輸了');
    },1000)
}


// 開始新遊戲
function startNewGame() {
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            updateBoard(data.board);
        });
}

function updateBoard(board) {

    const boardElement = document.getElementById('board');

    for (let i = 0; i < 15; i++) {
        for (let j = 0; j < 15; j++) {
            const cell = boardElement.children[i * 15 + j];
            const player = board[i][j];
            console.log(player)

            if (player === 1) {
                cell.setAttribute("data-player", "1");
            } else if (player === -1) {
                cell.setAttribute("data-player", "-1");
            }
        }
    }
}

function updateHoverStyle() {
    const cells = document.querySelectorAll('.cell');
    cells.forEach(cell => {
        if (playerTurn && ! cell.hasAttribute('data-player')) {
            cell.classList.add('hover');
            cell.addEventListener('click', handleClick);
        } else {
            cell.classList.remove('hover');
            cell.removeEventListener('click', handleClick);
        }
    });
}

// 顯示遊戲結果
function showResult(result) {
    window.location.href = '/result';
    localStorage.setItem('gameResult', result);
}

function highlightWinningCells(winningCells) {
    winningCells.forEach(([row, col]) => {
        const cell = document.getElementById('board').children[row * 15 + col];
        cell.classList.add('winning-piece');
    });
}