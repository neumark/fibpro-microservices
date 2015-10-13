#!/usr/bin/env python
# dependencies
from raven import Client
from raven.middleware import Sentry
# fibpro modules
from const import SENTRY_DSN
from http_basic import HTTPBasic
from user_db import init_user_db, get_user
from util import http_response
from pricing import update_user_credit
from logsink import log

init_user_db()

def fib(n):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a

def fib_app(environ, start_response):
    # get user object
    user_obj = environ.get('REMOTE_USER')
    # parse integer fibonacci sequence index
    try:
        requested_fib = int(environ['PATH_INFO'][1:])
    except ValueError, e:
        log.warn('Request to %s resulted in %s' % (
            environ['PATH_INFO'], str(e)))
        return http_response(start_response,
            status="404 NOT FOUND",
            body=str(e))
    # verify and update user credit
    credit_ok = update_user_credit(requested_fib, user_obj)
    if credit_ok != True:
        # log and return error if credit insufficient
        log.info(
                'User "%s" denied fib(%s), credit: %s' % (
            user_obj.username,
            requested_fib,
            user_obj.credit))
        return http_response(start_response,
                status="403 FORBIDDEN",
                body=credit_ok)
    # return requested fibonacci number
    return http_response(start_response,
        body=fib(requested_fib))

app = Sentry(
    HTTPBasic(fib_app, get_user),
    Client(SENTRY_DSN))