function toISOStringLocal(d) {
  function z(n){return (n<10?'0':'') + n}
  return d.getFullYear() + '-' + z(d.getMonth()+1) + '-' +
         z(d.getDate()) + ' ' + z(d.getHours()) + ':' +
         z(d.getMinutes()) + ':' + z(d.getSeconds())
}

function addGame(end_time) {
  key = sessionStorage.getItem('gameId');
  value='"' + key + '","' + toISOStringLocal(new Date()) + '","' + end_time + '"'
  console.log(value)
  axios.post('http://127.0.0.1:5000/add_game/' + key + '/' + value)
}

// New Game functionality
function startNewGame() {
  game.reset()
  board.position(game.fen())
  board.clearCircles()
  pendingMove = null
  updateStatus()
  updatePGN()
}

function surrender() {
  document.getElementById('gameStatus').innerHTML = 'Game over: White surrender. Black wins!'
  addGame(toISOStringLocal(new Date()))
}

// There are 5 outcomes from this action:
// - start a pending move
// - clear a pending move
// - clear a pending move AND start a different pending move
// - make a move (ie: complete their pending move)
// - do nothing
function onTouchSquare (square, piece, boardInfo) {
  // ask chess.js what legal moves are available from this square
  const legalMoves = game.moves({ square, verbose: true })

  // Option 1: start a pending move
  if (!pendingMove && legalMoves.length > 0) {
    pendingMove = square

    // add circles showing where the legal moves are for this piece
    legalMoves.forEach(move => {
      board.addCircle(move.to)
    })

  // Option 2: clear a pending move if the user selects the same square twice
  } else if (pendingMove && pendingMove === square) {
    pendingMove = null
    board.clearCircles()

  // Option 3: clear a pending move and start a new pending move
  } else if (pendingMove) {
    // ask chess.js to make a move
    const moveResult = game.move({
      from: pendingMove,
      to: square,
      promotion: 'q' // always promote to a Queen for example simplicity
    })

    // was this a legal move?
    if (moveResult) {
      // clear circles on the board
      board.clearCircles()

      // update to the new position
      board.position(game.fen()).then(() => {
        updatePGN()
        updateStatus()

        // wait a smidge, then make a random move for Black
        window.setTimeout(makeRandomMove, 250)
      })

    // if the move was not legal, then start a new pendingMove from this square
    } else if (piece) {
      pendingMove = square

      // remove any previous circles
      board.clearCircles()

      // add circles showing where the legal moves are for this piece
      legalMoves.forEach(m => {
        board.addCircle(m.to)
      })

    // else clear pendingMove
    } else {
      pendingMove = null
      board.clearCircles()
    }
  }
}

function updateStatus () {
  let statusHTML = ''
  const whosTurn = game.turn() === 'w' ? 'White' : 'Black'

  if (!game.game_over()) {
    if (game.in_check()) statusHTML = whosTurn + ' is in check! '
    statusHTML = 'Current turn: ' + statusHTML + whosTurn + ' to move'
  } else if (game.in_checkmate() && game.turn() === 'w') {
    statusHTML = 'Game over: white is in checkmate. Black wins!'
  } else if (game.in_checkmate() && game.turn() === 'b') {
    statusHTML = 'Game over: black is in checkmate. White wins!'
  } else if (game.in_stalemate() && game.turn() === 'w') {
    statusHTML = 'Game is drawn. White is stalemated.'
  } else if (game.in_stalemate() && game.turn() === 'b') {
    statusHTML = 'Game is drawn. Black is stalemated.'
  } else if (game.in_threefold_repetition()) {
    statusHTML = 'Game is drawn by threefold repetition rule.'
  } else if (game.insufficient_material()) {
    statusHTML = 'Game is drawn by insufficient material.'
  } else if (game.in_draw()) {
    statusHTML = 'Game is drawn by fifty-move rule.'
  }

  document.getElementById('gameStatus').innerHTML = statusHTML
}

