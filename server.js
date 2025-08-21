const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));

// 게임 상태 관리
const games = new Map();
const players = new Map();

// 숫자야구 게임 로직
class BaseballGame {
  constructor(digitCount = 3, isAIGame = false) {
    this.digitCount = digitCount;
    this.isAIGame = isAIGame;
    this.gameState = 'waiting'; // waiting, playing, finished
    this.round = 1;
    this.maxRounds = 20;
    this.currentPlayer = null; // 현재 추측하는 플레이어
    this.defender = null; // 수비하는 플레이어 (숫자를 정한 사람)
    this.attacker = null; // 공격하는 플레이어 (숫자를 추측하는 사람)
    this.secretNumber = null; // 맞춰야 할 숫자
    this.guessHistory = []; // 추측 기록
    this.winner = null;
  }

  // 게임 시작
  startGame(playerId, aiMode = false) {
    this.currentPlayer = playerId;
    
    if (aiMode) {
      // AI 게임: 플레이어가 공격, AI가 수비
      this.attacker = playerId;
      this.defender = 'ai';
      this.secretNumber = this.generateSecretNumber();
      console.log(`AI가 정한 숫자: ${this.secretNumber.join('')}`);
    } else {
      // 멀티플레이어: 플레이어가 수비, 상대방이 공격
      this.defender = playerId;
      this.attacker = null; // 상대방이 참가할 때 설정
    }
    
    this.gameState = 'playing';
    return true;
  }

  // 상대방 참가 (멀티플레이어용)
  addOpponent(playerId) {
    if (this.attacker === null) {
      this.attacker = playerId;
      this.currentPlayer = this.attacker; // 공격자부터 시작
      return true;
    }
    return false;
  }

  // 비밀 숫자 생성
  generateSecretNumber() {
    let numbers = [];
    while (numbers.length < this.digitCount) {
      const num = Math.floor(Math.random() * 10); // 0~9 범위
      if (!numbers.includes(num)) {
        numbers.push(num);
      }
    }
    return numbers;
  }

  // 추측 처리
  makeGuess(guess) {
    if (this.gameState !== 'playing') return null;
    
    // 입력 검증
    if (guess.length !== this.digitCount) {
      return { error: `${this.digitCount}자리 숫자를 입력해주세요!` };
    }
    
    // 중복 체크
    if (new Set(guess).size !== guess.length) {
      return { error: '중복되지 않는 숫자를 입력해주세요!' };
    }
    
    // 결과 계산
    const result = this.checkGuess(guess);
    
    // 기록 저장
    this.guessHistory.push({
      guess: guess,
      result: result,
      round: this.round
    });
    
    // 승리 체크
    if (result.strikes === this.digitCount) {
      this.gameState = 'finished';
      this.winner = this.currentPlayer;
      return { ...result, gameOver: true, winner: this.winner };
    }
    
    // 다음 라운드
    this.round++;
    if (this.round > this.maxRounds) {
      this.gameState = 'finished';
      this.winner = this.defender;
      return { ...result, gameOver: true, winner: this.winner, timeout: true };
    }
    
    return { ...result, gameOver: false };
  }

  // 추측 결과 계산
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

  // AI 차례 처리
  processAITurn() {
    if (this.currentPlayer !== 'ai' || this.gameState !== 'playing') return null;
    
    // AI가 추측할 숫자 생성 (간단한 랜덤 추측)
    const aiGuess = this.generateAIGuess();
    const result = this.makeGuess(aiGuess);
    
    return { guess: aiGuess, result: result };
  }

  // AI 추측 생성
  generateAIGuess() {
    let numbers = [];
    while (numbers.length < this.digitCount) {
      const num = Math.floor(Math.random() * 10);
      if (!numbers.includes(num)) {
        numbers.push(num);
      }
    }
    return numbers;
  }

