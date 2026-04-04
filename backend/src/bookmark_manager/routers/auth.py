from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User, UserCreate, UserResponse, UserLogin, Token
from bookmark_manager.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    # Validate password length
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    # Check if user exists
    statement = select(User).where(User.email == user_data.email)
    result = await session.execute(statement)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    statement = select(User).where(User.username == user_data.username)
    result = await session.execute(statement)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == credentials.email)
    result = await session.execute(statement)
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)
