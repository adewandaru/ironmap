uwsgi --socket 127.0.0.1:3031 --wsgi-file /root/wikip/parser.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191 --pidfile=/tmp/wikip --py-autoreload 1 --daemonize=/tmp/wikip_daemonize
