from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
from django.conf import settings
import random

from .models import WordChainGame, WordChainWord

def index(request):
    """끝말잇기 게임 메인 페이지"""
    return render(request, 'wordchain/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def start_game(request):
    """새로운 끝말잇기 게임 시작"""
    try:
        data = json.loads(request.body)
        start_word = data.get('startWord', '가나다')
        difficulty = data.get('difficulty', 'normal')
        
        # 게임 생성
        game = WordChainGame.objects.create(
            current_word=start_word,
            used_words=json.dumps([start_word]),
            game_status='playing',
            difficulty=difficulty
        )
        
        # 첫 단어 기록
        WordChainWord.objects.create(
            game=game,
            word=start_word,
            player_type='player',
            round_number=1,
            is_valid=True
        )
        
        return JsonResponse({
            'success': True,
            'gameId': game.id,
            'currentWord': start_word,
            'difficulty': difficulty
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def submit_word(request):
    """플레이어 단어 제출"""
    try:
        data = json.loads(request.body)
        game_id = data.get('gameId')
        word = data.get('word')
        
        game = WordChainGame.objects.get(id=game_id)
        
        if game.game_status != 'playing':
            return JsonResponse({
                'success': False,
                'error': '게임이 진행 중이 아닙니다.'
            }, status=400)
        
        # 단어 유효성 검사
        validation_result = validate_word(word, game.current_word, game.get_used_words_list())
        
        if not validation_result['is_valid']:
            return JsonResponse({
                'success': False,
                'error': validation_result['message'],
                'needRetry': True
            }, status=400)
        
        # 플레이어 단어 기록
        round_num = game.words.count() + 1
        WordChainWord.objects.create(
            game=game,
            word=word,
            player_type='player',
            round_number=round_num,
            is_valid=True
        )
        
        # 사용된 단어 목록 업데이트
        used_words = game.get_used_words_list()
        used_words.append(word)
        game.used_words = json.dumps(used_words)
        game.current_word = word
        game.save()
        
        # AI 차례 - 난이도에 따른 AI
        ai_word = generate_ai_word(word, used_words, game.difficulty)
        
        if ai_word:
            # AI 단어 기록
            round_num += 1
            WordChainWord.objects.create(
                game=game,
                word=ai_word,
                player_type='ai',
                round_number=round_num,
                is_valid=True
            )
            
            # 사용된 단어 목록 업데이트
            used_words.append(ai_word)
            game.used_words = json.dumps(used_words)
            game.current_word = ai_word
            game.save()
            
            return JsonResponse({
                'success': True,
                'playerWord': word,
                'aiWord': ai_word,
                'currentWord': ai_word,
                'gameOver': False,
                'aiStrategy': get_ai_strategy_description(game.difficulty)
            })
        else:
            # AI가 단어를 찾지 못함 - 플레이어 승리
            game.game_status = 'finished'
            game.winner = 'player'
            game.save()
            
            return JsonResponse({
                'success': True,
                'playerWord': word,
                'aiWord': None,
                'currentWord': word,
                'gameOver': True,
                'winner': 'player',
                'aiStrategy': 'AI가 더 이상 단어를 찾을 수 없습니다.'
            })
        
    except WordChainGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '게임을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def game_history(request):
    """게임 기록 조회"""
    games = WordChainGame.objects.filter(game_status='finished').order_by('-created_at')[:10]
    return render(request, 'wordchain/history.html', {'games': games})

# 단어 유효성 검사 강화
def validate_word(word, last_word, used_words):
    """단어 유효성 검사"""
    if not word or len(word) < 2:
        return {
            'is_valid': False,
            'message': '단어는 최소 2글자 이상이어야 합니다.'
        }
    
    # 마지막 글자로 시작하는지 확인
    if word[0] != last_word[-1]:
        return {
            'is_valid': False,
            'message': f'"{last_word}"의 마지막 글자 "{last_word[-1]}"로 시작해야 합니다.'
        }
    
    # 이미 사용된 단어인지 확인
    if word in used_words:
        return {
            'is_valid': False,
            'message': f'"{word}"는 이미 사용된 단어입니다.'
        }
    
    # 한국어 단어인지 확인 (간단한 검사)
    if not all(ord('가') <= ord(c) <= ord('힣') for c in word):
        return {
            'is_valid': False,
            'message': '한국어 단어만 사용할 수 있습니다.'
        }
    
    # 특수문자나 숫자 포함 여부 확인
    if any(c in word for c in '0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'):
        return {
            'is_valid': False,
            'message': '특수문자나 숫자는 포함할 수 없습니다.'
        }
    
    return {
        'is_valid': True,
        'message': '유효한 단어입니다.'
    }

# Claude API를 사용한 AI 단어 생성 강화
def generate_ai_word(last_word, used_words, difficulty):
    """Claude API를 사용하여 AI 단어 생성"""
    if not settings.CLAUDE_API_KEY:
        return generate_fallback_ai_word(last_word, used_words, difficulty)
    
    try:
        # 난이도별 프롬프트 설정
        difficulty_prompts = {
            'easy': '간단하고 쉬운 단어를 사용하세요.',
            'normal': '일반적인 수준의 단어를 사용하세요.',
            'hard': '어려운 단어나 고급 어휘를 사용하세요.',
            'expert': '매우 어려운 단어나 전문 용어를 사용하세요.'
        }
        
        system_prompt = f"""당신은 끝말잇기 게임의 AI입니다.
        규칙: 마지막 글자로 시작하는 단어, 2글자 이상, 한국어 단어만, 이미 사용된 단어 제외.
        난이도: {difficulty_prompts.get(difficulty, 'normal')}
        응답은 단어만 반환하세요."""
        
        prompt = f"""마지막 단어: "{last_word}" (마지막 글자: {last_word[-1]})
        이미 사용된 단어들: {', '.join(used_words[-10:])}  # 최근 10개만 표시
        난이도: {difficulty}
        
        위 조건에 맞는 새로운 단어를 제시해주세요. {difficulty_prompts.get(difficulty, '')}"""
        
        response = requests.post(
            settings.CLAUDE_API_URL,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': settings.CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': settings.CLAUDE_MODEL,
                'max_tokens': 1000,
                'messages': [
                    {'role': 'user', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data['content'][0]['text'].strip()
            
            # 결과 검증
            if (validate_word(result, last_word, used_words)['is_valid']):
                return result
        
        # API 실패 시 기본 로직 사용
        return generate_fallback_ai_word(last_word, used_words, difficulty)
        
    except Exception as e:
        print(f"Claude API 호출 실패: {e}")
        return generate_fallback_ai_word(last_word, used_words, difficulty)

def generate_fallback_ai_word(last_word, used_words, difficulty):
    """기본 로직을 사용한 AI 단어 생성 강화"""
    last_char = last_word[-1]
    
    # 난이도별 단어 목록
    difficulty_words = {
        'easy': [
            '가', '나', '다', '라', '마', '바', '사', '아', '자', '차', '카', '타', '파', '하',
            '기', '니', '리', '미', '비', '시', '이', '지', '치', '키', '피', '히',
            '구', '누', '루', '무', '부', '수', '우', '주', '추', '쿠', '투', '푸', '후',
            '글', '늘', '들', '물', '불', '술', '울', '줄', '출', '쿨', '툴', '풀', '훌'
        ],
        'normal': [
            '가족', '나무', '다리', '라면', '마음', '바다', '사랑', '아침', '자동차', '차례', '카드', '타임', '파도', '하늘',
            '기차', '니트', '리본', '미소', '비밀', '시계', '이름', '지도', '치마', '키스', '피아노', '히어로',
            '구름', '누나', '루비', '무지개', '부모', '수박', '우산', '주소', '춤추다', '쿠키', '투명', '풍경', '후회'
        ],
        'hard': [
            '가로수', '나비효과', '다문화', '라틴어', '마이너', '바이러스', '사이버', '아이템', '자연스럽', '차별화', '카테고리', '타임라인', '파라미터', '하이브리드',
            '기계학습', '니트로', '리더십', '미스터리', '비즈니스', '시스템', '이데올로기', '지식경제', '치유효과', '키보드', '피아니스트', '히스토리'
        ],
        'expert': [
            '가상현실', '나노기술', '다차원적', '라디오방송', '마이크로프로세서', '바이오테크놀로지', '사이버스페이스', '아이덴티티', '자연과학', '차세대기술', '카테고리이론', '타임머신', '파라다이스', '하이퍼텍스트'
        ]
    }
    
    # 난이도에 따른 단어 선택
    available_words = difficulty_words.get(difficulty, difficulty_words['normal'])
    
    # 마지막 글자로 시작하는 단어들 중 사용되지 않은 것 선택
    valid_words = [word for word in available_words 
                  if word.startswith(last_char) and word not in used_words]
    
    if valid_words:
        return random.choice(valid_words)
    
    # 해당 난이도에서 단어를 찾지 못한 경우, 낮은 난이도에서 찾기
    for diff in ['normal', 'easy']:
        if diff != difficulty:
            fallback_words = difficulty_words.get(diff, [])
            valid_words = [word for word in fallback_words 
                          if word.startswith(last_char) and word not in used_words]
            if valid_words:
                return random.choice(valid_words)
    
    return None

def get_ai_strategy_description(difficulty):
    """AI 전략 설명 반환"""
    strategies = {
        'easy': 'AI가 간단한 단어를 사용했습니다.',
        'normal': 'AI가 일반적인 단어를 사용했습니다.',
        'hard': 'AI가 어려운 단어를 사용했습니다.',
        'expert': 'AI가 매우 어려운 단어를 사용했습니다.'
    }
    return strategies.get(difficulty, 'AI가 단어를 선택했습니다.')
