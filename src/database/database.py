from sqlalchemy import create_engine, select, func, delete, desc, select
from sqlalchemy.orm import registry, Session

from src.database.models import AbstractModel, UserModel, EmployeeModel, AccessLogModel, AccessLayerModel

def hash_password(password: str):
    return password



class Database:

    def __init__(self, URL):
        self.URL = URL
        self.engine = create_engine(self.URL, echo=False)
        self.mapped_registry = registry()
        self.session = Session(self.engine)
        with self.session.begin():
            AbstractModel.metadata.create_all(self.engine)

        self._add_initial_data()

    def _add_initial_data(self):
        res = self.session.execute(select(AccessLayerModel.id))
        if res.first() is None:
            admin_access_layer = AccessLayerModel(id=0, name="admin")
            self.add(admin_access_layer)
            user_access_layer = AccessLayerModel(id=1, name="user")
            self.add(user_access_layer)
        res = self.session.execute(select(UserModel.id))
        if res.first() is None:
            self.create_user("admin", "admin", 0)
        res = self.session.execute(select(EmployeeModel.id))
        if res.first() is None:
            unknown_employee = EmployeeModel(id=0, name="-", info="-", photo_url="/", is_access=False)
            self.add(unknown_employee)
            known_employee = EmployeeModel(id=1, name="Каравайченко Иван", info="шеф", photo_url="/", is_access=True)
            self.add(known_employee)
        res = self.session.execute(select(AccessLogModel.id))
        if res.first() is None:
            some_logs = AccessLogModel(id=0, employee_id=0, timestamp="12-12-2024 12:25:10", is_known=False)
            self.add(some_logs)
            some_logs = AccessLogModel(id=1, employee_id=1, timestamp="12-12-2024 12:24:10", is_known=True)
            self.add(some_logs)



    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def create_user(self, login: str, password: str, access_id: int):
        res = self.session.execute(select(UserModel.login).where(UserModel.login == login))
        user = res.scalar()
        if user is not None:
            return False
        else:
            res = self.session.execute(select(UserModel.id).order_by(UserModel.id.desc()))
            id = res.scalar()
            print(id)
            if id:
                user = UserModel(id=(id + 1), login=login, access_layer_id=access_id, password=hash_password(password),
                                 verify=False)
            else:
                user = UserModel(id=1, login=login, access_layer_id=access_id, password=hash_password(password))
            self.add(user)


    def get_user(self, login):
        res = self.session.execute(select(UserModel).where(UserModel.login == login))
        user = res.scalar()
        return user

    def get_user_by_id(self, user_id):
        res = self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user = res.scalar()
        return user

    def delete_user(self, user_id):
        user = self.get_user_by_id(user_id)
        if user is not None:
            self.session.execute(delete(UserModel).where(UserModel.id == user_id))
            self.session.commit()
            return True
        else: return False

    def set_user_password(self, user_id, new_password):
        user = self.get_user_by_id(user_id)
        if user is None:
            return False
        user.password = new_password
        self.session.commit()
        return True

    def set_user_access(self, user_id, access_layer_id):
        user = self.get_user_by_id(user_id)
        if user is None: return False
        user.access_layer_id = access_layer_id
        self.session.commit()
        return True



    def get_access_logs(self, page: int, page_size: int = 10):
        stmt = select(AccessLogModel).order_by(desc(AccessLogModel.timestamp)).offset((page - 1) * page_size).limit(page_size)
        res = self.session.execute(stmt)
        logs = res.scalars().all()
        return logs

    def get_access_log_size(self):
        stmt = select(func.count()).select_from(AccessLogModel)
        return self.session.execute(stmt).scalar()

    def get_users(self, page: int, page_size: int = 10):
        stmt = (select(UserModel).order_by(desc(-UserModel.id))
                .offset((page - 1) * page_size).limit(page_size))
        res = self.session.execute(stmt)
        users = res.scalars().all()
        return users

    def get_users_size(self):
        stmt = select(func.count()).select_from(UserModel)
        return self.session.execute(stmt).scalar()

    def add_user(self, login, password, access_layer_id):
        res = self.session.execute(select(AccessLayerModel).where(AccessLayerModel.id == access_layer_id))
        access_layer = res.scalar()
        if self.get_user(login) is None and access_layer is not None:
            res = self.session.execute(select(UserModel.id).order_by(UserModel.id.desc()))
            user_id = res.scalar()
            user = UserModel(id=(user_id+1), login=login, password=password, access_layer_id=access_layer_id)
            self.add(user)
            return True
        else:
            return False

