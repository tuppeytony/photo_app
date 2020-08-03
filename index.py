import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.httpserver
import asyncio
import os.path
import psycopg2
from psycopg2.extras import DictCursor
# from config import DB_CONNECT
from boto.s3.connection import S3Connection
import os
import random
import string
# from config import DB_CONNECT_LOCAL


# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


db_name = os.environ['Database']
user_db = os.environ['User']
db_password = os.environ['Password']
db_host = os.environ['Host']
db_port = os.environ['Port']


# db_name = DB_CONNECT_LOCAL['db_name']
# user_db = DB_CONNECT_LOCAL['user_db']
# db_password = DB_CONNECT_LOCAL['db_password']
# db_host = DB_CONNECT_LOCAL['db_host']
# db_port = DB_CONNECT_LOCAL['db_port']


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("photo_app_user")

    def get_all_data(self, stmt, *args):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(stmt, *args)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records

    def get_current_album(self, id, page, stmt, *args):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(stmt, *args)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records

    def pic_actions(self, stmt, *args):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor()
        cursor.execute(stmt, *args)
        conn.commit()
        cursor.close()
        conn.close()

    def remove_pic(self, stmt, *args):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor()
        cursor.execute(stmt, *args)
        current_photo = str(cursor.fetchone()[0])
        conn.commit()
        cursor.close()
        conn.close()
        return current_photo

    def edit_album(self, stmt, *args):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(stmt, *args)
        current_album = str(cursor.fetchone()[0])
        conn.commit()
        cursor.close()
        conn.close()
        return current_album

    def registration(self):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor()
        cursor.execute("SELECT login_user, mail_user FROM users "
                    "WHERE login_user = %s AND mail_user = %s",
        (self.get_argument("login"),
        self.get_argument("email"))
        )
        user_exists = cursor.fetchone()
        if user_exists != None:
            error = True
            self.render('registration.html', title_page='Регистрация', error=error)
        else:
            cursor.execute(
            "INSERT INTO users (login_user, password_user, mail_user) "
            "VALUES (%s, %s, %s) RETURNING id_user",
            (self.get_argument("login"),
            self.get_argument("password"),
            self.get_argument("email"))
        )
            res = cursor.fetchone()
            cookie = str(res[0])
            self.set_secure_cookie("photo_app_user", cookie)
            self.redirect('/')
        conn.commit()
        cursor.close()
        conn.close()
    
    def signin(self):
        conn = psycopg2.connect(dbname=db_name, user=user_db, 
                        password=db_password, host=db_host, port=db_port)
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE mail_user = %s AND password_user = %s", 
            (self.get_argument("email"),
            self.get_argument("password"))
        )
        res = cursor.fetchone()
        if res == None:
            error = True
            self.render('signin.html', title_page='Авторизация', error=error)
        else:
            cookie = str(res[0])
            self.set_secure_cookie("photo_app_user", cookie)
            self.redirect('/')
        conn.commit()
        cursor.close()
        conn.close()


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect('/signin')
            return
        user = int(self.get_secure_cookie('photo_app_user'))
        db = self.get_all_data('SELECT id_album, title_album, description_album, fk_user_id, login_user, fk_user_id FROM album '
                                    'INNER JOIN users ON id_user = fk_user_id')
        self.render('index.html', title_page='Главная страница', db=db, user=user)


