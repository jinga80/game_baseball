import random
import itertools
from typing import List, Tuple, Dict, Set

class AdvancedAIPlayer:
    """고급 AI 플레이어 - Knuth 알고리즘 기반"""
    
    def __init__(self, difficulty: str = 'normal'):
        self.difficulty = difficulty
        self.possible_numbers = set()
        self.guess_history = []
        self.candidate_pool = set()
        self.difficulty_multipliers = {
            'easy': 0.3,      # 30% 확률로 실수
            'normal': 0.1,    # 10% 확률로 실수
            'hard': 0.05,     # 5% 확률로 실수
            'expert': 0.0     # 실수 없음
        }
    
    def initialize_game(self, digit_count: int):
        """게임 초기화"""
        self.digit_count = digit_count
        self.possible_numbers = set()
        self.guess_history = []
        
        # 가능한 모든 숫자 조합 생성
        numbers = list(range(10))
        for combo in itertools.permutations(numbers, digit_count):
            if combo[0] != 0:  # 첫 번째 숫자는 0이 될 수 없음
                self.possible_numbers.add(''.join(map(str, combo)))
        
        self.candidate_pool = self.possible_numbers.copy()
        
        # 난이도에 따른 초기 전략 설정
        if self.difficulty == 'easy':
            # 쉬운 난이도: 랜덤 시작
            self.first_guess = self._generate_random_guess()
        elif self.difficulty == 'normal':
            # 보통 난이도: 123으로 시작
            self.first_guess = '123'[:digit_count].ljust(digit_count, '0')
        elif self.difficulty == 'hard':
            # 어려운 난이도: 최적화된 시작 숫자
            self.first_guess = self._get_optimal_first_guess(digit_count)
        else:  # expert
            # 전문가 난이도: Knuth 알고리즘의 최적 첫 번째 추측
            self.first_guess = self._get_knuth_optimal_guess(digit_count)
    
    def _get_optimal_first_guess(self, digit_count: int) -> str:
        """최적화된 첫 번째 추측 생성"""
        if digit_count == 3:
            return '123'  # 3자리: 123
        elif digit_count == 4:
            return '1234'  # 4자리: 1234
        elif digit_count == 5:
            return '12345'  # 5자리: 12345
        else:
            return '1' + '0' * (digit_count - 1)
    
    def _get_knuth_optimal_guess(self, digit_count: int) -> str:
        """Knuth 알고리즘 기반 최적 첫 번째 추측"""
        if digit_count == 3:
            return '112'  # Knuth의 최적 3자리 시작
        elif digit_count == 4:
            return '1123'  # 4자리 최적화
        elif digit_count == 5:
            return '11234'  # 5자리 최적화
        else:
            return self._get_optimal_first_guess(digit_count)
    
    def make_guess(self) -> str:
        """다음 추측 생성"""
        if not self.guess_history:
            # 첫 번째 추측
            return self.first_guess
        
        # 난이도에 따른 실수 확률
        if random.random() < self.difficulty_multipliers[self.difficulty]:
            return self._generate_random_guess()
        
        # Knuth 알고리즘 기반 최적 추측
        return self._get_optimal_guess()
    
    def _get_optimal_guess(self) -> str:
        """Knuth 알고리즘 기반 최적 추측"""
        if not self.candidate_pool:
            return self._generate_random_guess()
        
        # 후보 풀이 1개면 바로 반환
        if len(self.candidate_pool) == 1:
            return list(self.candidate_pool)[0]
        
        # 최소 최대 전략: 가장 많은 정보를 제공하는 추측 선택
        best_guess = None
        min_max_group_size = float('inf')
        
        # 모든 가능한 추측에 대해 평가
        for guess in self.possible_numbers:
            max_group_size = 0
            group_counts = {}
            
            # 이 추측으로 가능한 모든 결과에 대해 그룹 크기 계산
            for candidate in self.candidate_pool:
                result = self._calculate_result(guess, candidate)
                result_key = f"{result['strikes']}S{result['balls']}B"
                
                if result_key not in group_counts:
                    group_counts[result_key] = 0
                group_counts[result_key] += 1
                
                max_group_size = max(max_group_size, group_counts[result_key])
            
            # 최대 그룹 크기가 가장 작은 추측 선택
            if max_group_size < min_max_group_size:
                min_max_group_size = max_group_size
                best_guess = guess
        
        return best_guess if best_guess else list(self.candidate_pool)[0]
    
    def _calculate_result(self, guess: str, secret: str) -> Dict[str, int]:
        """스트라이크와 볼 계산"""
        strikes = 0
        balls = 0
        
        for i in range(len(guess)):
            if guess[i] == secret[i]:
                strikes += 1
            elif guess[i] in secret:
                balls += 1
        
        return {'strikes': strikes, 'balls': balls}
    
    def update_knowledge(self, guess: str, result: Dict[str, int]):
        """추측 결과를 바탕으로 지식 업데이트"""
        self.guess_history.append({
            'guess': guess,
            'result': result
        })
        
        # 후보 풀에서 불가능한 숫자 제거
        impossible_numbers = set()
        for candidate in self.candidate_pool:
            candidate_result = self._calculate_result(guess, candidate)
            if (candidate_result['strikes'] != result['strikes'] or 
                candidate_result['balls'] != result['balls']):
                impossible_numbers.add(candidate)
        
        self.candidate_pool -= impossible_numbers
    
    def _generate_random_guess(self) -> str:
        """랜덤 추측 생성"""
        if self.candidate_pool:
            return random.choice(list(self.candidate_pool))
        
        # 후보 풀이 비어있으면 가능한 모든 숫자에서 선택
        numbers = list(range(1, 10))  # 0 제외
        result = []
        
        for _ in range(self.digit_count):
            if numbers:
                num = random.choice(numbers)
                result.append(str(num))
                numbers.remove(num)
            else:
                result.append(str(random.randint(0, 9)))
        
        return ''.join(result)
    
    def get_hint(self, guess: str, result: Dict[str, int]) -> str:
        """AI 힌트 생성"""
        if self.difficulty == 'easy':
            return self._generate_easy_hint(guess, result)
        elif self.difficulty == 'normal':
            return self._generate_normal_hint(guess, result)
        elif self.difficulty == 'hard':
            return self._generate_hard_hint(guess, result)
        else:  # expert
            return self._generate_expert_hint(guess, result)
    
    def _generate_easy_hint(self, guess: str, result: Dict[str, int]) -> str:
        """쉬운 난이도 힌트"""
        if result['strikes'] == 0 and result['balls'] == 0:
            return f"'{guess}'에 포함된 모든 숫자는 정답에 없습니다."
        elif result['strikes'] > 0:
            return f"'{guess}'의 {result['strikes']}개 숫자가 올바른 위치에 있습니다!"
        elif result['balls'] > 0:
            return f"'{guess}'의 {result['balls']}개 숫자가 정답에 포함되어 있지만 위치가 다릅니다."
        else:
            return "좋은 시도입니다! 계속 도전해보세요."
    
    def _generate_normal_hint(self, guess: str, result: Dict[str, int]) -> str:
        """보통 난이도 힌트"""
        if result['strikes'] == 0 and result['balls'] == 0:
            return f"'{guess}'의 모든 숫자를 다른 숫자로 바꿔보세요."
        elif result['strikes'] > 0:
            return f"'{guess}'의 {result['strikes']}개 숫자는 올바른 위치에 있습니다. 이 숫자들을 고정하고 나머지만 바꿔보세요."
        elif result['balls'] > 0:
            return f"'{guess}'의 {result['balls']}개 숫자는 정답에 포함되어 있습니다. 위치만 바꿔보세요."
        else:
            return "패턴을 분석해서 다음 추측을 해보세요."
    
    def _generate_hard_hint(self, guess: str, result: Dict[str, int]) -> str:
        """어려운 난이도 힌트"""
        if result['strikes'] == 0 and result['balls'] == 0:
            return f"'{guess}'는 완전히 틀렸습니다. 전략적으로 다른 범위의 숫자를 시도해보세요."
        elif result['strikes'] > 0:
            return f"'{guess}'의 {result['strikes']}개 숫자는 정확합니다. 이 정보를 바탕으로 나머지 숫자의 패턴을 추론해보세요."
        elif result['balls'] > 0:
            return f"'{guess}'의 {result['balls']}개 숫자는 정답에 포함됩니다. 위치 관계를 분석해보세요."
        else:
            return "이 결과를 바탕으로 정답의 패턴을 분석해보세요."
    
    def _generate_expert_hint(self, guess: str, result: Dict[str, int]) -> str:
        """전문가 난이도 힌트"""
        if result['strikes'] == 0 and result['balls'] == 0:
            return f"'{guess}'는 완전히 제외됩니다. 남은 후보 수: {len(self.candidate_pool)}개"
        elif result['strikes'] > 0:
            return f"'{guess}'의 {result['strikes']}개 숫자는 정확합니다. 후보 풀 크기: {len(self.candidate_pool)}개"
        elif result['balls'] > 0:
            return f"'{guess}'의 {result['balls']}개 숫자는 포함됩니다. 후보 풀 크기: {len(self.candidate_pool)}개"
        else:
            return f"정보가 축적되었습니다. 후보 풀 크기: {len(self.candidate_pool)}개"
    
    def get_game_statistics(self) -> Dict[str, any]:
        """게임 통계 반환"""
        return {
            'difficulty': self.difficulty,
            'total_guesses': len(self.guess_history),
            'candidate_pool_size': len(self.candidate_pool),
            'possible_numbers_size': len(self.possible_numbers),
            'efficiency': len(self.possible_numbers) / max(1, len(self.guess_history))
        }
