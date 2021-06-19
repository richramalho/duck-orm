import inspect
from duck_orm.sql.Condition import Condition
from typing import Any, Dict, Type

from duck_orm.Model import Model
from duck_orm.sql.fields import Column


class ForeignKey(Column):
    def __new__(cls, **kwargs):
        return super().__new__(cls)

    def __init__(self, model: Type[Model], name_in_table_fk: str):
        self.model = model
        self.name_in_table_fk = name_in_table_fk
        super().__init__('ForeignKey')

    def sql(self) -> str:
        column_sql = 'FOREIGN KEY ({name}) REFERENCES ' + \
            self.model.get_name() + ' (' + self.name_in_table_fk + ')'
        return column_sql


class OneToMany(Column):
    def __new__(cls, **kwargs):
        return super().__new__(cls)

    def __init__(self, model: Type[Model], name_in_table_fk: str, name_relation: str):
        self.model = model
        self.name_in_table_fk = name_in_table_fk
        self.model_: Type[Model] = None
        if not name_relation:
            raise Exception('Attribute name_relation is mandatory')
        self.name_relation = name_relation
        super().__init__('OneToMany')

    async def add(self, model: Type[Model]):
        model._instance[self.name_in_table_fk] = self.model_
        return await self.model.save(model)

    async def get_all(self):
        return await self.model.find_all(conditions=[
            Condition(self.name_in_table_fk, '=',
                      self.model_[self.model_.get_id()[0]])
        ])

    def sql_column(self, type_sql: str):
        sql = 'ALTER TABLE ' + self.model.get_name() + \
            ' ADD {name} ' + type_sql
        return sql

    def sql(self):
        column_sql = 'ALTER TABLE ' + self.model.get_name() + \
            ' ADD CONSTRAINT ' + self.name_relation + \
            ' FOREIGN KEY ({name}) REFERENCES {name_table} ({field_name})'
        return column_sql


class ManyToOne(Column):
    def __new__(cls, **kwargs):
        return super().__new__(cls)

    def __init__(self, model: Type[Model]):
        self.model = model
        super().__init__('OneToMany')


class OneToOne(Column):
    def __new__(cls, **kwargs):
        return super().__new__(cls)

    def __init__(self, model: Type[Model], name_relation: str, field: str):
        self.model = model
        if not name_relation:
            raise Exception('Attribute name_relation is mandatory')
        if not field:
            raise Exception('Attribute field is mandatory')
        self.name_relation = name_relation
        self.field = field
        super().__init__('OneToOne', primary_key=True)

    def sql(self) -> str:
        column_sql = 'ALTER TABLE {table}' + \
            ' ADD CONSTRAINT ' + self.name_relation + \
            ' FOREIGN KEY (' + self.field + \
            ') REFERENCES {name_table} ({field_name})'

        return column_sql


class ManyToMany(Column):
    def __new__(cls, **kwargs):
        return super().__new__(cls)

    def __init__(self, model: Type[Model], model_relation: Type[Model]):
        self.model = model
        self.model_: Type[Model] = None
        self.model_relation = model_relation
        super().__init__('ManyToMany')

    async def add(self, model_instance_one: Model, model_instance_two: Model):
        # TODO: Validation:
        #           - Check if model_instance_one and model_instance_two were
        #             persisted in the database.
        model_dict: Dict[str, Any] = {}
        for name, field in inspect.getmembers(self.model_relation):
            if (isinstance(field, ForeignKey)) and not field.primary_key:
                if isinstance(model_instance_one, field.model):
                    name_field = model_instance_one.get_id()[0]
                    model_dict[name] = model_instance_one[name_field]
                elif isinstance(model_instance_two, field.model):
                    name_field = model_instance_two.get_id()[0]
                    model_dict[name] = model_instance_two[name_field]

        model_save = self.model_relation(**model_dict)
        return await self.model_relation.save(model_save)

    async def add(self, model_instance_one: Model):
        # TODO: Validation:
        #           - Check if model_instance_one were
        #             persisted in the database.
        model_dict: Dict[str, Any] = {}
        for name, field in inspect.getmembers(self.model_relation):
            if (isinstance(field, ForeignKey)) and not field.primary_key:
                if isinstance(model_instance_one, field.model):
                    name_field = model_instance_one.get_id()[0]
                    model_dict[name] = model_instance_one[name_field]
                elif isinstance(self.model_, field.model):
                    name_field = self.model_.get_id()[0]
                    model_dict[name] = self.model_[name_field]

        model_save = self.model_relation(**model_dict)
        return await self.model_relation.save(model_save)

    async def get_all(self):
        return await self.model.find_all(conditions=[
            Condition(self.name_in_table_fk, '=',
                      self.model_[self.model_.get_id()[0]])
        ])

    def sql_column(self, type_sql: str):
        sql = 'ALTER TABLE ' + self.model.get_name() + \
            ' ADD {name} ' + type_sql
        return sql

    def sql(self):
        column_sql = 'ALTER TABLE ' + self.model.get_name() + \
            ' ADD CONSTRAINT ' + self.name_relation + \
            ' FOREIGN KEY ({name}) REFERENCES {name_table} ({field_name})'
        return column_sql