function createMove() {
  const moves = game.history({ verbose: true })
  const lastMove = moves[moves.length - 1]
  const key = uuid.v4();
  const player = lastMove.color == 'w' ? 'Player' : 'AI'
  const move = `${getPieceName(lastMove.piece)} from ${lastMove.from} to ${lastMove.to}`
  const value = '"' + key + '","' + sessionStorage.getItem('gameId') + '","' + player + '","' + move + '","' + toISOStringLocal(new Date()) + '"'
  
  console.log(value)
  axios.post('http://127.0.0.1:5000/add_move/' + key + '/' + value)
}

function getPieceName(piece) {
  const pieceNames = {
    'p': 'Pawn',
    'r': 'Rook',
    'n': 'Knight',
    'b': 'Bishop',
    'q': 'Queen',
    'k': 'King'
  }
  return pieceNames[piece] || piece
}

function updatePGN () {
  const pgnEl = document.getElementById('gamePGN')
  const moves = game.history({ verbose: true })
  let tableHTML = '<table style="width: 100%; border-collapse: collapse;"><thead><tr><th style="text-align:center;border: 1px solid #ccc; padding: 8px; background-color: #f5f5f5;">Move</th><th style="text-align:center;border: 1px solid #ccc; padding: 8px; background-color: #f5f5f5;">White</th><th style="text-align:center;border: 1px solid #ccc; padding: 8px; background-color: #f5f5f5;">Black</th></tr></thead><tbody>'


  for (let i = 0; i < moves.length; i += 2) {
    const moveNumber = Math.floor(i / 2) + 1
    const whiteMove = moves[i]
    const blackMove = moves[i + 1] || {'piece': '', 'from': '', 'to': ''}
    
    tableHTML += `<tr>
      <td style="border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">${moveNumber}</td>
      <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">
        <span style="background-color: #f0f0f0; color: #333; padding: 2px 4px; border-radius: 3px;">${getPieceName(whiteMove.piece)} from ${whiteMove.from} to ${whiteMove.to}</span>
      </td>
      <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">
        ${blackMove ? `<span style="background-color: #333; color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">${getPieceName(blackMove.piece)} from ${blackMove.from} to ${blackMove.to}</span>` : ''}
      </td>
    </tr>`
  }
  
  tableHTML += '</tbody></table>'
  pgnEl.innerHTML = tableHTML

  createMove()
}

function onDragStart (dragStartEvt) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // only pick up pieces for White
  if (!isWhitePiece(dragStartEvt.piece)) return false

  // what moves are available to White from this square?
  const legalMoves = game.moves({
    square: dragStartEvt.square,
    verbose: true
  })

  // do nothing if there are no legal moves
  if (legalMoves.length === 0) return false

  // place Circles on the possible target squares
  legalMoves.forEach((move) => {
    board.addCircle(move.to)
  })
}

function isWhitePiece (piece) { return /^w/.test(piece) }

function makeRandomMove () {
  const possibleMoves = game.moves()

  // game over
  if (possibleMoves.length === 0) return

  const randomIdx = Math.floor(Math.random() * possibleMoves.length)
  game.move(possibleMoves[randomIdx])
  board.position(game.fen(), (_positionInfo) => {
    updateStatus()
    updatePGN()
  })
}

function onDrop (dropEvt) {
  // see if the move is legal
  const move = game.move({
    from: dropEvt.source,
    to: dropEvt.target,
    promotion: 'q' // NOTE: always promote to a queen for example simplicity
  })

  // remove all Circles from the board
  board.clearCircles()

  // the move was legal
  if (move) {
    // reset the pending move
    pendingMove = null

    // update the board position
    board.fen(game.fen(), () => {
      updateStatus()
      updatePGN()

      // make a random legal move for black
      window.setTimeout(makeRandomMove, 250)
    })
  } else {
    // reset the pending move
    pendingMove = null

    // return the piece to the source square if the move was illegal
    return 'snapback'
  }
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
  board.position(game.fen())
}

module.exports = {
  toISOStringLocal,
  addGame,
  startNewGame,
  surrender,
  onTouchSquare,
  updateStatus,
  createMove,
  getPieceName,
  updatePGN,
  onDragStart,
  isWhitePiece,
  makeRandomMove,
  onDrop,
  onSnapEnd
};