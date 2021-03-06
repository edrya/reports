
from __future__ import division
import sendgrid
from elasticsearch import Elasticsearch
import datetime
import cli.app
import pymysql
from pymongo import MongoClient

DEV_ENV = {'es': '10.2.42.222', 'mysql': '10.2.42.88', 'mongo': '10.2.42.205'}
LOC_ENV = {'es': '127.0.0.1', 'mysql': 'localhost'}
PROD_ENV = {'es': '10.1.77.193', 'mysql': '10.1.77.167', 'mongo': '10.1.77.114'}


class Metric(object):

    def __init__(self, env_type, start_day, end_day):
        self.environment_type = env_type
        self.es = Elasticsearch([{'host': self.environment_type['es']}])
        self.start_date = start_day
        self.end_date = end_day

    def total_story(self):
        res = self.es.search(index='story', doc_type='story_meta', search_type='count',
                             body={
                                 "query": {"range": {"created": {
                                     "lte": self.end_date
                                 }}}})

        size = res['hits']['total']
        return size

    # def total_story(self):
    #     a = self._get_all_publishers()
    #     b = self._get_fake_accounts()
    #     pub = set(a)
    #     fake = set(b)
    #     fake_pub = fake.intersection(pub)
    #     f = list(fake_pub)
    #
    #     client = MongoClient(self.environment_type['mongo'], 27017)
    #     db = client.ecquant
    #
    #     fake_stories = db.news.find({"$and": [{"publisher_id": {"$in": f}},
    #                                           {"created_on": {"$lte": self.end_date}}]}).count()
    #
    #     all_stories = db.news.find({"created_on": {"$lte": self.end_date}}).count()
    #
    #     total_real_stories = all_stories - fake_stories
    #
    #     size = total_real_stories
    #     return size

    def total_publisher(self):

        a = self._get_all_publishers()
        b = self._get_fake_accounts()
        pub = set(a)
        fake = set(b)
        real_pub = pub - fake
        fake_pub = fake.intersection(pub)

        return len(real_pub)

    def _get_fake_accounts(self):

        msql_connection = pymysql.connect(host=self.environment_type['mysql'], user='devRead', password='Rypkit10',
                                          db='qb_main')
        try:
            with msql_connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT account_id FROM qb_main.users WHERE email REGEXP '@qbeats.com' OR " \
                      "email REGEXP '@mailinator.com' OR email REGEXP '@qbeatsinternal.com' " \
                      "OR email REGEXP '@drdrb.net' OR email REGEXP '@n-ix.com';"
                cursor.execute(sql)
                results = cursor.fetchall()

        finally:
            msql_connection.close()
        a = results
        print a
        fake_acct = [a['account_id'] for a in a]
        return fake_acct

    def _get_all_publishers(self):
        msql_connection = pymysql.connect(host=self.environment_type['mysql'], user='devRead', password='Rypkit10',
                                          db='qb_main')
        today = self.end_date
        try:
            with msql_connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT publishers.account_id, publishers.name  FROM qb_main.publishers where type IN " \
                      "('FREELANCER','INTEGRATED', 'ORGANIZATION') AND last_published_on IS NOT NULL " \
                      "AND created_at <= %s;"
                p = today
                cursor.execute(sql,[p])
                results = cursor.fetchall()

        finally:
            msql_connection.close()
        a = results
        print a
        pub_acct = [a['account_id'] for a in a]
        d = len(pub_acct)
        return pub_acct

    def priced_story(self):
        res = self.es.search(index='story', doc_type='story_meta', search_type='count',
                             body={
                                 "query": {
                                     "filtered": {
                                         "filter": {
                                             "bool":
                                                 {"must":
                                                     [{
                                                         "range": {
                                                             "price": {
                                                                 "gt": 0
                                                             }}},
                                                         {
                                                         "range": {
                                                             "created": {
                                                                 "gte": self.start_date,
                                                                 "lte": self.end_date
                                                             }}}
                                                     ]}
                                         }

                                     }}

                             })

        size = res['hits']['total']

        return size

    def es_total_story(self):
        res = self.es.search(index='story', doc_type='story_meta', search_type='count',
                             body={
                                 "query": {"range": {"created": {
                                     "lte": self.end_date
                                 }}}})

        size = res['hits']['total']
        return size

    def free_story(self):
        res = self.es.search(index='story', doc_type='story_meta', search_type='count',
                             body={
                                 "query": {
                                     "filtered": {
                                         "filter": {
                                             "bool":
                                                 {"must":
                                                     [{"term": {
                                                         "start_price": 0
                                                     }},
                                                         {"term": {
                                                         "price": 0
                                                     }}, {
                                                         "range": {
                                                             "created": {
                                                                 "lte": self.end_date
                                                             }}}
                                                     ]}
                                         }

                                     }}

                             })

        size = res['hits']['total']
        return size

    def price_change(self):
        res = self.es.search(index='story', doc_type='price_change', search_type='count',

                             body={
                                 "query": {"range": {"start": {
                                     "lte": self.end_date
                                 }}}})

        size = res['hits']['total']
        return size

    def shelf_life(self):
        return 0


class Analytics(object):

    def calc_weekly_trend(self, y1, y2):
        per_trend = 0
        trend = y1 - y2

        if trend:
            per_trend = round(100 * trend / y2, 2)

        return per_trend


