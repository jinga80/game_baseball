import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import GameRoom, RoomPlayer, ChatMessage

class MultiplayerConsumer(AsyncWebsocketConsumer):
    """멀티플레이어 게임 WebSocket 소비자"""
    
    async def connect(self):
        """WebSocket 연결"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'multiplayer_{self.room_id}'
        
        # 방이 존재하는지 확인
        if not await self.room_exists():
            await self.close()
            return
        
        # 사용자 인증 확인
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # 방에 참가 중인지 확인
        if not await self.is_room_member():
            await self.close()
            return
        
        # 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket 연결이 성공했습니다.'
        }))
    
    async def disconnect(self, close_code):
        """WebSocket 연결 해제"""
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'game_action':
                await self.handle_game_action(data)
            elif message_type == 'player_status':
                await self.handle_player_status(data)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '잘못된 JSON 형식입니다.'
            }))
    
    async def handle_chat_message(self, data):
        """채팅 메시지 처리"""
        content = data.get('content', '').strip()
        if not content:
            return
        
        # 메시지 저장
        message = await self.save_chat_message(content)
        
        # 그룹에 메시지 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': message.sender.username,
                    'senderNickname': message.sender_nickname,
                    'content': message.content,
                    'messageType': message.message_type,
                    'createdAt': message.created_at.isoformat(),
                }
            }
        )
    
    async def handle_game_action(self, data):
        """게임 액션 처리"""
        action = data.get('action')
        game_data = data.get('gameData', {})
        
        # 게임 액션을 그룹에 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_action',
                'action': action,
                'gameData': game_data,
                'player': self.scope['user'].username
            }
        )
    
    async def handle_player_status(self, data):
        """플레이어 상태 변경 처리"""
        status = data.get('status')
        
        # 플레이어 상태를 그룹에 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_status',
                'player': self.scope['user'].username,
                'status': status
            }
        )
    
    async def chat_message(self, event):
        """채팅 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def game_action(self, event):
        """게임 액션 전송"""
        await self.send(text_data=json.dumps({
            'type': 'game_action',
            'action': event['action'],
            'gameData': event['gameData'],
            'player': event['player']
        }))
    
    async def player_status(self, event):
        """플레이어 상태 전송"""
        await self.send(text_data=json.dumps({
            'type': 'player_status',
            'player': event['player'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def room_exists(self):
        """방이 존재하는지 확인"""
        try:
            return GameRoom.objects.filter(id=self.room_id).exists()
        except:
            return False
    
    @database_sync_to_async
    def is_room_member(self):
        """사용자가 방 멤버인지 확인"""
        try:
            return RoomPlayer.objects.filter(
                room_id=self.room_id,
                user=self.scope['user']
            ).exists()
        except:
            return False
    
    @database_sync_to_async
    def save_chat_message(self, content):
        """채팅 메시지 저장"""
        try:
            player = RoomPlayer.objects.get(
                room_id=self.room_id,
                user=self.scope['user']
            )
            
            message = ChatMessage.objects.create(
                room_id=self.room_id,
                sender=self.scope['user'],
                sender_nickname=player.nickname,
                message_type='chat',
                content=content
            )
            
            return message
        except Exception as e:
            print(f"채팅 메시지 저장 실패: {e}")
            return None

class GlobalChatConsumer(AsyncWebsocketConsumer):
    """전역 채팅 WebSocket 소비자"""
    
    async def connect(self):
        """WebSocket 연결"""
        self.room_group_name = 'global_chat'
        
        # 사용자 인증 확인
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '전역 채팅에 연결되었습니다.'
        }))
    
    async def disconnect(self, close_code):
        """WebSocket 연결 해제"""
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'global_chat_message':
                await self.handle_global_chat_message(data)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '잘못된 JSON 형식입니다.'
            }))
    
    async def handle_global_chat_message(self, data):
        """전역 채팅 메시지 처리"""
        content = data.get('content', '').strip()
        nickname = data.get('nickname', '').strip()
        
        if not content:
            return
        
        if not nickname:
            nickname = self.scope['user'].username
        
        # 메시지 저장
        message = await self.save_global_chat_message(content, nickname)
        
        if message:
            # 그룹에 메시지 브로드캐스트
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'global_chat_message',
                    'message': {
                        'id': message.id,
                        'sender': message.sender.username,
                        'senderNickname': message.sender_nickname,
                        'content': message.content,
                        'createdAt': message.created_at.isoformat(),
                    }
                }
            )
    
    async def global_chat_message(self, event):
        """전역 채팅 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'global_chat_message',
            'message': event['message']
        }))
    
    @database_sync_to_async
    def save_global_chat_message(self, content, nickname):
        """전역 채팅 메시지 저장"""
        try:
            from .models import ChatRoom, GlobalChatMessage
            
            # 전역 채팅방 가져오기
            global_chat, created = ChatRoom.objects.get_or_create(
                name='전역 채팅',
                defaults={'description': '모든 사용자가 참여할 수 있는 채팅방'}
            )
            
            # 메시지 저장
            message = GlobalChatMessage.objects.create(
                chat_room=global_chat,
                sender=self.scope['user'],
                sender_nickname=nickname,
                content=content
            )
            
            # 오래된 메시지 정리
            global_chat.cleanup_old_messages()
            
            return message
        except Exception as e:
            print(f"전역 채팅 메시지 저장 실패: {e}")
            return None
