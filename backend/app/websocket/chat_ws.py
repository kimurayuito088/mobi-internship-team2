"""
WebSocket ハンドラー: エンドユーザ・オペレータ用のチャット接続
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import SenderType
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.websocket.connection_manager import manager

router = APIRouter()
chat_service = ChatService()
auth_service = AuthService()


@router.websocket("/ws/chat/enduser/{inquiry_id}")
async def enduser_chat(websocket: WebSocket, inquiry_id: int):
    """
    エンドユーザ用WebSocketエンドポイント
    inquiry_id=0 の場合は接続時に INPUTTING の問い合わせを作成する。
    初回メッセージ送信で WAITING へ遷移する（ChatService.send_message）。
    切断時は問い合わせを終了する。
    """
    await websocket.accept()

    current_inquiry_id: int

    if inquiry_id == 0:
        # プレヒアリング開始（初回選択）時点で入力中の問い合わせを作成する
        inquiry = chat_service.create_inquiry_on_connect()
        current_inquiry_id = inquiry.id
        await manager.connect_existing(websocket, current_inquiry_id, "enduser")
    else:
        current_inquiry_id = inquiry_id
        if current_inquiry_id not in manager._connections:
            manager._connections[current_inquiry_id] = []
        from app.websocket.connection_manager import ConnectionInfo

        manager._connections[current_inquiry_id].append(
            ConnectionInfo(websocket=websocket, user_type="enduser")
        )

    await websocket.send_json({"type": "connected", "inquiry_id": current_inquiry_id})

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("type") == "message":
                content = payload.get("content", "").strip()
                if not content:
                    continue

                # 初回送信時の INPUTTING → WAITING と案内メッセージは send_message 側で行う
                await chat_service.send_message(
                    inquiry_id=current_inquiry_id,
                    sender_type=SenderType.ENDUSER,
                    content=content,
                    category_id=payload.get("category_id"),
                )
                manager.update_activity(websocket, current_inquiry_id)

            elif payload.get("type") == "close":
                # 明示的な終了
                await chat_service.close_inquiry(current_inquiry_id)
                break

    except WebSocketDisconnect:
        # タブ閉じ・切断 → 問い合わせを終了（INPUTTING 含む）
        await chat_service.close_inquiry(current_inquiry_id)
    finally:
        manager.disconnect(websocket, current_inquiry_id)


@router.websocket("/ws/chat/operator/{inquiry_id}")
async def operator_chat(websocket: WebSocket, inquiry_id: int):
    """
    オペレータ用WebSocketエンドポイント
    認証と担当確認を行ってから接続する
    """
    # Cookieからセッション検証
    session_id = websocket.cookies.get("session_id")
    operator = auth_service.get_current_operator(session_id)

    if operator is None:
        await websocket.close(code=4001, reason="認証が必要です")
        return

    # 担当者確認
    from app.services.inquiry_service import InquiryService

    inquiry_service = InquiryService()
    try:
        inquiry = inquiry_service.get_inquiry(inquiry_id)
    except Exception:
        await websocket.close(code=4004, reason="問い合わせが見つかりません")
        return

    if inquiry.assigned_operator_id != operator.id:
        await websocket.close(code=4003, reason="この問い合わせの担当ではありません")
        return

    # 接続登録
    await manager.connect(websocket, inquiry_id, "operator")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("type") == "message":
                content = payload.get("content", "").strip()
                if content:
                    await chat_service.send_message(
                        inquiry_id=inquiry_id,
                        sender_type=SenderType.OPERATOR,
                        content=content,
                        sender_name=operator.display_name,
                        operator_id=operator.id,
                    )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, inquiry_id)
