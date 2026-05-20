from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from api.deps import role_required
from db.session import get_db
from models.chat import ChatMessage, ChatThread
from models.user import User
from schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatThreadDetail, ChatThreadSummary

router = APIRouter()


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
    return message_response(message)
