#! python3
import functools
import hashlib
import os
import sys
import time
import zlib

import falcon

import handle
import model
import utils.log
import utils.telegram

sys.path.insert(0, os.path.abspath("calendar"))
import cal
import sleep


STATIC_PATH = {
    "/": (0, "text/html", "docs/index.html"),
    "/calendar": (2, "text/html", "docs/calendar.html"),
    "/favicon.ico": (0, "image/x-icon", "docs/favicon.ico"),
    "/future": (0, "text/html", "docs/future.html"),
    "/games": (0, "text/html", "docs/games.html"),
    "/main": (1, "text/html", "docs/main.html"),
    "/sleep": (2, "text/html", "docs/sleep.html"),
    "/tictactoe": (0, "text/html", "docs/tictactoe.html"),

    "/css/index.css": (0, "text/css", "docs/css/index.css"),
    "/css/main.css": (0, "text/css", "docs/css/main.css"),
    "/css/menu.css": (0, "text/css", "docs/css/menu.css"),

    "/js/menu.js": (0, "application/javascript", "docs/js/menu.js"),

    "/img/cat.png": (0, "image/png", "docs/img/cat.png"),
}
SHOW_FUNCTIONS = {
    "sleep": (handle.pregenerate_sleep, sleep.generate),
    "out": (handle.pregenerate_out, sleep.generate),
    "calendar": (handle.pregenerate_calendar, cal.generate)
}
IFTTT_TOKEN = os.environ["IFTTT_TOKEN"]

logger = utils.log.get("main")
bot = utils.telegram.Bot()


def report(s):
    try:
        bot.report(s)
    except Exception as e:
        logger.exception(e)


def handle_exception(ex, req, resp, params):
    """
    Falcon internal exception handler. Logs to logger.error
    """
    logger.error(f"{req.method} {req.path}")
    if isinstance(ex, falcon.HTTPError):
        logger.error(f"{type(ex).__name__} -> {ex}")
        raise ex
    else:
        logger.exception(ex)
        raise falcon.HTTPInternalServerError(str(ex))


def load(fpath):
    with open(fpath, "rb") as f:
        data = f.read()
    return data


@functools.lru_cache(maxsize=None)
def generate_user_token(role, hour):
    base = handle.LINK_KEY + str(role) + str(hour)
    return hashlib.sha512(base.encode()).hexdigest()


def redirect(req, res, location):
    res.location = location
    res.status = falcon.HTTP_303  # Force GET


def upload(req, res, content, content_type, cache=("public", "max-age=86400")):
    crc = str(zlib.crc32(content))
    res.cache_control = cache

    if req.if_none_match == crc:  # Cached
        res.status = falcon.HTTP_304
    else:
        res.etag = crc
        res.content_type = content_type
        res.data = content


def static_serve(req, res):
    if req.path not in STATIC_PATH:
        redirect(req, res, "/")
        return
    role, content_type, fpath = STATIC_PATH[req.path]

    if req.role < role:
        redirect(req, res, "/")
        return

    content = load(fpath)
    upload(req, res, content, content_type)


def authenticate(username, password):
    # TODO: add salt to password
    hashed = handle.hash_password(password)
    if list(model.User.select().where(model.User.username == username,
                                      model.User.password == hashed)):
        return 2
    else:
        return 0


class AuthMiddleware:
    def process_request(self, req, resp):
        # Check for token parameter
        token = req.params.get("token", "")
        if token == handle.generate_link_token(req.path):
            req.role = 9
            return

        auth = req.cookies.get("custom-auth", None)
        if not auth:
            req.role = 0
            logger.debug("No auth headers")
            return
        for role in range(1, 3):
            token = generate_user_token(role, int(time.time()) // 3600)
            if auth == token:
                req.role = role
                logger.debug(f"Authorized with role {role}")
                break
        else:
            req.role = 0
            logger.debug("Did not authorize")


class RoleResource:
    def on_get(self, req, res):
        content = load("docs/js/role.js") % req.role
        upload(req, res, content, "application/javascript", ("no-cache",))


class ShowResource:
    def on_get(self, req, res, name):
        real_name = name.lstrip("$")
        weeks = int(req.params.get("weeks", 26))

        if real_name in SHOW_FUNCTIONS:
            if req.role < 2:
                raise falcon.HTTPForbidden("Try with a higher role")
            pre, final = SHOW_FUNCTIONS[real_name]

            args = pre(weeks)

            if name.startswith("$"):
                res.media = args
            else:
                upload(req, res, final(**args), "image/png")
        else:
            redirect(req, res, "/img/cat.png")


class LoginResource:
    def on_post(self, req, res):
        redirect(req, res, "/")

        if req.content_type != "application/x-www-form-urlencoded":
            raise falcon.HTTPBadRequest

        pairs = req.stream.read(req.content_length or 0).decode().split("&")
        if pairs == [""]:  # De-authenticate
            res.unset_cookie("custom-auth")
            logger.debug("De-Auth")
            return
        data = dict(pair.split("=") for pair in pairs)

        try:
            username, password = data["username"], data["password"]
        except KeyError:
            raise falcon.HTTPBadRequest

        role = authenticate(username, password)
        token = generate_user_token(role, int(time.time()) // 3600)
        res.set_cookie("custom-auth", token)
        logger.debug("Set cookie")


class TelegramResource:
    def on_post(self, req, res):
        try:
            handle.handle(req.media)
        except Exception as ex:
            logger.exception(ex)
            report(str(ex))
            logger.error(str(req.media))
            report(str(req.media))


class IftttResource:
    def on_post(self, req, res):
        try:
            handle.ifttt(req.media)
        except Exception as ex:
            logger.exception(ex)
            report(str(ex))
            logger.error(str(req.media))
            report(str(req.media))


logger.info("Creating instance")
auth_middleware = AuthMiddleware()
app = falcon.API(middleware=auth_middleware)
app.add_error_handler(Exception, handler=handle_exception)

role_resource = RoleResource()
show_resource = ShowResource()
login_resource = LoginResource()
telegram_resource = TelegramResource()
ifttt_resource = IftttResource()

app.add_route("/js/role", role_resource)
app.add_route("/show/{name}", show_resource)
app.add_route("/login", login_resource)
app.add_route(f"/{utils.telegram.TELEGRAM_TOKEN}", telegram_resource)
app.add_route(f"/{IFTTT_TOKEN}", ifttt_resource)
app.add_sink(static_serve)
