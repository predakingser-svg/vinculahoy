from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from app.database import get_db
from app.models.user import User
from app.models.location import ChatMessage, WorkCenter
from app.schemas.location import ChatMessageCreate, ChatMessageResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Mensajería & Vinculación"])


@router.post("/message", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Envía un mensaje de contacto, vinculación o postulación entre un aprendiz y un centro.
    """
    if payload.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No es posible enviarse un mensaje a sí mismo"
        )

    # Validar que el destinatario exista
    receiver = await db.scalar(select(User).where(User.id == payload.receiver_id))
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario destinatario no existe"
        )

    # Validar centro si viene especificado
    if payload.center_id:
        center_exists = await db.scalar(select(WorkCenter).where(WorkCenter.id == payload.center_id))
        if not center_exists:
            payload.center_id = None

    message = ChatMessage(
        sender_id=current_user.id,
        receiver_id=payload.receiver_id,
        center_id=payload.center_id,
        content=payload.content,
        is_read=False
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/history/{other_user_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    other_user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el historial de conversación en orden cronológico entre el usuario autenticado y otro participante.
    """
    stmt = (
        select(ChatMessage)
        .where(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == other_user_id),
                and_(ChatMessage.sender_id == other_user_id, ChatMessage.receiver_id == current_user.id)
            )
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return result.all()
