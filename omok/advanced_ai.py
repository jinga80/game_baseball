import random
from typing import List, Tuple, Dict, Optional
import math

class AdvancedOmokAI:
    """고급 오목 AI - Minimax + Alpha-Beta Pruning + 전략적 사고"""
    
    def __init__(self, difficulty: str = 'normal'):
        self.difficulty = difficulty
        self.board_size = 15
        self.max_depth = 4  # 기본 탐색 깊이
        
        # 난이도별 설정
        self.difficulty_settings = {
            'easy': {'max_depth': 2, 'random_factor': 0.4, 'analysis_depth': 1},
            'normal': {'max_depth': 3, 'random_factor': 0.2, 'analysis_depth': 2},
            'hard': {'max_depth': 4, 'random_factor': 0.1, 'analysis_depth': 3},
            'expert': {'max_depth': 5, 'random_factor': 0.0, 'analysis_depth': 4}
        }
        
        # 설정 적용
        settings = self.difficulty_settings[difficulty]
        self.max_depth = settings['max_depth']
        self.random_factor = settings['random_factor']
        self.analysis_depth = settings['analysis_depth']
        
        # 위치 가중치 (중앙일수록 높은 가중치)
        self.position_weights = self._create_position_weights()
        
        # 패턴 점수
        self.pattern_scores = {
            'win': 100000,      # 승리
            'open_four': 10000, # 열린 4연속
            'blocked_four': 1000, # 막힌 4연속
            'open_three': 1000,  # 열린 3연속
            'blocked_three': 100, # 막힌 3연속
            'open_two': 100,     # 열린 2연속
            'blocked_two': 10    # 막힌 2연속
        }
    
    def _create_position_weights(self) -> List[List[float]]:
        """위치 가중치 생성 (중앙일수록 높음)"""
        weights = [[0.0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        center = self.board_size // 2
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                # 중앙으로부터의 거리
                distance = abs(i - center) + abs(j - center)
                # 가중치 계산 (중앙일수록 높음)
                weights[i][j] = max(0, 10 - distance)
        
        return weights
    
    def get_best_move(self, board: List[List[str]], player: str) -> Tuple[int, int]:
        """최적의 수 찾기"""
        # 랜덤 팩터 적용
        if random.random() < self.random_factor:
            return self._get_random_move(board)
        
        # 위험한 상황 체크 (즉시 방어 필요)
        defensive_move = self._find_critical_defense(board, player)
        if defensive_move:
            return defensive_move
        
        # 공격 기회 체크 (즉시 승리 가능)
        attack_move = self._find_winning_move(board, player)
        if attack_move:
            return attack_move
        
        # Minimax 알고리즘으로 최적 수 찾기
        best_move = self._minimax_search(board, player)
        if best_move:
            return best_move
        
        # 차선책: 전략적 위치
        return self._get_strategic_move(board, player)
    
    def _get_random_move(self, board: List[List[str]]) -> Tuple[int, int]:
        """랜덤 수 선택"""
        empty_positions = self._get_empty_positions(board)
        if not empty_positions:
            return (7, 7)  # 중앙
        
        # 중앙 근처 우선
        center_positions = [(i, j) for i, j in empty_positions if 5 <= i <= 9 and 5 <= j <= 9]
        if center_positions:
            return random.choice(center_positions)
        
        return random.choice(empty_positions)
    
    def _find_critical_defense(self, board: List[List[str]], player: str) -> Optional[Tuple[int, int]]:
        """치명적인 방어 수 찾기"""
        opponent = 'black' if player == 'white' else 'white'
        empty_positions = self._get_empty_positions(board)
        
        for row, col in empty_positions:
            # 임시로 상대방 수를 두고 승리 체크
            board[row][col] = opponent
            if self._check_winner(board, row, col, opponent):
                board[row][col] = ''  # 되돌리기
                return (row, col)  # 이 위치를 막아야 함
            board[row][col] = ''  # 되돌리기
        
        return None
    
    def _find_winning_move(self, board: List[List[str]], player: str) -> Optional[Tuple[int, int]]:
        """승리 수 찾기"""
        empty_positions = self._get_empty_positions(board)
        
        for row, col in empty_positions:
            # 임시로 수를 두고 승리 체크
            board[row][col] = player
            if self._check_winner(board, row, col, player):
                board[row][col] = ''  # 되돌리기
                return (row, col)  # 승리 수
            board[row][col] = ''  # 되돌리기
        
        return None
    
    def _minimax_search(self, board: List[List[str]], player: str) -> Optional[Tuple[int, int]]:
        """Minimax 알고리즘으로 최적 수 찾기"""
        empty_positions = self._get_empty_positions(board)
        if not empty_positions:
            return None
        
        best_score = -float('inf')
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        
        for row, col in empty_positions:
            board[row][col] = player
            score = self._minimax(board, self.max_depth - 1, False, player, alpha, beta)
            board[row][col] = ''  # 되돌리기
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
            
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break  # Alpha-Beta Pruning
        
        return best_move
    
    def _minimax(self, board: List[List[str]], depth: int, is_maximizing: bool, 
                 player: str, alpha: float, beta: float) -> float:
        """Minimax 알고리즘 재귀 함수"""
        if depth == 0:
            return self._evaluate_board(board, player)
        
        empty_positions = self._get_empty_positions(board)
        if not empty_positions:
            return 0
        
        if is_maximizing:
            max_score = -float('inf')
            for row, col in empty_positions:
                board[row][col] = player
                score = self._minimax(board, depth - 1, False, player, alpha, beta)
                board[row][col] = ''
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
            return max_score
        else:
            min_score = float('inf')
            opponent = 'black' if player == 'white' else 'white'
            for row, col in empty_positions:
                board[row][col] = opponent
                score = self._minimax(board, depth - 1, True, player, alpha, beta)
                board[row][col] = ''
                min_score = min(min_score, score)
                beta = min(beta, score)
                if alpha >= beta:
                    break
            return min_score
    
    def _evaluate_board(self, board: List[List[str]], player: str) -> float:
        """보드 상태 평가"""
        score = 0
        opponent = 'black' if player == 'white' else 'white'
        
        # 각 위치별 평가
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == player:
                    score += self._evaluate_position(board, i, j, player) * self.position_weights[i][j]
                elif board[i][j] == opponent:
                    score -= self._evaluate_position(board, i, j, opponent) * self.position_weights[i][j]
        
        return score
    
    def _evaluate_position(self, board: List[List[str]], row: int, col: int, player: str) -> float:
        """특정 위치의 가치 평가"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            # 한 방향으로 연속된 돌 분석
            pattern_info = self._analyze_line(board, row, col, dr, dc, player)
            score += self._score_pattern(pattern_info)
            
            # 반대 방향으로 연속된 돌 분석
            pattern_info = self._analyze_line(board, row, col, -dr, -dc, player)
            score += self._score_pattern(pattern_info)
        
        return score
    
    def _analyze_line(self, board: List[List[str]], row: int, col: int, 
                      dr: int, dc: int, player: str) -> Dict[str, int]:
        """한 방향의 돌 패턴 분석"""
        count = 1
        blocked = 0
        
        # 현재 위치에서 한 방향으로 이동
        r, c = row + dr, col + dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size:
            if board[r][c] == player:
                count += 1
            elif board[r][c] == '':
                break
            else:
                blocked += 1
                break
            r += dr
            c += dc
        
        return {
            'count': count,
            'blocked': blocked,
            'open': blocked == 0
        }
    
    def _score_pattern(self, pattern_info: Dict[str, int]) -> float:
        """패턴 점수 계산"""
        count = pattern_info['count']
        blocked = pattern_info['blocked']
        is_open = pattern_info['open']
        
        if count >= 5:
            return self.pattern_scores['win']
        elif count == 4:
            if is_open:
                return self.pattern_scores['open_four']
            else:
                return self.pattern_scores['blocked_four']
        elif count == 3:
            if is_open:
                return self.pattern_scores['open_three']
            else:
                return self.pattern_scores['blocked_three']
        elif count == 2:
            if is_open:
                return self.pattern_scores['open_two']
            else:
                return self.pattern_scores['blocked_two']
        
        return 0
    
    def _get_strategic_move(self, board: List[List[str]], player: str) -> Tuple[int, int]:
        """전략적 위치 찾기"""
        empty_positions = self._get_empty_positions(board)
        if not empty_positions:
            return (7, 7)
        
        # 중앙 우선
        center_positions = [(i, j) for i, j in empty_positions if 5 <= i <= 9 and 5 <= j <= 9]
        if center_positions:
            return random.choice(center_positions)
        
        # 모서리 근처 (전략적 위치)
        corner_positions = [(i, j) for i, j in empty_positions 
                           if (i <= 2 or i >= 12) and (j <= 2 or j >= 12)]
        if corner_positions:
            return random.choice(corner_positions)
        
        return random.choice(empty_positions)
    
    def _get_empty_positions(self, board: List[List[str]]) -> List[Tuple[int, int]]:
        """빈 위치 목록 반환"""
        positions = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == '':
                    positions.append((i, j))
        return positions
    
    def _check_winner(self, board: List[List[str]], row: int, col: int, player: str) -> bool:
        """승리 조건 체크"""
        directions = [
            [(0, 1), (0, -1)],   # 가로
            [(1, 0), (-1, 0)],   # 세로
            [(1, 1), (-1, -1)],  # 대각선 ↘↖
            [(1, -1), (-1, 1)]   # 대각선 ↙↗
        ]
        
        for dir_pair in directions:
            count = 1  # 현재 위치 포함
            
            for dr, dc in dir_pair:
                r, c = row + dr, col + dc
                while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
            
            if count >= 5:
                return True
        
        return False
    
    def get_move_analysis(self, board: List[List[str]], row: int, col: int, player: str) -> str:
        """수에 대한 AI 분석"""
        # 수를 두기 전 상태 저장
        original_board = [row[:] for row in board]
        
        # 임시로 수를 두고 분석
        board[row][col] = player
        
        # 공격 가치 평가
        attack_value = self._evaluate_position(board, row, col, player)
        
        # 방어 가치 평가 (상대방이 이 위치에 둘 경우)
        opponent = 'black' if player == 'white' else 'white'
        board[row][col] = opponent
        defense_value = self._evaluate_position(board, row, col, opponent)
        board[row][col] = player
        
        # 보드 복원
        for i in range(len(board)):
            board[i] = original_board[i][:]
        
        # 분석 결과 생성
        if attack_value >= 10000:
            return f"🎯 승리 수! 이 수로 {player}가 승리합니다."
        elif attack_value >= 1000:
            return f"⚡ 강력한 공격! {player}에게 유리한 상황을 만듭니다."
        elif defense_value >= 1000:
            return f"🛡️ 중요한 방어! 상대방의 승리를 막습니다."
        elif attack_value >= 100:
            return f"📈 좋은 공격! {player}에게 유리한 위치를 만듭니다."
        elif defense_value >= 100:
            return f"🔒 방어 수! 상대방의 공격을 막습니다."
        else:
            return f"📍 기본 수! 전략적 위치에 돌을 놓습니다."
    
    def get_difficulty_info(self) -> Dict[str, str]:
        """난이도 정보 반환"""
        info = {
            'easy': {
                'description': '초보자용 - AI가 실수할 수 있음',
                'strategy': '기본적인 수준의 수',
                'thinking_depth': f'{self.difficulty_settings["easy"]["max_depth"]}단계 전망'
            },
            'normal': {
                'description': '일반인용 - 균형잡힌 AI',
                'strategy': '공격과 방어의 균형',
                'thinking_depth': f'{self.difficulty_settings["normal"]["max_depth"]}단계 전망'
            },
            'hard': {
                'description': '숙련자용 - 강력한 AI',
                'strategy': '전략적 사고와 장기 계획',
                'thinking_depth': f'{self.difficulty_settings["hard"]["max_depth"]}단계 전망'
            },
            'expert': {
                'description': '전문가용 - 최고 수준 AI',
                'strategy': 'Minimax + Alpha-Beta Pruning',
                'thinking_depth': f'{self.difficulty_settings["expert"]["max_depth"]}단계 전망'
            }
        }
        
        return info.get(self.difficulty, info['normal'])
