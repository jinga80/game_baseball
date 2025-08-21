const { Server } = require('socket.io');

// Socket.IO 서버 인스턴스 (전역 변수로 관리)
let io = null;

// 게임 상태 관리
const games = new Map();
const players = new Map();

// 숫자야구 게임 로직
class BaseballGame {
  constructor(digitCount = 3, isAIGame = false) {
    this.digitCount = digitCount;
    this.isAIGame = isAIGame;
    this.gameState = 'waiting';
    this.round = 1;
    this.maxRounds = 20;
    this.currentPlayer = null;
    this.defender = null;
    this.attacker = null;
    this.secretNumber = null;
    this.guessHistory = [];
    this.winner = null;
  }

  startGame(playerId, aiMode = false) {
    this.currentPlayer = playerId;
    
    if (aiMode) {
      this.attacker = playerId;
      this.defender = 'ai';
      this.secretNumber = this.generateSecretNumber();
    } else {
      this.defender = playerId;
      this.attacker = null;
    }
    
    this.gameState = 'playing';
    return true;
  }

  generateSecretNumber() {
    let numbers = [];
    while (numbers.length < this.digitCount) {
      const num = Math.floor(Math.random() * 10);
      if (!numbers.includes(num)) {
        numbers.push(num);
      }
    }
    return numbers;
  }

  makeGuess(guess) {
    if (this.gameState !== 'playing') return null;
    
    if (guess.length !== this.digitCount) {
      return { error: `${this.digitCount}자리 숫자를 입력해주세요!` };
    }
    
    if (new Set(guess).size !== guess.length) {
      return { error: '중복되지 않는 숫자를 입력해주세요!' };
    }
    
    const result = this.checkGuess(guess);
    
    this.guessHistory.push({
      guess: guess,
      result: result,
      round: this.round
    });
    
    if (result.strikes === this.digitCount) {
      this.gameState = 'finished';
      this.winner = this.currentPlayer;
      return { ...result, gameOver: true, winner: this.winner };
    }
    
    this.round++;
    if (this.round > this.maxRounds) {
      this.gameState = 'finished';
      this.winner = this.defender;
      return { ...result, gameOver: true, winner: this.winner, timeout: true };
    }
    
    return { ...result, gameOver: false };
  }

  checkGuess(guess) {
    let strikes = 0;
    let balls = 0;
    
    for (let i = 0; i < this.digitCount; i++) {
      if (guess[i] === this.secretNumber[i]) {
        strikes++;
      } else if (this.secretNumber.includes(guess[i])) {
        balls++;
      }
    }
    
    return { strikes, balls };
  }

  getGameInfo() {
    return {
      digitCount: this.digitCount,
      gameState: this.gameState,
      round: this.round,
      maxRounds: this.maxRounds,
      currentPlayer: this.currentPlayer,
      defender: this.defender,
      attacker: this.attacker,
      guessHistory: this.guessHistory,
      winner: this.winner,
      isAIGame: this.isAIGame
    };
  }
}

// Netlify Function 핸들러
exports.handler = async (event, context) => {
  // CORS 헤더 설정
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  // OPTIONS 요청 처리 (CORS preflight)
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const { action, data } = JSON.parse(event.body || '{}');

    switch (action) {
      case 'startAIGame':
        return handleStartAIGame(data, headers);
      
      case 'makeGuess':
        return handleMakeGuess(data, headers);
      
      default:
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Unknown action' })
        };
    }
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message })
    };
  }
};

// AI 게임 시작 처리
function handleStartAIGame(data, headers) {
  const { digitCount = 3, playerId } = data;
  
  const gameId = 'ai_game_' + Date.now();
  const game = new BaseballGame(digitCount, true);
  
  game.startGame(playerId, true);
  games.set(gameId, game);
  players.set(playerId, { id: playerId, gameId: gameId });
  
  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({
      success: true,
      gameId: gameId,
      gameInfo: game.getGameInfo()
    })
  };
}

// 추측 처리
function handleMakeGuess(data, headers) {
  const { gameId, guess, playerId } = data;
  
  const game = games.get(gameId);
  if (!game) {
    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ error: 'Game not found' })
    };
  }
  
  if (game.gameState !== 'playing') {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Game is not in progress' })
    };
  }
  
  if (game.currentPlayer !== playerId) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Not your turn' })
    };
  }
  
  const result = game.makeGuess(guess);
  
  if (result.error) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: result.error })
    };
  }
  
  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({
      success: true,
      result: result,
      gameInfo: game.getGameInfo()
    })
  };
}
