from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
import random
import uuid
from django.utils import timezone
from django.db import transaction

from .models import BaseballGame, BaseballGuess, AIPlayer
from .ai_logic import AdvancedAIPlayer

# AI 플레이어 인스턴스들을 저장하는 전역 딕셔너리
ai_players = {}

def index(request):
    """숫자야구 게임 메인 페이지"""
    return render(request, 'baseball/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def start_game(request):
    """새로운 게임 시작 - 서버에서 모든 로직 관리"""
    try:
        data = json.loads(request.body)
        digit_count = int(data.get('digitCount', 3))
        difficulty = data.get('difficulty', 'normal')
        
        # 입력 검증
        if digit_count not in [3, 4, 5]:
            return JsonResponse({
                'success': False,
                'error': '자릿수는 3, 4, 5 중 하나여야 합니다.'
            }, status=400)
        
        if difficulty not in ['easy', 'normal', 'hard', 'expert']:
            return JsonResponse({
                'success': False,
                'error': '잘못된 난이도입니다.'
            }, status=400)
        
        # 고유한 플레이어 ID 생성
        player_id = str(uuid.uuid4())
        
        # 정답 숫자 생성 (서버에서 관리)
        secret_number = generate_secret_number(digit_count, difficulty)
        
        # AI 플레이어 초기화
        ai_player = AdvancedAIPlayer(difficulty)
        ai_player.initialize_game(digit_count)
        ai_players[player_id] = ai_player
        
        # 게임 생성
        with transaction.atomic():
            game = BaseballGame.objects.create(
                secret_number=secret_number,
                digit_count=digit_count,
                difficulty=difficulty,
                game_status='playing',
                player_id=player_id,
                ai_opponent=True,
                started_at=timezone.now()
            )
        
        return JsonResponse({
            'success': True,
            'gameId': game.id,
            'playerId': player_id,
            'digitCount': digit_count,
            'difficulty': difficulty,
            'maxRounds': game.max_rounds,
            'message': f'{difficulty} 난이도의 {digit_count}자리 숫자야구 게임이 시작되었습니다!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 시작 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def make_guess(request):
    """숫자 추측 - 서버에서 모든 검증 및 AI 처리"""
    try:
        data = json.loads(request.body)
        game_id = data.get('gameId')
        player_id = data.get('playerId')
        guess_number = data.get('guessNumber')
        
        # 입력 검증
        if not all([game_id, player_id, guess_number]):
            return JsonResponse({
                'success': False,
                'error': '필수 정보가 누락되었습니다.'
            }, status=400)
        
        # 게임 조회
        try:
            game = BaseballGame.objects.get(id=game_id)
        except BaseballGame.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '게임을 찾을 수 없습니다.'
            }, status=404)
        
        # 게임 상태 확인
        if game.game_status != 'playing':
            return JsonResponse({
                'success': False,
                'error': '게임이 진행 중이 아닙니다.'
            }, status=400)
        
        # 플레이어 ID 확인
        if game.player_id != player_id:
            return JsonResponse({
                'success': False,
                'error': '잘못된 플레이어 ID입니다.'
            }, status=400)
        
        # 추측 숫자 검증
        validation_result = validate_guess(guess_number, game.digit_count)
        if not validation_result['valid']:
            return JsonResponse({
                'success': False,
                'error': validation_result['error']
            }, status=400)
        
        # 추측 결과 계산 (서버에서)
        strikes, balls = calculate_result(guess_number, game.secret_number)
        
        # AI 힌트 생성
        ai_player = ai_players.get(player_id)
        ai_hint = ""
        if ai_player:
            ai_hint = ai_player.get_hint(guess_number, {'strikes': strikes, 'balls': balls})
            # AI 지식 업데이트
            ai_player.update_knowledge(guess_number, {'strikes': strikes, 'balls': balls})
        
        # 추측 기록 저장
        with transaction.atomic():
            guess = BaseballGuess.objects.create(
                game=game,
                guess_number=guess_number,
                strikes=strikes,
                balls=balls,
                round_number=game.current_round,
                ai_hint=ai_hint
            )
            
            # 게임 상태 업데이트
            game.current_round += 1
            
            # 승리 체크
            if strikes == game.digit_count:
                game.game_status = 'finished'
                game.winner = 'player'
                game.finished_at = timezone.now()
            elif game.current_round > game.max_rounds:
                game.game_status = 'finished'
                game.winner = 'ai'
                game.finished_at = timezone.now()
            
            game.save()
        
        # AI 차례 처리 (자동)
        ai_guess_result = None
        if game.game_status == 'playing' and ai_player:
            ai_guess_result = process_ai_turn(game, ai_player)
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'strikes': strikes,
            'balls': balls,
            'gameOver': game.game_status == 'finished',
            'winner': game.winner,
            'currentRound': game.current_round,
            'aiHint': ai_hint,
            'difficulty': game.difficulty,
            'remainingRounds': game.get_remaining_rounds()
        }
        
        # 게임 종료 시 정답 공개
        if game.game_status == 'finished':
            response_data['secretNumber'] = game.secret_number
            response_data['totalRounds'] = game.current_round - 1
        
        # AI 추측 결과가 있으면 추가
        if ai_guess_result:
            response_data['aiGuess'] = ai_guess_result
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'추측 처리 실패: {str(e)}'
        }, status=500)