class CurrentAlbum(BaseHandler):
    def get(self, id):
        page = int(self.get_query_argument('page'))
        limit = 6
        offset = limit * (page - 1)
        albumDB = self.get_current_album(id, page, 
        'SELECT title_photo, description_photo, src_photo, login_user, fk_album_id, id_photo, id_user' 
        ' FROM photo INNER JOIN users ON fk_user_id = id_user WHERE fk_album_id = %s LIMIT %s OFFSET %s',
        (id,
        int(limit),
        int(offset))
        )
        user = int(self.get_secure_cookie('photo_app_user'))
        self.render('album.html', title_page='Выбранный альбом', albumDB=albumDB, user=user)


    def post(self, id):
        file1 = self.request.files['src'][0]
        original_fname = file1['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        final_filename= fname+extension
        output_file = open("album/" + final_filename, 'wb')
        output_file.write(file1['body'])


        self.pic_actions('INSERT INTO photo (title_photo, description_photo, src_photo, fk_user_id, fk_album_id) '
        'VALUES (%s, %s, %s, %s, %s)',
        (self.get_argument("title"),
        self.get_argument("description"),
        final_filename,
        int(self.get_secure_cookie("photo_app_user")),
        self.get_argument('album', str(id)))
        )
        page = int(self.get_query_argument('page'))
        self.redirect(self.get_argument('album', str(id) + '?' + "page" + "=" + str(page)))



class Delete_photo(BaseHandler):
    def post(self):
        current_photo = self.remove_pic('DELETE FROM photo WHERE id_photo = %s RETURNING src_photo',
        (self.get_argument('id_photo'),)
        )
        os.remove(f'album/{current_photo}')
        self.redirect('/album/' + self.get_argument('id_album') + '?page=1')
     
     
class Edit_photo(BaseHandler):
    
    def get(self):
        albumDB = self.get_all_data('SELECT * FROM photo WHERE id_photo = %s',
        (self.get_argument('id_photo'),)
        )
        self.render('edit.html', title_page='Редактировать фотографию', albumDB=albumDB)

    def post(self):
        self.pic_actions('UPDATE photo SET title_photo = %s, description_photo = %s WHERE id_photo = %s',
        (self.get_argument('title'),
        self.get_argument('description'),
        self.get_argument('id_photo'),)
        )
        self.redirect('/')


class Edit_album(BaseHandler):
    def get(self):
        albumDB = self.get_all_data('SELECT * FROM album WHERE id_album = %s',
        (self.get_argument('id_album'),)
        )
        self.render('edit_album.html', title_page='Редактировать альбом', albumDB=albumDB)

    def post(self):
        current_album = self.edit_album('UPDATE album SET title_album = %s, description_album = %s where id_album = %s '
        'RETURNING id_album',
        (self.get_argument('title'),
        self.get_argument('description'),
        self.get_argument('id_album'),)
        )
        self.redirect('/album/' + current_album + '?page=1')


class Delete_album(BaseHandler):
    def post(self):
        self.pic_actions('DELETE FROM album WHERE id_album = %s',
        (self.get_argument('id_album'),)
        )
        self.redirect('/')
         

class LogOut(BaseHandler):
    def get(self):
        self.clear_all_cookies("photo_app_user")
        self.redirect('/')


class Registration(BaseHandler):
    def get(self):
        self.render('registration.html', title_page='Регистрация', error=None)

    def post(self):
        self.registration()


class Signin (BaseHandler):
    def get(self):
        self.render('signin.html', title_page='Авторизация', error=None)
    
    def post(self):
        self.signin()


class New_album(BaseHandler):
    def get(self):
        self.render('new_album.html', title_page='Новый альбом')

    def post(self):
        self.pic_actions("INSERT INTO album (title_album, description_album, fk_user_id) "
                        "VALUES (%s, %s, %s)",            
        (self.get_argument("title"),
        self.get_argument("description"),
        int(self.get_secure_cookie('photo_app_user'))))
        self.redirect('/')
    






def main():
    settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url": "/signin",
    "debug": True,
    "autoreload": True,
    }

    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/signin", Signin),
    (r"/new_album", New_album),
    (r"/album/(\w+)", CurrentAlbum),
    (r"/album/(.*)", tornado.web.StaticFileHandler, {"path" : "album/"}),
    (r"/registration", Registration),
    (r"/logout", LogOut),
    (r"/delete", Delete_album),
    (r"/delete_photo", Delete_photo),
    (r"/edit_photo", Edit_photo),
    (r"/edit_album", Edit_album),
    ], 
    **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 5000))
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()



if __name__ == '__main__':
    print('Server running!')
    main()