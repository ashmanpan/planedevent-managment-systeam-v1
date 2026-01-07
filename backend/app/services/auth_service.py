from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, Token
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def create_tokens(self, user: User) -> Token:
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return Token(access_token=access_token, refresh_token=refresh_token)

    def get_all_users(self) -> list[User]:
        return self.db.query(User).all()

    def update_user_role(self, user_id: UUID, role: UserRole) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_status(self, user_id: UUID, is_active: bool) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user