def validate_guess(guess_number: str, digit_count: int) -> dict:
    """추측 숫자 검증"""
    if not guess_number.isdigit():
        return {'valid': False, 'error': '숫자만 입력해주세요.'}
    
    if len(guess_number) != digit_count:
        return {'valid': False, 'error': f'{digit_count}자리 숫자를 입력해주세요.'}
    
    if len(set(guess_number)) != len(guess_number):
        return {'valid': False, 'error': '중복되지 않는 숫자를 입력해주세요.'}
    
    if guess_number[0] == '0':
        return {'valid': False, 'error': '첫 번째 숫자는 0이 될 수 없습니다.'}
    
    return {'valid': True}

def calculate_result(guess: str, secret: str) -> tuple:
    """스트라이크와 볼 계산"""
    strikes = 0
    balls = 0
    
    for i in range(len(guess)):
        if guess[i] == secret[i]:
            strikes += 1
        elif guess[i] in secret:
            balls += 1
    
    return strikes, balls

def generate_secret_number(digit_count: int, difficulty: str) -> str:
    """난이도에 따른 정답 숫자 생성"""
    if difficulty == 'easy':
        # 쉬운 난이도: 연속된 숫자나 예측 가능한 패턴
        if digit_count == 3:
            patterns = ['123', '234', '345', '456', '567', '678', '789']
        elif digit_count == 4:
            patterns = ['1234', '2345', '3456', '4567', '5678', '6789']
        elif digit_count == 5:
            patterns = ['12345', '23456', '34567', '45678', '56789']
        
        return random.choice(patterns)
    
    elif difficulty == 'normal':
        # 보통 난이도: 랜덤하지만 예측 가능한 패턴
        return generate_random_number(digit_count)
    
    elif difficulty == 'hard':
        # 어려운 난이도: 복잡한 패턴
        return generate_complex_number(digit_count)
    
    else:  # expert
        # 전문가 난이도: 가장 복잡한 패턴
        return generate_expert_number(digit_count)

def generate_random_number(digit_count: int) -> str:
    """기본 랜덤 숫자 생성"""
    numbers = list(range(1, 10))  # 0 제외
    result = []
    
    for _ in range(digit_count):
        num = random.choice(numbers)
        result.append(str(num))
        numbers.remove(num)
    
    return ''.join(result)

def generate_complex_number(digit_count: int) -> str:
    """복잡한 패턴의 숫자 생성"""
    # 홀수와 짝수를 섞어서 생성
    odds = [1, 3, 5, 7, 9]
    evens = [0, 2, 4, 6, 8]
    
    result = []
    for i in range(digit_count):
        if i == 0:  # 첫 번째는 0이 될 수 없음
            num = random.choice(odds)
        else:
            if random.random() < 0.6:  # 60% 확률로 홀수
                num = random.choice(odds)
            else:
                num = random.choice(evens)
        
        if num not in result:
            result.append(num)
        else:
            # 중복되면 다른 숫자 선택
            available = [n for n in (odds + evens) if n not in result]
            if available:
                num = random.choice(available)
        
        result.append(num)
    
    return ''.join(map(str, result[:digit_count]))

