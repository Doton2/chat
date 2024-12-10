# 💬 Chat

## 목차
[1. 프로젝트 정보](#-프로젝트-정보)

[2. 요구 사항](#-요구-사항)

[3. 사용 설명서](#-사용-설명서)

[4. 의사 결정](#-의사-결정)

<br>

# 📄 프로젝트 정보
### 제작기간 : 
24.11.18 ~ 진행 중

### 개발자 :
김병민 

### 개발목적
WebSocket의 심화 과정과 대규모 채팅 서버 설계를 학습하고, Celery를 활용한 비동기 통신과 실시간 랭킹 구현을 통해 실시간 응답 시스템에 대한 이해를 높이는 것을 목표로 했습니다. 또한 React를 복습하며 프론트엔드와 백엔드 간의 실시간 데이터 처리에 대한 실력을 높이려 했습니다.

### 기술 스택 
Python,  Django-REST-framework,  React,  Redis,  django-Channels,  Celery

<br>

# 💬 요구 사항
1. 채팅방 입장 시 기존 채팅 내용을 조회할 수 있어야 한다.
2. 실시간 접속자 정보를 확인할 수 있어야 한다.
3. 실시간 접속자 수를 기반으로 채팅방 랭킹을 확인할 수 있어야 한다.


<br>

# 📕 사용 설명서

## 메인 화면

<details>
<summary>이미지</summary>
<div markdown="1">
 
![스크린샷 2024-12-10 20 02 58](https://github.com/user-attachments/assets/6d426cbf-d9ae-46ab-8900-4c4172929641)

</div>
</details>

1. 채팅방의 접속자 수를 기준으로 랭킹 표시
2. 채팅방을 생성일 순서대로 정렬하여 표시
3. 버튼 클릭하면 로그인 페이지로 이동
4. 채팅방 입력창이 표시되며 새로운 채팅방 생성 가능

## 채팅방 화면

<details>
<summary>이미지</summary>
<div markdown="1">
 
 ![스크린샷 2024-12-10 20 04 59](https://github.com/user-attachments/assets/a2f9e863-e2bd-469a-93f9-cdaf0845eaca)

</div>
</details>

1. 현제 채팅방에 접속 중인 사용자 목록 표시
2. 채팅 메시지 표시(기존 메시지, 입장 및 퇴장 알림 포함)
3. 메인 화면으로 이동하는 버튼
4. 사진 첨부 버튼 (추후 추가 예정)
5. 메시지 입력창

## 로그인 화면

<details>
<summary>이미지</summary>
<div markdown="1">
 
 ![스크린샷 2024-12-10 18 04 35](https://github.com/user-attachments/assets/c748d80d-cbc8-4af3-a9e3-c247c2c8e954)

</div>
</details>

1. 이메일을 통해 로그인 하며, 로그인 후 메인 화면으로 이동
2. 회원가입 화면으로 이동하며, 회원가입 완료 시 로그인 화면으로 다시 이동 

<br>

# 🤔 의사 결정

<details>
<summary>API 요청 제거로 서버 효율성 증가 </summary>
<div markdown="1">

채팅방 접속자 목록을 실시간으로 갱신하는 과정에서 빈번한 API 요청으로 DB와 서버에 과부하가 발생을 우려했습니다. 

**기존 방식**

1. 채팅방에 접속/퇴장 시 사용자 정보 DB에 업데이트
2. 다른 접속자에게 상태 업데이트

## 🛠️ 해결 방법 : SQLite → Redis 전환

DB에 직접 업데이트하던 방식을 Redis와 웹소켓으로 전환하여 접속자 상태를 관리하고 실시간으로 업데이트하도록 개선했습니다.

## 결과 

서버와의 API 요청 없이 웹소켓만으로 접속자 목록을 실시간으로 갱신이 가능했고, 연결 속도가 2.6s → 2.4s로 개선됐습니다.

[ ➡️ 자세히 보기 ](https://byeongtil.tistory.com/84)
</div>
</details>



<details>
<summary> N+1 문제 해결을 통한 요청 속도 향상 </summary>
<div markdown="1">

채팅방 리스트 조회 시, 채팅방 수에 비례해 쿼리 수가 증가하는 문제가 발생하며 요청 처리 시간이 함께 늘어났습니다.

## 원인

Django ORM의 데이터를 필요할 때마다 가져오는 지연로딩 방식으로 인해  발상한 N+1 문제였습니다. 

## 🛠️ 해결 방법해결 방법 : 즉시로딩 방식으로 해결 

지연 로딩 대신 연관된 데이터를 미리 가져오는 즉시 로딩 방식으로 전환하여 문제를 해결했습니다.

## 결과 

기존에 발생하던 N개의 쿼리에서 3개로 감소 했으면 속도도 매우 향상됐습니다.

[ ➡️ 자세히 보기 ](https://byeongtil.tistory.com/85)
</div>
</details>
 

<details>
<summary> 실시간 랭킹을 위한 웹소켓 활용 결정 과정 </summary>
<div markdown="1">

홈 화면에서 채팅방의 실시간 접속자 수와 랭킹 정보를 제공했지만, 즉각적인 반영이 이루어지지 않거나 사용자 간 데이터가 불일치하는 문제가 발생했습니다.

## 🛠️ 해결 방법 1: 홈 화면에 웹소켓 적용

웹소켓을 활용하여 접속자 정보를 실시간으로 주고받는 양방향 통신 환경을 구축했습니다. 이를 통해 즉각적인 데이터 갱신이 가능해졌습니다.

## 문제점

웹소켓 연결 상태에서는 빠른 데이터 전달이 가능했지만, 채팅방 이동 시 새로운 웹소켓 연결로 인해 약간의 지연 시간이 발생하며 데이터 갱신이 늦어지는 문제가 발생했습니다.

## 🛠️ 해결 방법 2: 채팅방 접속 후 데이터 갱신

채팅방 접속 후 Celery를 활용하여 데이터를 비동기적으로 갱신하는 방식을 도입했습니다. 이를 통해 지연 문제를 효과적으로 해결할 수 있었습니다.

[ ➡️ 자세히 보기](https://byeongtil.tistory.com/86)
</div>
</details>