  // 게임 정보 가져오기
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

// 소켓 연결 처리
io.on('connection', (socket) => {
  console.log('플레이어 연결됨:', socket.id);
  players.set(socket.id, { id: socket.id, gameId: null });

  // AI 게임 시작
  socket.on('startAIGame', (digitCount = 3) => {
    console.log(`AI 게임 시작: ${digitCount}자리, 플레이어: ${socket.id}`);
    
    const gameId = 'ai_game_' + Date.now();
    const game = new BaseballGame(digitCount, true);
    
    // 플레이어를 게임에 추가
    game.startGame(socket.id, true);
    games.set(gameId, game);
    players.get(socket.id).gameId = gameId;
    socket.join(gameId);
    
    console.log(`AI 게임 생성됨: ${gameId}`);
    console.log(`게임 정보:`, game.getGameInfo());
    
    io.to(gameId).emit('aiGameStarted', {
      gameId: gameId,
      gameInfo: game.getGameInfo()
    });
  });

  // 숫자 추측
  socket.on('makeGuess', (guess) => {
    const player = players.get(socket.id);
    if (!player || !player.gameId) {
      socket.emit('error', { message: '게임에 참가하지 않았습니다.' });
      return;
    }
    
    const game = games.get(player.gameId);
    if (!game) {
      socket.emit('error', { message: '게임을 찾을 수 없습니다.' });
      return;
    }
    
    if (game.gameState !== 'playing') {
      socket.emit('error', { message: '게임이 진행 중이 아닙니다.' });
      return;
    }
    
    // 현재 플레이어의 차례인지 확인
    if (game.currentPlayer !== socket.id) {
      socket.emit('error', { message: '아직 당신의 차례가 아닙니다.' });
      return;
    }
    
    console.log(`플레이어 ${socket.id} 추측: ${guess.join('')}`);
    
    // 추측 처리
    const result = game.makeGuess(guess);
    
    if (result.error) {
      socket.emit('error', { message: result.error });
      return;
    }
    
    // 결과 전송
    io.to(player.gameId).emit('guessResult', {
      playerId: socket.id,
      guess: guess,
      result: result,
      round: game.round,
      gameInfo: game.getGameInfo()
    });
    
    // 게임 종료 체크
    if (result.gameOver) {
      console.log(`게임 종료! 승자: ${result.winner}`);
      io.to(player.gameId).emit('gameOver', {
        winner: result.winner,
        gameInfo: game.getGameInfo(),
        secretNumber: game.secretNumber
      });
      return;
    }
    
    // AI 게임인 경우 AI 차례로 넘어가기
    if (game.isAIGame && game.currentPlayer === socket.id) {
      setTimeout(() => {
        console.log('AI 차례 시작');
        const aiResult = game.processAITurn();
        
        if (aiResult) {
          console.log(`AI 추측: ${aiResult.guess.join('')}, 결과: ${aiResult.result.strikes}S ${aiResult.result.balls}B`);
          
          io.to(player.gameId).emit('aiGuess', {
            guess: aiResult.guess,
            result: aiResult.result,
            gameInfo: game.getGameInfo()
          });
          
          if (aiResult.result.gameOver) {
            console.log(`AI 게임 종료! 승자: ${aiResult.result.winner}`);
            io.to(player.gameId).emit('gameOver', {
              winner: aiResult.result.winner,
              gameInfo: game.getGameInfo(),
              secretNumber: game.secretNumber
            });
          }
        }
      }, 1000);
    }
  });

  // 연결 해제 처리
  socket.on('disconnect', () => {
    console.log('플레이어 연결 해제:', socket.id);
    const player = players.get(socket.id);
    if (player && player.gameId) {
      const game = games.get(player.gameId);
      if (game) {
        // 게임에서 플레이어 제거
        if (game.attacker === socket.id) {
          game.attacker = null;
        }
        if (game.defender === socket.id) {
          game.defender = null;
        }
        
        // 게임이 비어있으면 삭제
        if (!game.attacker && !game.defender) {
          games.delete(player.gameId);
        }
      }
    }
    players.delete(socket.id);
  });
});

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';

server.listen(PORT, HOST, () => {
  console.log(`서버가 포트 ${PORT}에서 실행 중입니다.`);
  console.log(`환경: ${process.env.NODE_ENV || 'development'}`);
  console.log(`로컬 접속: http://localhost:${PORT}`);
  console.log(`네트워크 접속: http://${getLocalIP()}:${PORT}`);
});

// 로컬 IP 주소 가져오기
function getLocalIP() {
  const { networkInterfaces } = require('os');
  const nets = networkInterfaces();
  
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      // IPv4이고 내부 주소가 아닌 경우
      if (net.family === 'IPv4' && !net.internal) {
        return net.address;
      }
    }
  }
  return 'localhost';
}