class Report(object):
    @staticmethod
    def send(start_date, end_date, p, l, t, n):

        format_end_day = end_date.strftime('%B %d')
        format_start_day = start_date.strftime('%B %d')
        previous_wk, last_wk, trend = p, l, t

        sg = sendgrid.SendGridClient(sg_username, sg_password)
        message = sendgrid.Mail()
        message.set_from("amir.edry@qbeats.com")
        message.set_subject('Weekly update')
        header = 'Statistics Overview as of  %s' % format_end_day

        message.set_text(" ")
        message.set_html(" ")

        # SMTP API
        # ========================================================#
        # Add the recipients
        # recipients = ["amir.edry@qbeats.com", "dan.conte@qbeats.com", ]
        recipients = ["amir.edry@qbeats.com"]

        message.smtpapi.set_tos(recipients)

        subs = {
            "%header%": [header] * len(recipients),

            "%l_total_story%": ['{:,}'.format(last_wk['total_story'])] * len(recipients),
            "%l_priced_story%": ['{:,}'.format(last_wk['priced_story'])] * len(recipients),
            "%l_free_story%": ['{:,}'.format(last_wk['free_story'])] * len(recipients),
            "%l_price_change%": ['{:,}'.format(last_wk['price_change'])] * len(recipients),
            "%l_shelf_life%": ['-'] * len(recipients),
            "%l_total_publisher%": ['{:,}'.format(last_wk['total_publisher'])] * len(recipients),

            "%t_total_story%": ['{:,}'.format(n['total_story']) + " [" + trend['total_story']+"]"] * len(recipients),
            "%t_priced_story%": ['{:,}'.format(n['priced_story']) + " [" + trend['priced_story']+"]"] * len(recipients),
            "%t_free_story%": ['{:,}'.format(n['free_story']) + " [" + trend['free_story']+"]"] * len(recipients),
            "%t_price_change%": ['{:,}'.format(n['price_change']) + " [" + trend['price_change']+"]"] * len(recipients),
            "%t_shelf_life%": ['-'] * len(recipients),
            "%t_total_publisher%": ['{:,}'.format(n['total_publisher']) + " [" + trend['total_publisher']+"]"] * len(recipients)

        }

        for tag, values in subs.iteritems():
            for value in values:
                message.add_substitution(tag, value)

        message.add_filter('templates', 'template_id', 'd92ae7cd-958b-43ee-bd1b-bc5cd7efe48b')
        message.add_filter('subscriptiontrack', 'enable', '0')

        # SEND THE MESSAGE
        # ========================================================#
        status, msg = sg.send(message)

        print msg

    @staticmethod
    def get_metrics(t, s, e):
        metrics = {}
        m = Metric(t, s, e)
        metrics['total_story'] = m.total_story()
        metrics['es_total_story'] = m.es_total_story()
        metrics['total_publisher'] = m.total_publisher()

        # metrics['priced_story'] = m.priced_story()
        metrics['free_story'] = m.free_story()
        metrics['priced_story'] = metrics['es_total_story'] - metrics['free_story']
        metrics['price_change'] = m.price_change()
        metrics['shelf_life'] = m.shelf_life()

        return metrics

    def generate_report(self, env_type, start_day, end_day):
        a = Analytics()
        trend = {}
        change_number = {}

        previous_wk = Report.get_metrics(env_type, datetime.datetime(2015, 01, 01), generate_date(10))
        last_wk = Report.get_metrics(env_type, datetime.datetime(2015, 01, 01), generate_date(3))

        for metric in previous_wk:
            trend_num = a.calc_weekly_trend(last_wk[metric], previous_wk[metric])
            change_number[metric] = last_wk[metric]- previous_wk[metric]
            if trend_num > 0:
                trend[metric] = '<span style="color:#46a800; font-size:12px; ' \
                                'font-weight:normal; font-family:Helvetica Neue,' \
                                'Helvetica,Lucida Grande,tahoma,verdana,' \
                                'arial,sans-serif">{}%</span>'.format(trend_num)
            elif trend_num == 0:
                trend[metric] = '<span style="color:#141823; font-size:12px; font-weight:normal; ' \
                                'font-family:Helvetica Neue,Helvetica,Lucida Grande,tahoma,verdana,arial,sans-serif">' \
                                '{}%</span>'.format(trend_num)
            else:
                trend[metric] = '<span style="color:#da2929; font-size:12px; font-weight:normal; ' \
                                'font-family:Helvetica Neue,Helvetica,Lucida Grande,tahoma,' \
                                'verdana,arial,sans-serif">{}%</span>'.format(trend_num)

        Report.send(generate_date(9), end_day,  previous_wk, last_wk, trend, change_number)


def generate_date(delta_days):
    date = datetime.datetime.today() - datetime.timedelta(days=delta_days)
    return date


def run(report_type, env_type):
    r = Report()
    if report_type == 'daily':
        pass
    else:
        start_day = generate_date(10)
        end_day = generate_date(3)
        r.generate_report(PROD_ENV, start_day, end_day)


@cli.app.CommandLineApp
def main(app):
    run(app.params.report_type, app.params.environment_type)


main.add_param("-t", "--report_type", help="What type of report to run? *Default to daily", default="daily",
               required=True)
main.add_param("-e", "--environment_type", help="What environment to run it on? *Default to Development Environment",
               default="loc", required=True)

if __name__ == '__main__':
    main.run()
