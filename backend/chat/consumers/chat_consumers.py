import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import *
import time
from ..chat_redis import *
from ..tasks import send_room_list_celery


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.query_string = self.scope["query_string"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_name"]

        self.username = str(self.query_string).split('=')[1][:-1]
        self.user = await self.get_user(self.username)

        #같은 이름의 채팅방이 있는지 확인 및 생성
        self.chat_room = await self.get_or_create_room(self.room_id)
        self.room_group_name = f"chat_room_id.{self.chat_room.id}"
        
        #Redis에 접속자 저장
        await add_user_to_redis(self.room_group_name, self.user.username)
        
        #현재 채널을 그룹에 추가 + 연결 수락
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        #채팅방 입장 전송
        save_messages = await self.get_message(self.chat_room)
        users_redis = await get_users_from_redis(self.room_group_name)
        await self.channel_layer.group_send(
            self.room_group_name,{
                "type": "chat.update_users",  # 사용자 목록 갱신을 위한 이벤트
                "users": list(users_redis), # Redis에서 가져온 사용자 목록
                "message": f'{self.user.username}님이 입장 했습니다.', 
            }
        )
        await self.send(text_data=json.dumps({
                    "save_messages":save_messages
                    }))
        
        #홈화면 갱신
        send_room_list_celery.delay()

    #현제 채널 그룹에서 제거
    async def disconnect(self, close_code):
        #사용자 삭제
        users_count = await remove_user_to_redis(self.room_group_name, self.user.username)

        if users_count:
            await self.delete_room(self.chat_room.id)

        #퇴장 메시지 전송 + 접속자 리스트 갱신
        users_redis = await get_users_from_redis(self.room_group_name)
        await self.channel_layer.group_send(
            self.room_group_name,{
                "type": "chat.update_users",  # 사용자 목록 갱신을 위한 이벤트
                "users": list(users_redis), # Redis에서 가져온 사용자 목록
                "message": f'{self.user.username}님이 퇴장 했습니다.', 
            }
        )
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    #메시지 보내는 로직
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        image = text_data_json.get("image", None)
        
        #메시지 저장
        await self.create_message(chat_room=self.chat_room,
                                    sender_user=self.user,  
                                    message=message,    
                                    image=None)
        
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message",
                    "sender_user": self.user.username,
                    "message": message, 
                    "image":image}
        )


    #메시지를 JSON으로 변환
    async def chat_message(self, event):
        message = event["message"]
        sender_user = event["sender_user"]
        image = event["image"]
        
        await self.send(text_data=json.dumps({
                    "sender_user": sender_user,
                    "message": message, 
                    "image":image
                    }))
    

    #채팅방 접속자 디코딩 후 JSON으로 변환
    async def chat_update_users(self, event):
        users = event["users"]
        message = event["message"]
        users_str = [user.decode('utf-8') for user in users]
        await self.send(text_data=json.dumps({
                    "users": users_str,
                    "message": message,
                    }))


    #같은 이름의 채팅방을 가져오거난 생성
    @database_sync_to_async
    def get_or_create_room(self,room_id):
        room, created = ChatRoom.objects.get_or_create(id=room_id)
        return room
    
    #해당채팅방에 있는 유저 확인하기
    @database_sync_to_async
    def get_room_users(self,room_id):
        room = ChatRoom.objects.get(id=room_id)
        return room.users.exists()
    
    #채팅방 삭제
    @database_sync_to_async
    def delete_room(self,room_id):
        room = ChatRoom.objects.get(id=room_id)
        room.delete()

    #사용자 찾기
    @database_sync_to_async
    def get_user(self, username):
        user= User.objects.get(username=username)
        return user

    #메시지를 데이터 베이스에 저장
    @database_sync_to_async
    def create_message(self, chat_room, sender_user, message, image):
        Message.objects.create(
            chat_room=chat_room,
            sender_user=sender_user,
            content=message,
            image=image,
        )
    
    #메시지 가져오기
    @database_sync_to_async
    def get_message(self, room):
        messages = Message.objects.filter(chat_room=room).order_by('add_date')

        dict_messages =[]
        for message in messages:
            dict_messages.append({
                "sender_user": message.sender_user.username,
                "message": message.content, 
                "image": None
                })
        return dict_messages
