from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime


Base = declarative_base()


"""
one to one
one to many -> many to one
many to many
"""


post_x_tag_table = Table(
    'post_x_tag',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id')),
)


class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, autoincrement=True, primary_key=True)
    gb_id = Column(Integer, nullable=False, unique=True)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, unique=False, nullable=False)
    img = Column(String, unique=False, nullable=True)
    published_at = Column(DateTime, nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary='post_x_tag', backref='posts')
    comments = relationship('Comment')


class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, unique=False, nullable=False)
    posts = relationship('Post')


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, unique=False, nullable=False)


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, autoincrement=True, primary_key=True)
    site_id = Column(Integer, nullable=True, unique=True)
    parent_id = Column(Integer, nullable=True, unique=False)
    root_id = Column(Integer, nullable=True, unique=False)
    url = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=False)
    content = Column(String, nullable=True, unique=False)
    post_id = Column(Integer, ForeignKey('post.id'))
    post = relationship('Post')
