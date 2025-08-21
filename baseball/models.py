from django.db import models
from django.utils import timezone
import random

class BaseballGame(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', '쉬움'),
        ('normal', '보통'),
        ('hard', '어려움'),
        ('expert', '전문가'),
    ]
    
    GAME_STATUS_CHOICES = [
        ('waiting', '대기 중'),
        ('playing', '진행 중'),
        ('finished', '종료'),
    ]
    
    # 게임 기본 정보
    secret_number = models.CharField(max_length=10, help_text="정답 숫자")
    digit_count = models.IntegerField(default=3, help_text="자릿수")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='normal')
    game_status = models.CharField(max_length=10, choices=GAME_STATUS_CHOICES, default='waiting')
    
    # 게임 진행 정보
    current_round = models.IntegerField(default=1)
    max_rounds = models.IntegerField(default=20)
    current_player = models.CharField(max_length=50, null=True, blank=True)
    
    # 플레이어 정보
    player_id = models.CharField(max_length=100, null=True, blank=True)
    ai_opponent = models.BooleanField(default=True)
    
    # 게임 결과
    winner = models.CharField(max_length=50, null=True, blank=True)
    secret_number_revealed = models.BooleanField(default=False)
    
    # 시간 정보
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Baseball Game {self.id} - {self.difficulty} ({self.digit_count}자리)"
    
    def start_game(self):
        """게임 시작"""
        self.game_status = 'playing'
        self.started_at = timezone.now()
        self.save()
    
    def end_game(self, winner):
        """게임 종료"""
        self.game_status = 'finished'
        self.winner = winner
        self.finished_at = timezone.now()
        self.save()
    
    def is_finished(self):
        """게임 종료 여부 확인"""
        return self.game_status == 'finished'
    
    def get_remaining_rounds(self):
        """남은 라운드 수"""
        return max(0, self.max_rounds - self.current_round + 1)

class BaseballGuess(models.Model):
    """게임 추측 기록"""
    game = models.ForeignKey(BaseballGame, on_delete=models.CASCADE, related_name='guesses')
    guess_number = models.CharField(max_length=10, help_text="추측한 숫자")
    strikes = models.IntegerField(default=0, help_text="스트라이크 수")
    balls = models.IntegerField(default=0, help_text="볼 수")
    round_number = models.IntegerField(help_text="라운드 번호")
    ai_hint = models.TextField(blank=True, help_text="AI 힌트")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['round_number']
    
    def __str__(self):
        return f"Guess {self.guess_number} - {self.strikes}S {self.balls}B (Round {self.round_number})"

class AIPlayer(models.Model):
    """AI 플레이어 정보"""
    name = models.CharField(max_length=50, default="AI Player")
    difficulty = models.CharField(max_length=10, choices=BaseballGame.DIFFICULTY_CHOICES)
    win_count = models.IntegerField(default=0)
    loss_count = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    average_rounds = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-total_games']
    
    def __str__(self):
        return f"{self.name} ({self.difficulty})"
    
    def update_stats(self, won, rounds):
        """통계 업데이트"""
        self.total_games += 1
        if won:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        # 평균 라운드 업데이트
        if self.total_games > 0:
            self.average_rounds = ((self.average_rounds * (self.total_games - 1)) + rounds) / self.total_games
        
        self.save()
