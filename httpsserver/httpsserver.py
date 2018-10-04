#!/usr/bin/env python3.4
import hashlib
import re
import ssl
from . import billing_service
from redis import Redis
from rq import Queue
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse
import imp

with open('.secret/botsecret.py', 'rb') as fp:
    botsecret = imp.load_module('botsecret', fp, '.secret/botsecret.py', ('.py', 'rb', imp.PY_SOURCE)).botsecret
with open('.secret/ymsecret.py', 'rb') as fp:
    ymsecret = imp.load_module('ymsecret', fp, '.secret/ymsecret.py', ('.py', 'rb', imp.PY_SOURCE)).ymsecret
    ym_account_id = imp.load_module('ymsecret', fp, '.secret/ymsecret.py', ('.py', 'rb', imp.PY_SOURCE)).ym_account_id
with open('.secret/rq_access.py', 'rb') as fp:
    rq_access = imp.load_module('rq_access', fp, '.secret/rq_access.py', ('.py', 'rb', imp.PY_SOURCE))

redis_conn = Redis(host=rq_access.host, port=rq_access.port, password=rq_access.password)
q_billing = Queue(connection=redis_conn, name='billing', default_timeout=3600)
post_data_last = None


class S(SimpleHTTPRequestHandler):
    def _set_headers(self):
        raw_url = str(self.path)
        if raw_url.find('yourdomain.xyz/generate?page=') != -1:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            self.send_response(403)

    def do_GET(self):
        self._set_headers()
        # self.send_header('Content-type', 'text/html')
        raw_url = self.path
        try:
            parsed_url = parse.parse_qs(raw_url)
            page_type = str(parsed_url['/generate?page'][0])
            if page_type == 'subscribe':
                user_id = int(parsed_url['uid'][0])
                months = int(parsed_url['months'][0])
                sumrub = int(parsed_url['sum'][0])
                security = str(parsed_url['hash'][0])
                param_str = '&{0}&{1}&{2}&{3}'.format(str(user_id), str(months), str(sumrub), botsecret)
                hash_sha1 = hashlib.sha1()
                hash_sha1.update(param_str.encode('utf-8'))
                computed_hash = str(hash_sha1.hexdigest())
                print(security, computed_hash)
                if computed_hash == security:
                    invoice_label = '{0}:{1}'.format(user_id, computed_hash)
                    base_page = open('payment_form.html', 'r').read()
                    generated_page = re.sub('%DEFAULTSUM%', str(sumrub), base_page)
                    generated_page = re.sub('%USERID%', str(user_id), generated_page)
                    generated_page = re.sub('%TRANSACTIONLABEL%', str(invoice_label), generated_page)
                    generated_page = re.sub('%YMACCOUNTID%', str(ym_account_id), generated_page)
                else:
                    generated_page = open('hash_error.html', 'r').read()
                self.wfile.write(generated_page.encode('utf-8'))
            elif page_type == 'donate':
                base_page = open('donate_form.html', 'rb').read()
                self.wfile.write(base_page)
            else:
                self.send_response(403)
        except Exception:
            self.send_response(403)

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        input_data = post_data.decode('utf-8')
        parsed_data = parse.parse_qs(input_data)
        shared_secret = ymsecret
        # notification_type & operation_id & amount & currency & datetime & sender & codepro & notification_secret &
        # label
        operation_id = '{}'.format(parsed_data['operation_id'][0])
        datetime = '{}'.format(parsed_data['datetime'][0])

        verify_str = '{}&'.format(parsed_data['notification_type'][0])
        verify_str += '{}&'.format(parsed_data['operation_id'][0])
        verify_str += '{}&'.format(parsed_data['amount'][0])
        verify_str += '{}&'.format(parsed_data['currency'][0])
        verify_str += '{}&'.format(parsed_data['datetime'][0])
        verify_str += '{}&'.format(parsed_data['sender'][0])
        verify_str += '{}&'.format(parsed_data['codepro'][0])
        verify_str += '{}&'.format(shared_secret)
        try:
            invoice_label = '{}'.format(parsed_data['label'][0])
        except Exception:
            invoice_label = ''
        verify_str += invoice_label
        hash_sha1 = hashlib.sha1()
        hash_sha1.update(verify_str.encode('utf-8'))
        computed_hash = str(hash_sha1.hexdigest())
        incoming_hash = parsed_data['sha1_hash'][0]
        print(incoming_hash, computed_hash)

        # logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
        #         str(self.path), str(self.headers), post_data.decode('utf-8'))
        # post_data_last = post_data
        if incoming_hash == computed_hash:
            job_dl = q_billing.enqueue(billing_service.successful_payment_callback, invoice_label, operation_id,
                                       datetime)
            while job_dl.result is None:
                job_dl.refresh()
                if job_dl.is_failed:
                    raise Exception
            print(post_data.decode('utf-8'))
            self.send_response(200)
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=S, port=443):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='/etc/letsencrypt/live/yourdomain.xyz/privkey.key',
                                   certfile='/etc/letsencrypt/live/yourdomain.xyz/certificate.crt', server_side=True)
    print('Starting httpd...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
