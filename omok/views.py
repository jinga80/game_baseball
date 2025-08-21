from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import random
from django.utils import timezone
from typing import List, Optional, Tuple

from .models import OmokGame, OmokMove
from .advanced_ai import AdvancedOmokAI

# AI 인스턴스들을 저장하는 전역 딕셔너리
ai_instances = {}

def index(request):
    """오목 게임 메인 페이지"""
    return render(request, 'omok/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def start_game(request):
    """새로운 오목 게임 시작"""
    try:
        data = json.loads(request.body)
        game_mode = data.get('gameMode', 'ai')
        difficulty = data.get('difficulty', 'normal')
        
        # 입력 검증
        if difficulty not in ['easy', 'normal', 'hard', 'expert']:
            return JsonResponse({
                'success': False,
                'error': '잘못된 난이도입니다.'
            }, status=400)
        
        # 게임 생성
        game = OmokGame.objects.create(
            game_mode=game_mode,
            difficulty=difficulty,
            game_status='playing',
            current_player='black'
        )
        
        # AI 인스턴스 생성
        if game_mode == 'ai':
            ai_instances[game.id] = AdvancedOmokAI(difficulty)
        
        return JsonResponse({
            'success': True,
            'gameId': game.id,
            'gameMode': game_mode,
            'difficulty': difficulty,
            'message': f'{difficulty} 난이도의 오목 게임이 시작되었습니다!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 시작 실패: {str(e)}'
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def make_move(request):
    """오목 수 두기"""
    try:
        data = json.loads(request.body)
        game_id = data.get('gameId')
        row = data.get('row')
        col = data.get('col')
        player = data.get('player', 'black')
        
        # 입력 검증
        if not all([game_id, row is not None, col is not None]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        if not (0 <= row < 15 and 0 <= col < 15):
            return JsonResponse({
                'success': False,
                'error': '잘못된 위치입니다.'
            }, status=400)
        
        game = OmokGame.objects.get(id=game_id)
        
        if game.game_status != 'playing':
            return JsonResponse({
                'success': False,
                'error': '게임이 진행 중이 아닙니다.'
            }, status=400)
        
        # 보드 상태 가져오기
        board = game.get_board_state()
        
        # 이미 돌이 놓인 위치인지 확인
        if board[row][col] != '':
            return JsonResponse({
                'success': False,
                'error': '이미 돌이 놓인 위치입니다.'
            }, status=400)
        
        # 플레이어 수 기록
        board[row][col] = player
        round_num = game.moves.count() + 1
        
        # AI 분석 결과 생성
        ai_analysis = ""
        if game.game_mode == 'ai' and game.id in ai_instances:
            ai_analysis = ai_instances[game.id].get_move_analysis(board, row, col, player)
        
        OmokMove.objects.create(
            game=game,
            player_type=player,
            row=row,
            col=col,
            round_number=round_num,
            ai_analysis=ai_analysis
        )
        
        # 승리 체크
        if check_winner(board, row, col, player):
            game.game_status = 'finished'
            game.winner = player
            game.finished_at = timezone.now()
            game.save()
            
            return JsonResponse({
                'success': True,
                'gameOver': True,
                'winner': player,
                'board': board,
                'aiAnalysis': ai_analysis
            })
        
        # AI 모드이고 AI 차례인 경우
        ai_move = None
        if game.game_mode == 'ai' and player == 'black':
            ai_move = process_ai_turn(game, board)
            
            if ai_move:
                ai_row, ai_col = ai_move
                board[ai_row][ai_col] = 'white'
                
                # AI 수 기록
                round_num += 1
                ai_analysis = ""
                if game.id in ai_instances:
                    ai_analysis = ai_instances[game.id].get_move_analysis(board, ai_row, ai_col, 'white')
                
                OmokMove.objects.create(
                    game=game,
                    player_type='white',
                    row=ai_row,
                    col=ai_col,
                    round_number=round_num,
                    ai_analysis=ai_analysis
                )
                
                # AI 승리 체크
                if check_winner(board, ai_row, ai_col, 'white'):
                    game.game_status = 'finished'
                    game.winner = 'white'
                    game.finished_at = timezone.now()
                    game.save()
                    
                    return JsonResponse({
                        'success': True,
                        'gameOver': True,
                        'winner': 'white',
                        'board': board,
                        'aiMove': {'row': ai_row, 'col': ai_col},
                        'aiAnalysis': ai_analysis
                    })
        
        # 보드 상태 업데이트
        game.board_state = json.dumps(board)
        game.save()
        
        return JsonResponse({
            'success': True,
            'board': board,
            'aiMove': ai_move,
            'aiAnalysis': ai_analysis
        })
        
    except OmokGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '게임을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'수 두기 실패: {str(e)}'
        }, status=500)

def process_ai_turn(game: OmokGame, board: List[List[str]]) -> Optional[Tuple[int, int]]:
    """AI 차례 처리"""
    try:
        if game.id not in ai_instances:
            return None
        
        ai = ai_instances[game.id]
        ai_move = ai.get_best_move(board, 'white')
        
        return ai_move
        
    except Exception as e:
        print(f"AI 차례 처리 실패: {e}")
        return None

def game_history(request):
    """게임 기록 조회"""
    games = OmokGame.objects.filter(game_status='finished').order_by('-created_at')[:20]
    return render(request, 'omok/history.html', {'games': games})

# 승리 조건 체크
def check_winner(board, row, col, player):
    """오목 승리 조건 체크"""
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
            while 0 <= r < 15 and 0 <= c < 15 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
        
        if count >= 5:
            return True
    
    return False

@csrf_exempt
@require_http_methods(["GET"])
def get_ai_info(request):
    """AI 정보 조회"""
    try:
        difficulty = request.GET.get('difficulty', 'normal')
        
        if difficulty not in ['easy', 'normal', 'hard', 'expert']:
            return JsonResponse({
                'success': False,
                'error': '잘못된 난이도입니다.'
            }, status=400)
        
        # 임시 AI 인스턴스 생성하여 정보 조회
        temp_ai = AdvancedOmokAI(difficulty)
        ai_info = temp_ai.get_difficulty_info()
        
        return JsonResponse({
            'success': True,
            'aiInfo': ai_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'AI 정보 조회 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def restart_game(request):
    """게임 재시작"""
    try:
        data = json.loads(request.body)
        game_id = data.get('gameId')
        
        # 기존 게임 종료
        try:
            old_game = OmokGame.objects.get(id=game_id)
            old_game.game_status = 'finished'
            old_game.save()
            
            # AI 인스턴스 정리
            if game_id in ai_instances:
                del ai_instances[game_id]
                
        except OmokGame.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'message': '게임이 재시작되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 재시작 실패: {str(e)}'
        }, status=500)
