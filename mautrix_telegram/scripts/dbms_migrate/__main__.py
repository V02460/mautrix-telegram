import argparse
import sqlalchemy as sql
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from alchemysession import AlchemySessionContainer

parser = argparse.ArgumentParser(description="mautrix-telegram dbms migration script",
                                 prog="python -m mautrix_telegram.scripts.dbms_migrate")
parser.add_argument("-f", "--from-url", type=str, required=True, metavar="<url>",
                    help="the old database path")
parser.add_argument("-t", "--to-url", type=str, required=True, metavar="<url>",
                    help="the new database path")
args = parser.parse_args()


def connect(to):
    import mautrix_telegram.db.base as base
    base.Base = declarative_base(cls=base.BaseBase)
    from mautrix_telegram.db import (Portal, Message, UserPortal, User, RoomState, UserProfile,
                                     Contact, Puppet, BotChat, TelegramFile)
    db_engine = sql.create_engine(to)
    db_factory = orm.sessionmaker(bind=db_engine)
    db_session = orm.scoped_session(db_factory)  # type: orm.Session
    base.Base.metadata.bind = db_engine
    session_container = AlchemySessionContainer(engine=db_engine, session=db_session,
                                                table_base=base.Base, table_prefix="telethon_",
                                                manage_tables=False)

    return db_session, {
        "Version": session_container.Version,
        "Session": session_container.Session,
        "Entity": session_container.Entity,
        "SentFile": session_container.SentFile,
        "UpdateState": session_container.UpdateState,
        "Portal": Portal,
        "Message": Message,
        "Puppet": Puppet,
        "User": User,
        "UserPortal": UserPortal,
        "RoomState": RoomState,
        "UserProfile": UserProfile,
        "Contact": Contact,
        "BotChat": BotChat,
        "TelegramFile": TelegramFile,
    }


session, tables = connect(args.from_url)

data = {}
for name, table in tables.items():
    data[name] = session.query(table).all()

session, tables = connect(args.to_url)
for name, table in tables.items():
    for row in data[name]:
        session.merge(row)
session.commit()
