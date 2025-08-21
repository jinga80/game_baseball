from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class GameRoom(models.Model):
    """게임 방 모델"""
    GAME_TYPES = [
        ('baseball', '숫자야구'),
        ('omok', '오목'),
        ('wordchain', '끝말잇기'),
        ('baskin31', '바스킨31'),
        ('gonu', '고누'),
    ]
    
    ROOM_STATUS = [
        ('waiting', '대기 중'),
        ('playing', '게임 중'),
        ('finished', '종료'),
    ]
    
    # 기본 정보
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="방 이름")
    game_type = models.CharField(max_length=20, choices=GAME_TYPES, help_text="게임 종류")
    room_status = models.CharField(max_length=20, choices=ROOM_STATUS, default='waiting')
    
    # 게임 설정
    max_players = models.IntegerField(default=4, help_text="최대 플레이어 수")
    difficulty = models.CharField(max_length=20, default='normal', help_text="게임 난이도")
    is_private = models.BooleanField(default=False, help_text="비공개 방 여부")
    password = models.CharField(max_length=100, blank=True, null=True, help_text="방 비밀번호")
    
    # 생성자 정보
    creator = models.CharField(max_length=100, help_text="방장 닉네임", default="Unknown")
    creator_id = models.CharField(max_length=100, help_text="방장 ID", default="")
    
    # 시간 정보
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_game_type_display()})"
    
    def get_current_players_count(self):
        """현재 플레이어 수 반환"""
        return self.players.filter(is_active=True).count()
    
    def is_full(self):
        """방이 가득 찼는지 확인"""
        return self.get_current_players_count() >= self.max_players
    
    def can_join(self):
        """참가 가능한지 확인"""
        return (self.room_status == 'waiting' and 
                not self.is_full() and 
                self.room_status != 'finished')

class Player(models.Model):
    """플레이어 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nickname = models.CharField(max_length=50, help_text="플레이어 닉네임")
    session_id = models.CharField(max_length=100, unique=True, help_text="세션 ID")
    
    # 게임 방 정보
    current_room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players', null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="활성 상태")
    is_ready = models.BooleanField(default=False, help_text="준비 상태")
    
    # 게임 통계
    total_games = models.IntegerField(default=0, help_text="총 게임 수")
    wins = models.IntegerField(default=0, help_text="승리 수")
    losses = models.IntegerField(default=0, help_text="패배 수")
    
    # 시간 정보
    joined_at = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.nickname} ({self.session_id[:8]})"
    
    def update_stats(self, won: bool):
        """게임 통계 업데이트"""
        self.total_games += 1
        if won:
            self.wins += 1
        else:
            self.losses += 1
        self.save()
    
    def get_win_rate(self):
        """승률 계산"""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100

class ChatMessage(models.Model):
    """채팅 메시지 모델"""
    MESSAGE_TYPES = [
        ('chat', '일반 채팅'),
        ('system', '시스템 메시지'),
        ('game', '게임 관련'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='messages')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    
    # 메시지 내용
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='chat')
    content = models.TextField(help_text="메시지 내용")
    
    # 시간 정보
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        if self.player:
            return f"{self.player.nickname}: {self.content[:50]}"
        return f"System: {self.content[:50]}"

class GameSession(models.Model):
    """게임 세션 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.OneToOneField(GameRoom, on_delete=models.CASCADE, related_name='game_session')
    
    # 게임 상태
    game_data = models.JSONField(default=dict, help_text="게임 데이터")
    current_turn = models.CharField(max_length=100, null=True, blank=True, help_text="현재 차례 플레이어")
    
    # 게임 진행 정보
    round_number = models.IntegerField(default=1, help_text="현재 라운드")
    max_rounds = models.IntegerField(default=10, help_text="최대 라운드")
    
    # 시간 정보
    started_at = models.DateTimeField(default=timezone.now)
    last_action_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Game Session {self.id} - {self.room.name}"
    
    def update_game_data(self, new_data: dict):
        """게임 데이터 업데이트"""
        self.game_data.update(new_data)
        self.last_action_at = timezone.now()
        self.save()
    
    def get_player_order(self):
        """플레이어 순서 반환"""
        return self.game_data.get('player_order', [])
    
    def next_turn(self):
        """다음 차례로 넘어가기"""
        player_order = self.get_player_order()
        if not player_order:
            return
        
        current_index = player_order.index(self.current_turn) if self.current_turn in player_order else -1
        next_index = (current_index + 1) % len(player_order)
        self.current_turn = player_order[next_index]
        
        if next_index == 0:  # 한 바퀴 돌았으면 라운드 증가
            self.round_number += 1
        
        self.save()
