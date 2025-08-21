from django.db import models
from django.contrib.auth.models import User

class WordChainGame(models.Model):
    """끝말잇기 게임 모델"""
    GAME_STATUS_CHOICES = [
        ('waiting', '대기 중'),
        ('playing', '진행 중'),
        ('finished', '종료'),
    ]
    
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    current_word = models.CharField(max_length=50)  # 현재 단어
    used_words = models.TextField(default='[]')    # 사용된 단어들 (JSON)
    game_status = models.CharField(max_length=20, choices=GAME_STATUS_CHOICES, default='waiting')
    winner = models.CharField(max_length=20, null=True, blank=True)  # 승자
    difficulty = models.CharField(max_length=20, default='normal')  # 난이도
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"끝말잇기 게임 {self.id} - {self.player.username if self.player else '게스트'}"
    
    def get_used_words_list(self):
        """사용된 단어 리스트 반환"""
        import json
        try:
            return json.loads(self.used_words)
        except:
            return []

class WordChainWord(models.Model):
    """끝말잇기 단어 기록 모델"""
    game = models.ForeignKey(WordChainGame, on_delete=models.CASCADE, related_name='words')
    player_type = models.CharField(max_length=20)  # player 또는 ai
    word = models.CharField(max_length=50)         # 단어
    round_number = models.IntegerField()           # 라운드 번호
    is_valid = models.BooleanField(default=True)   # 유효한 단어인지 여부
    validation_message = models.CharField(max_length=100, blank=True)  # 검증 메시지
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['round_number']
    
    def __str__(self):
        return f"라운드 {self.round_number}: {self.player_type} - {self.word}"
