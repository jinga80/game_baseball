import random
import re
from typing import List, Dict, Optional, Set
from collections import defaultdict

class AdvancedWordchainAI:
    """고급 끝말잇기 AI - 사전 기반 + 전략적 사고"""
    
    def __init__(self, difficulty: str = 'normal'):
        self.difficulty = difficulty
        self.used_words = set()
        self.word_history = []
        self.letter_frequency = self._create_letter_frequency()
        
        # 난이도별 설정
        self.difficulty_settings = {
            'easy': {'min_length': 2, 'max_length': 4, 'random_factor': 0.6},
            'normal': {'min_length': 3, 'max_length': 6, 'random_factor': 0.3},
            'hard': {'min_length': 4, 'max_length': 8, 'random_factor': 0.1},
            'expert': {'min_length': 5, 'max_length': 10, 'random_factor': 0.0}
        }
        
        # 설정 적용
        settings = self.difficulty_settings[difficulty]
        self.min_length = settings['min_length']
        self.max_length = settings['max_length']
        self.random_factor = settings['random_factor']
        
        # 한국어 단어 사전 (실제로는 더 큰 사전 사용)
        self.korean_words = self._load_korean_words()
        
        # 단어 길이별 분류
        self.words_by_length = defaultdict(list)
        for word in self.korean_words:
            self.words_by_length[len(word)].append(word)
    
    def _create_letter_frequency(self) -> Dict[str, int]:
        """한국어 자음/모음 빈도"""
        return {
            'ㄱ': 9, 'ㄴ': 4, 'ㄷ': 3, 'ㄹ': 3, 'ㅁ': 2, 'ㅂ': 4, 'ㅅ': 3, 'ㅇ': 1, 'ㅈ': 2, 'ㅊ': 1,
            'ㅋ': 1, 'ㅌ': 1, 'ㅍ': 1, 'ㅎ': 2, 'ㅏ': 4, 'ㅑ': 2, 'ㅓ': 4, 'ㅕ': 2, 'ㅗ': 4, 'ㅛ': 2,
            'ㅜ': 4, 'ㅠ': 2, 'ㅡ': 2, 'ㅣ': 4
        }
    
    def _load_korean_words(self) -> Set[str]:
        """한국어 단어 사전 로드"""
        # 기본 한국어 단어들 (실제로는 더 큰 사전 사용)
        words = {
            '가나다', '나비', '다람쥐', '라면', '마법', '바다', '사과', '아기', '자동차', '차량',
            '카드', '타이어', '파도', '하늘', '가방', '나무', '다리', '라디오', '마을', '바람',
            '사람', '아침', '자전거', '차고', '카메라', '타워', '파일', '하루', '가족', '나라',
            '다음', '라인', '마음', '바닥', '사랑', '아빠', '자리', '차례', '카페', '타임',
            '파티', '하나', '가수', '나이', '다음', '라면', '마음', '바다', '사과', '아기',
            '자동차', '차량', '카드', '타이어', '파도', '하늘', '가방', '나무', '다리', '라디오'
        }
        return words
    
    def get_next_word(self, last_word: str) -> Optional[str]:
        """다음 단어 생성"""
        if not last_word:
            return self._get_starting_word()
        
        # 랜덤 팩터 적용
        if random.random() < self.random_factor:
            return self._get_random_word(last_word)
        
        # 전략적 단어 선택
        return self._get_strategic_word(last_word)
    
    def _get_starting_word(self) -> str:
        """시작 단어 선택"""
        # 중간 길이의 단어 선택
        target_length = random.randint(self.min_length, self.max_length)
        available_words = self.words_by_length[target_length]
        
        if available_words:
            word = random.choice(available_words)
            self.used_words.add(word)
            self.word_history.append(word)
            return word
        
        # 기본 단어
        return '가나다'
    
    def _get_random_word(self, last_word: str) -> str:
        """랜덤 단어 선택"""
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if available_words:
            word = random.choice(available_words)
            self.used_words.add(word)
            self.word_history.append(word)
            return word
        
        # 패스
        return "패스"
    
    def _get_strategic_word(self, last_word: str) -> str:
        """전략적 단어 선택"""
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if not available_words:
            return "패스"
        
        # 전략적 평가
        best_word = None
        best_score = -float('inf')
        
        for word in available_words:
            if word in self.used_words:
                continue
            
            score = self._evaluate_word_strategy(word)
            if score > best_score:
                best_score = score
                best_word = word
        
        if best_word:
            self.used_words.add(best_word)
            self.word_history.append(best_word)
            return best_word
        
        return "패스"
    
    def _get_last_letter(self, word: str) -> str:
        """단어의 마지막 글자 추출"""
        if not word:
            return ''
        
        # 받침이 있는 경우 받침, 없는 경우 마지막 글자
        last_char = word[-1]
        
        # 받침 매핑
        batchim_map = {
            '가': 'ㄱ', '나': 'ㄴ', '다': 'ㄷ', '라': 'ㄹ', '마': 'ㅁ', '바': 'ㅂ', '사': 'ㅅ',
            '아': 'ㅇ', '자': 'ㅈ', '차': 'ㅊ', '카': 'ㅋ', '타': 'ㅌ', '파': 'ㅍ', '하': 'ㅎ'
        }
        
        return batchim_map.get(last_char, last_char)
    
    def _get_words_starting_with(self, letter: str) -> List[str]:
        """특정 글자로 시작하는 단어들 찾기"""
        words = []
        for word in self.korean_words:
            if word.startswith(letter) and word not in self.used_words:
                words.append(word)
        return words
    
    def _evaluate_word_strategy(self, word: str) -> float:
        """단어 전략 가치 평가"""
        score = 0
        
        # 길이 점수 (적당한 길이가 좋음)
        length = len(word)
        if self.min_length <= length <= self.max_length:
            score += 10
        else:
            score -= abs(length - (self.min_length + self.max_length) // 2)
        
        # 자음/모음 균형 점수
        consonant_count = sum(1 for c in word if c in 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ')
        vowel_count = sum(1 for c in word if c in 'ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ')
        
        if consonant_count > 0 and vowel_count > 0:
            score += 5
        
        # 다음 단어 가능성 점수
        last_letter = self._get_last_letter(word)
        next_word_count = len(self._get_words_starting_with(last_letter))
        score += min(next_word_count * 2, 20)  # 최대 20점
        
        # 사용된 글자 빈도 점수
        for char in word:
            if char in self.letter_frequency:
                score += self.letter_frequency[char]
        
        return score
    
    def get_hint(self, last_word: str, difficulty: str) -> str:
        """AI 힌트 생성"""
        if difficulty == 'easy':
            return self._generate_easy_hint(last_word)
        elif difficulty == 'normal':
            return self._generate_normal_hint(last_word)
        elif difficulty == 'hard':
            return self._generate_hard_hint(last_word)
        else:  # expert
            return self._generate_expert_hint(last_word)
    
    def _generate_easy_hint(self, last_word: str) -> str:
        """쉬운 난이도 힌트"""
        if not last_word:
            return "한국어 단어를 생각해보세요!"
        
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if available_words:
            hint_word = random.choice(available_words[:3])  # 처음 3개 중에서
            return f"'{last_letter}'로 시작하는 단어를 생각해보세요. 예: {hint_word}"
        else:
            return f"'{last_letter}'로 시작하는 단어가 없습니다. 패스하세요."
    
    def _generate_normal_hint(self, last_word: str) -> str:
        """보통 난이도 힌트"""
        if not last_word:
            return "3-6글자 단어를 생각해보세요."
        
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if available_words:
            word_count = len(available_words)
            return f"'{last_letter}'로 시작하는 단어가 {word_count}개 있습니다. 전략적으로 선택하세요."
        else:
            return f"'{last_letter}'로 시작하는 단어가 없습니다. 패스하세요."
    
    def _generate_hard_hint(self, last_word: str) -> str:
        """어려운 난이도 힌트"""
        if not last_word:
            return "4-8글자 단어를 생각해보세요. 자음과 모음의 균형을 고려하세요."
        
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if available_words:
            # 전략적 분석
            strategic_words = [w for w in available_words if self._evaluate_word_strategy(w) > 50]
            if strategic_words:
                return f"'{last_letter}'로 시작하는 전략적 단어가 있습니다. 다음 단어 가능성을 고려하세요."
            else:
                return f"'{last_letter}'로 시작하는 단어가 있지만 전략적 가치는 낮습니다."
        else:
            return f"'{last_letter}'로 시작하는 단어가 없습니다. 패스하세요."
    
    def _generate_expert_hint(self, last_word: str) -> str:
        """전문가 난이도 힌트"""
        if not last_word:
            return "5-10글자 단어를 생각해보세요. 최적의 전략을 구사하세요."
        
        last_letter = self._get_last_letter(last_word)
        available_words = self._get_words_starting_with(last_letter)
        
        if available_words:
            # 상세한 전략 분석
            word_scores = [(w, self._evaluate_word_strategy(w)) for w in available_words]
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            top_words = word_scores[:3]
            if top_words:
                best_word, best_score = top_words[0]
                return f"최고 점수 단어: '{best_word}' (점수: {best_score:.1f}). 전략적 가치를 분석하세요."
            else:
                return f"'{last_letter}'로 시작하는 단어가 있지만 전략적 가치는 낮습니다."
        else:
            return f"'{last_letter}'로 시작하는 단어가 없습니다. 패스하세요."
    
    def get_game_statistics(self) -> Dict[str, any]:
        """게임 통계 반환"""
        return {
            'difficulty': self.difficulty,
            'total_words': len(self.word_history),
            'used_words': len(self.used_words),
            'available_words': len(self.korean_words),
            'efficiency': len(self.used_words) / max(1, len(self.word_history))
        }
    
    def reset_game(self):
        """게임 상태 초기화"""
        self.used_words.clear()
        self.word_history.clear()
