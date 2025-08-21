from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from django.utils import timezone
from django.db import transaction

from .models import GameRoom, Player, ChatMessage, GameSession

def index(request):
    """멀티플레이어 게임 메인 페이지"""
    return render(request, 'multiplayer/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_room(request):
    """게임 방 생성"""
    try:
        data = json.loads(request.body)
        room_name = data.get('roomName')
        game_type = data.get('gameType')
        max_players = data.get('maxPlayers', 4)
        difficulty = data.get('difficulty', 'normal')
        is_private = data.get('isPrivate', False)
        password = data.get('password', '')
        creator_nickname = data.get('creatorNickname')
        
        # 입력 검증
        if not all([room_name, game_type, creator_nickname]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        if game_type not in ['baseball', 'omok', 'wordchain', 'baskin31', 'gonu']:
            return JsonResponse({
                'success': False,
                'error': '지원하지 않는 게임입니다.'
            }, status=400)
        
        # 방 생성
        with transaction.atomic():
            room = GameRoom.objects.create(
                name=room_name,
                game_type=game_type,
                max_players=max_players,
                difficulty=difficulty,
                is_private=is_private,
                password=password if is_private else '',
                creator=creator_nickname,
                creator_id=str(uuid.uuid4())
            )
            
            # 방장을 첫 번째 플레이어로 추가
            creator_session_id = str(uuid.uuid4())
            creator = Player.objects.create(
                nickname=creator_nickname,
                session_id=creator_session_id,
                current_room=room,
                is_ready=True
            )
            
            # 시스템 메시지 생성
            ChatMessage.objects.create(
                room=room,
                message_type='system',
                content=f'{creator_nickname}님이 방을 생성했습니다.'
            )
        
        return JsonResponse({
            'success': True,
            'roomId': str(room.id),
            'creatorSessionId': creator_session_id,
            'message': '방이 성공적으로 생성되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'방 생성 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def join_room(request):
    """게임 방 참가"""
    try:
        data = json.loads(request.body)
        room_id = data.get('roomId')
        nickname = data.get('nickname')
        password = data.get('password', '')
        
        # 입력 검증
        if not all([room_id, nickname]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        try:
            room = GameRoom.objects.get(id=room_id)
        except GameRoom.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '방을 찾을 수 없습니다.'
            }, status=404)
        
        # 방 참가 가능 여부 확인
        if not room.can_join():
            return JsonResponse({
                'success': False,
                'error': '방에 참가할 수 없습니다.'
            }, status=400)
        
        # 비밀번호 확인
        if room.is_private and room.password != password:
            return JsonResponse({
                'success': False,
                'error': '비밀번호가 일치하지 않습니다.'
            }, status=400)
        
        # 플레이어 생성
        with transaction.atomic():
            session_id = str(uuid.uuid4())
            player = Player.objects.create(
                nickname=nickname,
                session_id=session_id,
                current_room=room
            )
            
            # 시스템 메시지 생성
            ChatMessage.objects.create(
                room=room,
                message_type='system',
                content=f'{nickname}님이 방에 참가했습니다.'
            )
        
        return JsonResponse({
            'success': True,
            'sessionId': session_id,
            'roomInfo': {
                'id': str(room.id),
                'name': room.name,
                'gameType': room.game_type,
                'difficulty': room.difficulty,
                'maxPlayers': room.max_players,
                'currentPlayers': room.get_current_players_count(),
                'creator': room.creator
            },
            'message': '방에 성공적으로 참가했습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'방 참가 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_room_list(request):
    """게임 방 목록 조회"""
    try:
        game_type = request.GET.get('gameType', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('perPage', 10))
        
        # 방 목록 조회
        rooms = GameRoom.objects.filter(room_status='waiting')
        
        if game_type:
            rooms = rooms.filter(game_type=game_type)
        
        # 페이지네이션
        start = (page - 1) * per_page
        end = start + per_page
        rooms_page = rooms[start:end]
        
        room_list = []
        for room in rooms_page:
            room_list.append({
                'id': str(room.id),
                'name': room.name,
                'gameType': room.game_type,
                'gameTypeDisplay': room.get_game_type_display(),
                'difficulty': room.difficulty,
                'maxPlayers': room.max_players,
                'currentPlayers': room.get_current_players_count(),
                'creator': room.creator,
                'isPrivate': room.is_private,
                'createdAt': room.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'rooms': room_list,
            'total': rooms.count(),
            'page': page,
            'perPage': per_page,
            'hasNext': end < rooms.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'방 목록 조회 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_room_info(request, room_id):
    """방 정보 조회"""
    try:
        room = GameRoom.objects.get(id=room_id)
        
        # 플레이어 목록
        players = []
        for player in room.players.filter(is_active=True):
            players.append({
                'id': str(player.id),
                'nickname': player.nickname,
                'isReady': player.is_ready,
                'joinedAt': player.joined_at.isoformat(),
                'isCreator': player.nickname == room.creator
            })
        
        # 채팅 메시지 (최근 50개)
        messages = []
        for msg in room.messages.order_by('-created_at')[:50]:
            messages.append({
                'id': str(msg.id),
                'type': msg.message_type,
                'content': msg.content,
                'playerNickname': msg.player.nickname if msg.player else None,
                'createdAt': msg.created_at.isoformat()
            })
        
        # 메시지 순서 뒤집기 (최신순)
        messages.reverse()
        
        room_info = {
            'id': str(room.id),
            'name': room.name,
            'gameType': room.game_type,
            'gameTypeDisplay': room.get_game_type_display(),
            'difficulty': room.difficulty,
            'maxPlayers': room.max_players,
            'currentPlayers': room.get_current_players_count(),
            'creator': room.creator,
            'isPrivate': room.is_private,
            'status': room.room_status,
            'createdAt': room.created_at.isoformat(),
            'players': players,
            'messages': messages
        }
        
        return JsonResponse({
            'success': True,
            'room': room_info
        })
        
    except GameRoom.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '방을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'방 정보 조회 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """채팅 메시지 전송"""
    try:
        data = json.loads(request.body)
        room_id = data.get('roomId')
        session_id = data.get('sessionId')
        content = data.get('content')
        message_type = data.get('messageType', 'chat')
        
        # 입력 검증
        if not all([room_id, session_id, content]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        try:
            room = GameRoom.objects.get(id=room_id)
            player = Player.objects.get(session_id=session_id, current_room=room)
        except (GameRoom.DoesNotExist, Player.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '방 또는 플레이어를 찾을 수 없습니다.'
            }, status=404)
        
        # 메시지 생성
        message = ChatMessage.objects.create(
            room=room,
            player=player,
            message_type=message_type,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(message.id),
                'type': message.message_type,
                'content': message.content,
                'playerNickname': player.nickname,
                'createdAt': message.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'메시지 전송 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def leave_room(request):
    """방 나가기"""
    try:
        data = json.loads(request.body)
        room_id = data.get('roomId')
        session_id = data.get('sessionId')
        
        # 입력 검증
        if not all([room_id, session_id]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        try:
            room = GameRoom.objects.get(id=room_id)
            player = Player.objects.get(session_id=session_id, current_room=room)
        except (GameRoom.DoesNotExist, Player.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '방 또는 플레이어를 찾을 수 없습니다.'
            }, status=404)
        
        with transaction.atomic():
            # 시스템 메시지 생성
            ChatMessage.objects.create(
                room=room,
                message_type='system',
                content=f'{player.nickname}님이 방을 나갔습니다.'
            )
            
            # 플레이어 제거
            player.current_room = None
            player.is_active = False
            player.save()
            
            # 방이 비어있으면 방 삭제
            if room.get_current_players_count() == 0:
                room.room_status = 'finished'
                room.finished_at = timezone.now()
                room.save()
        
        return JsonResponse({
            'success': True,
            'message': '방을 성공적으로 나갔습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'방 나가기 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def start_game(request):
    """게임 시작"""
    try:
        data = json.loads(request.body)
        room_id = data.get('roomId')
        session_id = data.get('sessionId')
        
        # 입력 검증
        if not all([room_id, session_id]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        try:
            room = GameRoom.objects.get(id=room_id)
            player = Player.objects.get(session_id=session_id, current_room=room)
        except (GameRoom.DoesNotExist, Player.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '방 또는 플레이어를 찾을 수 없습니다.'
            }, status=404)
        
        # 방장만 게임 시작 가능
        if player.nickname != room.creator:
            return JsonResponse({
                'success': False,
                'error': '방장만 게임을 시작할 수 있습니다.'
            }, status=400)
        
        # 모든 플레이어가 준비되었는지 확인
        active_players = room.players.filter(is_active=True)
        if active_players.count() < 2:
            return JsonResponse({
                'success': False,
                'error': '최소 2명의 플레이어가 필요합니다.'
            }, status=400)
        
        if not all(p.is_ready for p in active_players):
            return JsonResponse({
                'success': False,
                'error': '모든 플레이어가 준비되어야 합니다.'
            }, status=400)
        
        with transaction.atomic():
            # 방 상태 변경
            room.room_status = 'playing'
            room.started_at = timezone.now()
            room.save()
            
            # 게임 세션 생성
            game_session = GameSession.objects.create(
                room=room,
                game_data={
                    'player_order': [p.nickname for p in active_players],
                    'current_turn': active_players.first().nickname,
                    'game_type': room.game_type,
                    'difficulty': room.difficulty
                }
            )
            
            # 시스템 메시지 생성
            ChatMessage.objects.create(
                room=room,
                message_type='system',
                content='게임이 시작되었습니다!'
            )
        
        return JsonResponse({
            'success': True,
            'gameSessionId': str(game_session.id),
            'message': '게임이 시작되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 시작 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def toggle_ready(request):
    """준비 상태 토글"""
    try:
        data = json.loads(request.body)
        room_id = data.get('roomId')
        session_id = data.get('sessionId')
        
        # 입력 검증
        if not all([room_id, session_id]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        try:
            room = GameRoom.objects.get(id=room_id)
            player = Player.objects.get(session_id=session_id, current_room=room)
        except (GameRoom.DoesNotExist, Player.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '방 또는 플레이어를 찾을 수 없습니다.'
            }, status=404)
        
        # 준비 상태 토글
        player.is_ready = not player.is_ready
        player.save()
        
        # 시스템 메시지 생성
        status_text = "준비 완료" if player.is_ready else "준비 취소"
        ChatMessage.objects.create(
            room=room,
            message_type='system',
            content=f'{player.nickname}님이 {status_text}했습니다.'
        )
        
        return JsonResponse({
            'success': True,
            'isReady': player.is_ready,
            'message': f'{status_text}했습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'준비 상태 변경 실패: {str(e)}'
        }, status=500)
