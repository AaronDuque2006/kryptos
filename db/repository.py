from sqlmodel import Session, select
from models.user import User
from models.credential import Credential
from typing import List

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user: User) -> User:
        existing_user = self.get_user_by_username(user.username)
        if existing_user:
            raise ValueError("El usuario ya existe")

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_user_by_username(self, username: str) -> User | None:
        stament = select(User).where(User.username == username)
        return self.session.exec(stament).first()

class CredentialRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_credential(self, user_id: int, title: str, nonce: bytes, encrypted_payload: bytes) -> Credential:
        new_credential = Credential(
            user_id=user_id,
            title=title,
            nonce=nonce,
            encrypted_payload=encrypted_payload
        )
        self.session.add(new_credential)
        self.session.commit()
        self.session.refresh(new_credential)
        return new_credential

    def get_credentials_by_user(self, user_id: int) -> List[Credential]:
        statement = select(Credential).where(Credential.user_id == user_id)
        return list(self.session.exec(statement).all())

    def delete_credential(self, credential_id: int, user_id: int) -> bool:
        statement = select(Credential).where(
            Credential.id == credential_id,
            Credential.user_id == user_id
        )
        credential = self.session.exec(statement).first()
            
        if credential:
            self.session.delete(credential)
            self.session.commit()
            return True
        return False