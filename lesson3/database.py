from sqlalchemy import create_engine
from sqlalchemy.exc import InterfaceError
from sqlalchemy.orm import sessionmaker
import lesson3.models as models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.session_m = sessionmaker(bind=engine)

    def get_or_create(self, session, model, **data):
        db_model = session.query(model).filter(model.url == data['url']).first()
        if not db_model:
            db_model = model(**data)
        return db_model

    def get_done_urls(self):
        session = self.session_m()
        urls = set(session.query(models.Post.url).all())
        session.close()
        return urls

    def create_post(self, data):
        session = self.session_m()
        author = self.get_or_create(session, models.Author, **data['author'])
        tags = [self.get_or_create(session, models.Tag, **tag) for tag in data['tag_data']]
        comments = [self.get_or_create(session, models.Comment, **comment) for comment in data['comment_data']]
        rel_data = {
            'author': author,
            'tags': tags,
            'comments': comments,
        }
        post_data: dict = data['post_data']
        post_data.update(rel_data)
        post = self.get_or_create(session, models.Post, **post_data)

        session.add(post)

        try:
            session.commit()
        except InterfaceError:
            session.rollback()
        finally:
            session.close()


if __name__ == '__main__':
    db = Database('sqlite:///gb_blog.db')
    print(1)
