from django.db import models
from django.contrib.auth.models import User

class OmokGame(models.Model):
    """오목 게임 모델"""
    GAME_STATUS_CHOICES = [
        ('waiting', '대기 중'),
        ('playing', '진행 중'),
        ('finished', '종료'),
    ]
    
    GAME_MODE_CHOICES = [
        ('ai', 'AI와 대결'),
        ('friend', '친구와 대결'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', '쉬움'),
        ('normal', '보통'),
        ('hard', '어려움'),
        ('expert', '전문가'),
    ]
    
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    game_mode = models.CharField(max_length=20, choices=GAME_MODE_CHOICES, default='ai')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='normal')
    board_state = models.TextField(default='[["" for _ in range(15)] for _ in range(15)]')  # 보드 상태 (JSON)
    current_player = models.CharField(max_length=20, default='black')  # black 또는 white
    game_status = models.CharField(max_length=20, choices=GAME_STATUS_CHOICES, default='waiting')
    winner = models.CharField(max_length=20, null=True, blank=True)  # 승자
    ai_strategy = models.TextField(blank=True)  # AI 전략 설명
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"오목 게임 {self.id} - {self.player.username if self.player else '게스트'} ({self.game_mode})"
    
    def get_board_state(self):
        """보드 상태 반환"""
        import json
        try:
            return json.loads(self.board_state)
        except:
            return [["" for _ in range(15)] for _ in range(15)]

class OmokMove(models.Model):
    """오목 이동 기록 모델"""
    game = models.ForeignKey(OmokGame, on_delete=models.CASCADE, related_name='moves')
    player_type = models.CharField(max_length=20)  # black 또는 white
    row = models.IntegerField()                    # 행
    col = models.IntegerField()                    # 열
    round_number = models.IntegerField()           # 라운드 번호
    ai_analysis = models.TextField(blank=True)    # AI 분석 결과
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['round_number']
    
    def __str__(self):
        return f"라운드 {self.round_number}: {self.player_type} - ({self.row}, {self.col})"
