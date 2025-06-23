from sqlalchemy import create_engine, select, func, delete, desc, select, update
from sqlalchemy.orm import registry, Session, sessionmaker, joinedload
from src.utils.utils import hash_password

from src.database.models import AbstractModel, UserModel, EmployeeModel, AccessLogModel, AccessLayerModel, \
    EmployeeEncodingsModel


class Database:

    def __init__(self, URL, root_password, admin_password):
        self.URL = URL
        self.engine = create_engine(self.URL, echo=False)
        self.mapped_registry = registry()
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session().begin():
            AbstractModel.metadata.create_all(self.engine)

        self._add_initial_data(root_password, admin_password)

    def _add_initial_data(self, root_password, admin_password):
        with self.Session() as session:
            res = session.execute(select(AccessLayerModel.id))
            if res.first() is None:
                admin_access_layer = AccessLayerModel(id=0, name="admin")
                self.add(session, admin_access_layer)
                user_access_layer = AccessLayerModel(id=1, name="user")
                self.add(session, user_access_layer)
            res = session.execute(select(UserModel.id))
            if res.first() is None:
                root_user = UserModel(id=0, login='root', password=hash_password(root_password), access_layer_id=0)
                admin = UserModel(id=1, login='admin', password=hash_password(admin_password), access_layer_id=0)
                self.add(session, admin)
                self.add(session, root_user)
            res = session.execute(select(EmployeeModel.id))
            if res.first() is None:
                unknown_employee = EmployeeModel(id=0, name="-", info="-", photo_url="/", is_access=False)
                self.add(session, unknown_employee)
                # known_employee = EmployeeModel(id=1, name="Каравайченко Иван", info="шеф", photo_url="/", is_access=True)
                # self.add(session, known_employee)
            # res = session.execute(select(AccessLogModel.id))
            # if res.first() is None:
            #     some_logs = AccessLogModel(id=0, employee_id=0, timestamp="12-12-2024 12:25:10", photo_url="0")
            #     self.add(session, some_logs)
            #     some_logs = AccessLogModel(id=1, employee_id=1, timestamp="12-12-2024 12:24:10", photo_url="1")
            #     self.add(session, some_logs)

    def add(self, session, obj):
        session.add(obj)
        session.commit()

    # Users

    def add_user(self, login, password, access_layer_id):
        with self.Session() as session:
            res = session.execute(select(AccessLayerModel).where(AccessLayerModel.id == access_layer_id))
            access_layer = res.scalar()
            if self.get_user(login) is None and access_layer is not None:
                res = session.execute(select(UserModel.id).order_by(UserModel.id.desc()))
                user_id = res.scalar()
                user_id = user_id + 1 if user_id is not None else 0
                user = UserModel(id=user_id, login=login, password=hash_password(password), access_layer_id=access_layer_id)
                self.add(session, user)
                return True
            else:
                return False

    def get_users(self, page: int, page_size: int = 10):
        with self.Session() as session:
            stmt = (select(UserModel).where(UserModel.login != "root").order_by(desc(-UserModel.id))
                    .offset((page - 1) * page_size).limit(page_size))
            res = session.execute(stmt)
            users = res.scalars().all()
            return users

    def get_users_size(self):
        with self.Session() as session:
            stmt = select(func.count()).select_from(UserModel)
            return session.execute(stmt).scalar()

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
            user.password = hash_password(new_password)
            session.commit()
            return True

    def set_user_access(self, user_id, access_layer_id):
        with self.Session() as session:
            user = self.get_user_by_id(user_id)
            if user is None: return False
            user.access_layer_id = access_layer_id
            self.add(session, user)
            return True

    # AccessLogs

    def get_access_logs(self, page: int, page_size: int = 10):
        with self.Session() as session:
            stmt = select(AccessLogModel).options(joinedload(AccessLogModel.employee)).order_by(desc(AccessLogModel.timestamp)).offset((page - 1) * page_size).limit(page_size)
            res = session.execute(stmt)
            logs = res.scalars().unique()
            logs = list(map(lambda x: x.to_schema(), logs))
            return logs

    def get_access_log(self, id):
        with self.Session() as session:
            res = session.execute(select(AccessLogModel).where(AccessLogModel.id == id))
            access_log = res.scalar()
            return access_log

    def get_access_log_size(self):
        with self.Session() as session:
            stmt = select(func.count()).select_from(AccessLogModel)
            return session.execute(stmt).scalar()

    def add_access_log(self, employee_id, timestamp):
        with self.Session() as session:
            employee = self.get_employee(employee_id)
            if employee is None: return False
            res = session.execute(select(AccessLogModel.id).order_by(AccessLogModel.id.desc()))
            log_id = res.scalar()
            log_id = log_id + 1 if log_id is not None else 0
            access_log = AccessLogModel(id=log_id, employee_id=employee_id, timestamp=timestamp)
            self.add(session, access_log)
            return True

    # Employees

    def get_employees(self, page, page_size, substr):
        with self.Session() as session:
            try:
                if substr is not None and substr != '':
                    substr = f"%{substr}%"
                    stmt = (select(EmployeeModel).where(EmployeeModel.name.ilike(substr))
                            .order_by(desc(EmployeeModel.name))
                            .offset((page - 1) * page_size).limit(page_size))
                    res = session.execute(stmt)
                    employees = res.scalars().unique()
                else:
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
            # Удаление энкодинга
            session.execute(delete(EmployeeEncodingsModel).where(EmployeeEncodingsModel.employee_id == employee_id))
            employee.photo_url = employee_id
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
                # Замена связанных логов
                _res = session.execute(update(AccessLogModel)
                                       .where(AccessLogModel.employee_id == employee.id).values(employee_id=0))
                # Удаление энкодинга
                session.execute(delete(EmployeeEncodingsModel)
                                .where(EmployeeEncodingsModel.employee_id == employee.id))
                session.execute(delete(EmployeeModel).where(EmployeeModel.id == employee_id))
                session.commit()
                return True
            else:
                return False

    def set_employee_data(self, employee_id, name, info, is_access):
        with self.Session() as session:
            employee = self.get_employee(employee_id)
            if employee is None: return False
            res = session.execute(select(EmployeeModel.id).where(EmployeeModel.name == name))
            employee_name = res.scalar()
            if employee_name is not None and employee_name != employee_id: return False
            employee.name = name
            info = "-" if not info else info
            employee.info = info
            employee.is_access = is_access
            self.add(session, employee)
            return True