def generate_expert_number(digit_count: int) -> str:
    """전문가 난이도 숫자 생성"""
    # 가장 복잡한 패턴: 소수, 제곱수 등을 활용
    if digit_count == 3:
        # 소수 패턴 활용
        primes = [2, 3, 5, 7]
        non_primes = [1, 4, 6, 8, 9]
        
        result = []
        for i in range(digit_count):
            if i == 0:
                num = random.choice(non_primes)  # 첫 번째는 소수가 아닌 수
            else:
                if random.random() < 0.7:  # 70% 확률로 소수
                    num = random.choice(primes)
                else:
                    num = random.choice(non_primes)
            
            if num not in result:
                result.append(num)
            else:
                available = [n for n in (primes + non_primes) if n not in result]
                if available:
                    num = random.choice(available)
            
            result.append(num)
        
        return ''.join(map(str, result[:digit_count]))
    
    else:
        # 4자리 이상은 더 복잡한 패턴
        return generate_complex_number(digit_count)

def process_ai_turn(game: BaseballGame, ai_player: AdvancedAIPlayer) -> dict:
    """AI 차례 처리"""
    try:
        # AI가 추측할 숫자 생성
        ai_guess = ai_player.make_guess()
        
        # AI 추측 결과 계산
        strikes, balls = calculate_result(ai_guess, game.secret_number)
        
        # AI 추측 기록 저장
        with transaction.atomic():
            BaseballGuess.objects.create(
                game=game,
                guess_number=ai_guess,
                strikes=strikes,
                balls=balls,
                round_number=game.current_round,
                ai_hint="AI의 추측입니다."
            )
            
            # 게임 상태 업데이트
            game.current_round += 1
            
            # AI 승리 체크
            if strikes == game.digit_count:
                game.game_status = 'finished'
                game.winner = 'ai'
                game.finished_at = timezone.now()
            elif game.current_round > game.max_rounds:
                game.game_status = 'finished'
                game.winner = 'player'
                game.finished_at = timezone.now()
            
            game.save()
        
        return {
            'guess': ai_guess,
            'strikes': strikes,
            'balls': balls,
            'gameOver': game.game_status == 'finished',
            'winner': game.winner
        }
        
    except Exception as e:
        print(f"AI 차례 처리 실패: {e}")
        return None

@csrf_exempt
@require_http_methods(["GET"])
def game_status(request, game_id):
    """게임 상태 조회"""
    try:
        game = BaseballGame.objects.get(id=game_id)
        guesses = BaseballGuess.objects.filter(game=game).order_by('round_number')
        
        game_data = {
            'id': game.id,
            'digitCount': game.digit_count,
            'difficulty': game.difficulty,
            'gameStatus': game.game_status,
            'currentRound': game.current_round,
            'maxRounds': game.max_rounds,
            'remainingRounds': game.get_remaining_rounds(),
            'winner': game.winner,
            'createdAt': game.created_at.isoformat(),
            'guesses': []
        }
        
        for guess in guesses:
            game_data['guesses'].append({
                'guessNumber': guess.guess_number,
                'strikes': guess.strikes,
                'balls': guess.balls,
                'roundNumber': guess.round_number,
                'aiHint': guess.ai_hint,
                'createdAt': guess.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'game': game_data
        })
        
    except BaseballGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '게임을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 상태 조회 실패: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def restart_game(request):
    """게임 재시작"""
    try:
        data = json.loads(request.body)
        game_id = data.get('gameId')
        player_id = data.get('playerId')
        
        # 기존 게임 종료
        try:
            old_game = BaseballGame.objects.get(id=game_id)
            if old_game.player_id == player_id:
                old_game.game_status = 'finished'
                old_game.save()
        except BaseballGame.DoesNotExist:
            pass
        
        # AI 플레이어 정리
        if player_id in ai_players:
            del ai_players[player_id]
        
        return JsonResponse({
            'success': True,
            'message': '게임이 재시작되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'게임 재시작 실패: {str(e)}'
        }, status=500)

def game_history(request):
    """게임 기록 조회"""
    games = BaseballGame.objects.filter(game_status='finished').order_by('-created_at')[:20]
    return render(request, 'baseball/history.html', {'games': games})

@csrf_exempt
@require_http_methods(["GET"])
def get_ai_statistics(request):
    """AI 통계 조회"""
    try:
        stats = {}
        for player_id, ai_player in ai_players.items():
            stats[player_id] = ai_player.get_game_statistics()
        
        return JsonResponse({
            'success': True,
            'aiStatistics': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'AI 통계 조회 실패: {str(e)}'
        }, status=500)
