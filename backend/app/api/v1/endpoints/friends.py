"""Friends system endpoints"""
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=list[schemas.FriendOut])
async def get_friends(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Получить список друзей"""
    result = await db.execute(
        select(models.Friendship)
        .options(selectinload(models.Friendship.friend))
        .where(models.Friendship.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    friendships = result.scalars().all()
    
    return [
        schemas.FriendOut(
            id=f.id,
            user_id=f.user_id,
            friend_id=f.friend_id,
            created_at=f.created_at,
            nickname=f.nickname,
            friend_username=f.friend.username,
            friend_display_name=f.friend.display_name,
            friend_avatar_url=f.friend.avatar_url,
            friend_level=f.friend.level,
            friend_xp=f.friend.xp,
            friend_is_online=False,  # TODO: implement
        )
        for f in friendships
    ]


@router.get("/requests/incoming", response_model=list[schemas.FriendRequestOut])
async def get_incoming_requests(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить входящие заявки в друзья"""
    result = await db.execute(
        select(models.FriendRequest)
        .options(
            selectinload(models.FriendRequest.from_user),
            selectinload(models.FriendRequest.to_user)
        )
        .where(
            models.FriendRequest.to_user_id == current_user.id,
            models.FriendRequest.status == "pending"
        )
        .order_by(models.FriendRequest.created_at.desc())
    )
    requests = result.scalars().all()
    
    return [
        schemas.FriendRequestOut(
            id=r.id,
            from_user_id=r.from_user_id,
            to_user_id=r.to_user_id,
            status=r.status,
            created_at=r.created_at,
            responded_at=r.responded_at,
            from_user_username=r.from_user.username,
            from_user_display_name=r.from_user.display_name,
            from_user_avatar_url=r.from_user.avatar_url,
            from_user_level=r.from_user.level,
            to_user_username=r.to_user.username,
            to_user_display_name=r.to_user.display_name,
            to_user_avatar_url=r.to_user.avatar_url,
            to_user_level=r.to_user.level,
        )
        for r in requests
    ]


@router.get("/requests/outgoing", response_model=list[schemas.FriendRequestOut])
async def get_outgoing_requests(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить исходящие заявки в друзья"""
    result = await db.execute(
        select(models.FriendRequest)
        .options(
            selectinload(models.FriendRequest.from_user),
            selectinload(models.FriendRequest.to_user)
        )
        .where(
            models.FriendRequest.from_user_id == current_user.id,
            models.FriendRequest.status == "pending"
        )
        .order_by(models.FriendRequest.created_at.desc())
    )
    requests = result.scalars().all()
    
    return [
        schemas.FriendRequestOut(
            id=r.id,
            from_user_id=r.from_user_id,
            to_user_id=r.to_user_id,
            status=r.status,
            created_at=r.created_at,
            responded_at=r.responded_at,
            from_user_username=r.from_user.username,
            from_user_display_name=r.from_user.display_name,
            from_user_avatar_url=r.from_user.avatar_url,
            from_user_level=r.from_user.level,
            to_user_username=r.to_user.username,
            to_user_display_name=r.to_user.display_name,
            to_user_avatar_url=r.to_user.avatar_url,
            to_user_level=r.to_user.level,
        )
        for r in requests
    ]


@router.post("/request/{user_id}")
async def send_friend_request(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Отправить заявку в друзья"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")
    
    # Check if target user exists
    target_user = await db.get(models.User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already friends
    existing_friendship = await db.scalar(
        select(models.Friendship).where(
            models.Friendship.user_id == current_user.id,
            models.Friendship.friend_id == user_id
        )
    )
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Already friends")
    
    # Check if request already exists
    existing_request = await db.scalar(
        select(models.FriendRequest).where(
            models.FriendRequest.from_user_id == current_user.id,
            models.FriendRequest.to_user_id == user_id,
            models.FriendRequest.status == "pending"
        )
    )
    if existing_request:
        raise HTTPException(status_code=400, detail="Request already sent")
    
    # Check if there's a pending request from the other user (auto-accept)
    reverse_request = await db.scalar(
        select(models.FriendRequest).where(
            models.FriendRequest.from_user_id == user_id,
            models.FriendRequest.to_user_id == current_user.id,
            models.FriendRequest.status == "pending"
        )
    )
    if reverse_request:
        # Auto-accept: create friendship both ways
        reverse_request.status = "accepted"
        reverse_request.responded_at = datetime.utcnow()
        
        friendship1 = models.Friendship(user_id=current_user.id, friend_id=user_id)
        friendship2 = models.Friendship(user_id=user_id, friend_id=current_user.id)
        db.add(friendship1)
        db.add(friendship2)
        await db.commit()
        
        return {"message": "Friendship created (mutual request)", "status": "accepted"}
    
    # Create new request
    request = models.FriendRequest(
        from_user_id=current_user.id,
        to_user_id=user_id,
        status="pending"
    )
    db.add(request)
    await db.commit()
    
    return {"message": "Friend request sent", "status": "pending"}


@router.post("/accept/{request_id}")
async def accept_friend_request(
    request_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Принять заявку в друзья"""
    request = await db.get(models.FriendRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Accept request
    request.status = "accepted"
    request.responded_at = datetime.utcnow()
    
    # Create friendship both ways
    friendship1 = models.Friendship(user_id=current_user.id, friend_id=request.from_user_id)
    friendship2 = models.Friendship(user_id=request.from_user_id, friend_id=current_user.id)
    db.add(friendship1)
    db.add(friendship2)
    
    await db.commit()
    
    return {"message": "Friend request accepted"}


@router.post("/reject/{request_id}")
async def reject_friend_request(
    request_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Отклонить заявку в друзья"""
    request = await db.get(models.FriendRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    request.status = "rejected"
    request.responded_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Friend request rejected"}


@router.delete("/cancel/{request_id}")
async def cancel_friend_request(
    request_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Отменить свою заявку"""
    request = await db.get(models.FriendRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.from_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    await db.delete(request)
    await db.commit()
    
    return {"message": "Friend request cancelled"}


@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Удалить из друзей"""
    # Remove both directions
    friendship1 = await db.scalar(
        select(models.Friendship).where(
            models.Friendship.user_id == current_user.id,
            models.Friendship.friend_id == friend_id
        )
    )
    friendship2 = await db.scalar(
        select(models.Friendship).where(
            models.Friendship.user_id == friend_id,
            models.Friendship.friend_id == current_user.id
        )
    )
    
    if not friendship1 and not friendship2:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    if friendship1:
        await db.delete(friendship1)
    if friendship2:
        await db.delete(friendship2)
    
    await db.commit()
    
    return {"message": "Friend removed"}


@router.put("/{friend_id}/nickname")
async def set_friend_nickname(
    friend_id: int,
    nickname: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Установить локальный ник для друга"""
    friendship = await db.scalar(
        select(models.Friendship).where(
            models.Friendship.user_id == current_user.id,
            models.Friendship.friend_id == friend_id
        )
    )
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    if len(nickname) > 50:
        raise HTTPException(status_code=400, detail="Nickname too long")
    
    friendship.nickname = nickname if nickname else None
    await db.commit()
    
    return {"message": "Nickname updated"}


@router.get("/count")
async def get_friends_count(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить количество друзей и заявок"""
    friends_count = await db.scalar(
        select(func.count()).select_from(models.Friendship).where(
            models.Friendship.user_id == current_user.id
        )
    )
    incoming_count = await db.scalar(
        select(func.count()).select_from(models.FriendRequest).where(
            models.FriendRequest.to_user_id == current_user.id,
            models.FriendRequest.status == "pending"
        )
    )
    outgoing_count = await db.scalar(
        select(func.count()).select_from(models.FriendRequest).where(
            models.FriendRequest.from_user_id == current_user.id,
            models.FriendRequest.status == "pending"
        )
    )
    
    return {
        "friends": friends_count or 0,
        "incoming_requests": incoming_count or 0,
        "outgoing_requests": outgoing_count or 0,
    }
