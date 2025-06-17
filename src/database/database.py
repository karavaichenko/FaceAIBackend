from sqlalchemy import create_engine, select, func, delete, desc, select
from sqlalchemy.orm import registry, Session, sessionmaker, joinedload

from src.database.models import AbstractModel, UserModel, EmployeeModel, AccessLogModel, AccessLayerModel

def hash_password(password: str):
    return password



class Database:

    def __init__(self, URL):
        self.URL = URL
        self.engine = create_engine(self.URL, echo=False)
        self.mapped_registry = registry()
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session().begin():
            AbstractModel.metadata.create_all(self.engine)

        self._add_initial_data()

    def _add_initial_data(self):
        with self.Session() as session:
            res = session.execute(select(AccessLayerModel.id))
            if res.first() is None:
                admin_access_layer = AccessLayerModel(id=0, name="admin")
                self.add(session, admin_access_layer)
                user_access_layer = AccessLayerModel(id=1, name="user")
                self.add(session, user_access_layer)
            res = session.execute(select(UserModel.id))
            if res.first() is None:
                self.create_user("admin", "admin", 0)
            res = session.execute(select(EmployeeModel.id))
            if res.first() is None:
                unknown_employee = EmployeeModel(id=0, name="-", info="-", photo_url="/", is_access=False)
                self.add(session, unknown_employee)
                known_employee = EmployeeModel(id=1, name="Каравайченко Иван", info="шеф", photo_url="/", is_access=True)
                self.add(session, known_employee)
            res = session.execute(select(AccessLogModel.id))
            if res.first() is None:
                some_logs = AccessLogModel(id=0, employee_id=0, timestamp="12-12-2024 12:25:10", is_known=False)
                self.add(session, some_logs)
                some_logs = AccessLogModel(id=1, employee_id=1, timestamp="12-12-2024 12:24:10", is_known=True)
                self.add(session, some_logs)

    def add(self,session, obj):
        session.add(obj)
        session.commit()

    def create_user(self, login: str, password: str, access_id: int):
        with self.Session() as session:
            res = session.execute(select(UserModel.login).where(UserModel.login == login))
            user = res.scalar()
            if user is not None:
                return False
            else:
                res = session.execute(select(UserModel.id).order_by(UserModel.id.desc()))
                id = res.scalar()
                print(id)
                if id:
                    user = UserModel(id=(id + 1), login=login, access_layer_id=access_id, password=hash_password(password),
                                     verify=False)
                else:
                    user = UserModel(id=1, login=login, access_layer_id=access_id, password=hash_password(password))
                self.add(session, user)


    def get_user(self, login):
        with self.Session() as session:
            res = session.execute(select(UserModel).where(UserModel.login == login))
            user = res.scalar()
            return user

    def get_user_by_id(self, user_id):
        with self.Session() as session:
            res = session.execute(select(UserModel).where(UserModel.id == user_id))
            user = res.scalar()
            return user

    def delete_user(self, user_id):
        with self.Session() as session:
            user = self.get_user_by_id(user_id)
            if user is not None:
                session.execute(delete(UserModel).where(UserModel.id == user_id))
                session.commit()
                return True
            else: return False

    def set_user_password(self, user_id, new_password):
        with self.Session() as session:
            user = self.get_user_by_id(user_id)
            if user is None:
                return False
            user.password = new_password
            session.commit()
            return True

    def set_user_access(self, user_id, access_layer_id):
        with self.Session() as session:
            user = self.get_user_by_id(user_id)
            if user is None: return False
            user.access_layer_id = access_layer_id
            session.commit()
            return True

    def get_access_logs(self, page: int, page_size: int = 10):
        with self.Session() as session:
            stmt = select(AccessLogModel).options(joinedload(AccessLogModel.employee)).order_by(desc(AccessLogModel.timestamp)).offset((page - 1) * page_size).limit(page_size)
            res = session.execute(stmt)
            logs = res.scalars().unique()
            logs = list(map(lambda x: x.to_schema(), logs))
            return logs

    def get_access_log_size(self):
        with self.Session() as session:
            stmt = select(func.count()).select_from(AccessLogModel)
            return session.execute(stmt).scalar()

    def get_users(self, page: int, page_size: int = 10):
        with self.Session() as session:
            stmt = (select(UserModel).order_by(desc(-UserModel.id))
                    .offset((page - 1) * page_size).limit(page_size))
            res = session.execute(stmt)
            users = res.scalars().all()
            return users

    def get_users_size(self):
        with self.Session() as session:
            stmt = select(func.count()).select_from(UserModel)
            return session.execute(stmt).scalar()

    def add_user(self, login, password, access_layer_id):
        with self.Session() as session:
            res = session.execute(select(AccessLayerModel).where(AccessLayerModel.id == access_layer_id))
            access_layer = res.scalar()
            if self.get_user(login) is None and access_layer is not None:
                res = session.execute(select(UserModel.id).order_by(UserModel.id.desc()))
                user_id = res.scalar()
                user = UserModel(id=(user_id+1), login=login, password=password, access_layer_id=access_layer_id)
                self.add(session, user)
                return True
            else:
                return False

    def get_employees(self, page, page_size):
        with self.Session() as session:
            try:
                stmt = (select(EmployeeModel).order_by(desc(EmployeeModel.name))
                        .offset((page - 1) * page_size).limit(page_size))
                res = session.execute(stmt)
                employees = res.scalars().unique()
                employees = list(map(lambda x: x.to_schema(), employees))
                return employees
            except:
                session.rollback()

    def get_employee(self, employee_id: int):
        with self.Session() as session:
            try:
                res = session.execute(select(EmployeeModel).where(EmployeeModel.id == employee_id))
                employee = res.scalar()
                return employee
            except:
                session.rollback()

    def add_employee(self, name, info, is_access):
        with self.Session() as session:
            res = session.execute(select(EmployeeModel).where(EmployeeModel.name == name))
            employee = res.scalar()
            if employee is not None: return None
            res = session.execute(select(EmployeeModel).order_by(EmployeeModel.id.desc()))
            employee_id = res.scalar().id
            info = info if info != '' else '-'
            employee = EmployeeModel(id=(employee_id+1), name=name, info=info, is_access=is_access)
            self.add(session, employee)
            return employee_id+1

    def set_employee_photo(self, employee_id):
        with self.Session() as session:
            employee = self.get_employee(employee_id)
            if employee is None: return False
            employee.photo_url = employee_id
            # session.commit()
            self.add(session, employee)
            return True

    def get_employees_size(self):
        with self.Session() as session:
            stmt = select(func.count()).select_from(EmployeeModel)
            return session.execute(stmt).scalar()

    def delete_employee(self, employee_id: int):
        with self.Session() as session:
            employee = self.get_employee(employee_id)
            if employee is not None:
                session.execute(delete(EmployeeModel).where(EmployeeModel.id == employee_id))
                session.commit()
                return True
            else:
                return False
