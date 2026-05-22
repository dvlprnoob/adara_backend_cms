from datetime import datetime

import anyio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from api.deps import role_required
from core.security import ALGORITHM, SECRET_KEY
from db.session import SessionLocal, get_db
from models.chat import ChatMessage, ChatThread
from models.user import User
from schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatThreadDetail, ChatThreadSummary

router = APIRouter()


class ChatConnectionManager:
    def __init__(self):
        self.admin_connections: set[WebSocket] = set()

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.add(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        self.admin_connections.discard(websocket)

    async def broadcast_admin(self, payload: dict):
        disconnected = []
        for websocket in self.admin_connections:
            try:
                await websocket.send_json(jsonable_encoder(payload))
            except RuntimeError:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect_admin(websocket)


chat_connections = ChatConnectionManager()


def get_or_create_thread(db: Session, resident: User) -> ChatThread:
    thread = db.query(ChatThread).filter(ChatThread.resident_id == resident.id).first()
    if thread:
        return thread

    thread = ChatThread(resident_id=resident.id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def message_response(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        sender_id=message.sender_id,
        sender_name=message.sender.name if message.sender else "-",
        sender_role=message.sender_role,
        message=message.message,
        created_at=message.created_at,
    )


def thread_summary(thread: ChatThread, viewer_role: str) -> ChatThreadSummary:
    last_message = thread.messages[-1] if thread.messages else None
    unread_count = 0

    for message in thread.messages:
        if viewer_role in ["admin", "super_admin"] and not message.is_read_by_admin:
            unread_count += 1
        if viewer_role == "resident" and not message.is_read_by_resident:
            unread_count += 1

    return ChatThreadSummary(
        id=thread.id,
        resident_id=thread.resident_id,
        resident_name=thread.resident.name if thread.resident else "-",
        resident_email=thread.resident.email if thread.resident else "-",
        status=thread.status,
        last_message=last_message.message if last_message else None,
        last_message_at=last_message.created_at if last_message else None,
        unread_count=unread_count,
    )


def mark_read(db: Session, thread: ChatThread, viewer_role: str):
    for message in thread.messages:
        if viewer_role in ["admin", "super_admin"]:
            message.is_read_by_admin = True
        if viewer_role == "resident":
            message.is_read_by_resident = True
    db.commit()


def clean_message(payload: ChatMessageCreate) -> str:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return message


def websocket_user(websocket: WebSocket, db: Session) -> User | None:
    token = websocket.query_params.get("token") or websocket.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None

    return user


def chat_event_payload(db: Session, thread_id: int, message: ChatMessage) -> dict:
    thread = (
        db.query(ChatThread)
        .options(joinedload(ChatThread.resident), joinedload(ChatThread.messages).joinedload(ChatMessage.sender))
        .filter(ChatThread.id == thread_id)
        .first()
    )
    return {
        "type": "message_created",
        "thread": thread_summary(thread, "admin"),
        "message": message_response(message),
    }


def broadcast_admin_chat_event(payload: dict):
    try:
        anyio.from_thread.run(chat_connections.broadcast_admin, payload)
    except RuntimeError:
        pass


@router.websocket("/ws/admin")
async def admin_chat_websocket(websocket: WebSocket):
    db = SessionLocal()
    try:
        user = websocket_user(websocket, db)
        if not user or user.role.name not in ["admin", "super_admin"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await chat_connections.connect_admin(websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        chat_connections.disconnect_admin(websocket)
    finally:
        db.close()


@router.get("/threads", response_model=list[ChatThreadSummary])
def get_threads(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    threads = (
        db.query(ChatThread)
        .options(joinedload(ChatThread.resident), joinedload(ChatThread.messages).joinedload(ChatMessage.sender))
        .order_by(ChatThread.updated_at.desc())
        .all()
    )
    return [thread_summary(thread, current_user.role.name) for thread in threads]


@router.get("/threads/{thread_id}", response_model=ChatThreadDetail)
def get_thread_detail(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    thread = (
        db.query(ChatThread)
        .options(joinedload(ChatThread.resident), joinedload(ChatThread.messages).joinedload(ChatMessage.sender))
        .filter(ChatThread.id == thread_id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Chat thread not found")

    mark_read(db, thread, current_user.role.name)
    db.refresh(thread)
    summary = thread_summary(thread, current_user.role.name)
    return ChatThreadDetail(**summary.dict(), messages=[message_response(message) for message in thread.messages])


@router.post("/threads/{thread_id}/messages", response_model=ChatMessageResponse)
def admin_send_message(
    thread_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Chat thread not found")

    message = ChatMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        sender_role=current_user.role.name,
        message=clean_message(payload),
        is_read_by_admin=True,
        is_read_by_resident=False,
    )
    thread.updated_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    broadcast_admin_chat_event(chat_event_payload(db, thread.id, message))
    return message_response(message)


@router.get("/my-thread", response_model=ChatThreadDetail)
def get_my_thread(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident"])),
):
    thread = get_or_create_thread(db, current_user)
    thread = (
        db.query(ChatThread)
        .options(joinedload(ChatThread.resident), joinedload(ChatThread.messages).joinedload(ChatMessage.sender))
        .filter(ChatThread.id == thread.id)
        .first()
    )
    mark_read(db, thread, current_user.role.name)
    db.refresh(thread)
    summary = thread_summary(thread, current_user.role.name)
    return ChatThreadDetail(**summary.dict(), messages=[message_response(message) for message in thread.messages])


@router.post("/my-thread/messages", response_model=ChatMessageResponse)
def resident_send_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident"])),
):
    thread = get_or_create_thread(db, current_user)
    message = ChatMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        sender_role=current_user.role.name,
        message=clean_message(payload),
        is_read_by_admin=False,
        is_read_by_resident=True,
    )
    thread.updated_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    broadcast_admin_chat_event(chat_event_payload(db, thread.id, message))
    return message_response(message)
