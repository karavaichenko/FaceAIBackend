from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, String, DateTime
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from src.schemas.schemas import LogResponse, UserResponse


class AbstractModel(DeclarativeBase):
    pass

class EmployeeModel(AbstractModel):
    __tablename__ = 'employees'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    info: Mapped[str] = mapped_column(String(200))
    photo_url: Mapped[str] = mapped_column(String, nullable=True)
    is_access: Mapped[bool] = mapped_column()

    access_logs: Mapped[list["AccessLogModel"]] = relationship(back_populates="employee")

class AccessLogModel(AbstractModel):
    __tablename__ = "access_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'))
    timestamp: Mapped[datetime] = mapped_column()
    is_known: Mapped[bool] = mapped_column()

    employee: Mapped["EmployeeModel"] = relationship(back_populates="access_logs")

    def to_schema(self):
        return LogResponse(id=self.id, name=self.employee.name, access=self.is_known, time=str(self.timestamp))

class AccessLayerModel(AbstractModel):
    __tablename__ = "access_layers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30))

class UserModel(AbstractModel):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column()
    access_layer_id: Mapped[int] = mapped_column(ForeignKey('access_layers.id'))

    def to_schema(self):
        return UserResponse(id=self.id, login=self.login, accessLayer=self.access_layer_id)
