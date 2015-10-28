# main webservice for the ironmap 
# dewandaru@gmail.com
# development notes:
# for production, run this script using #./runwsgi.sh 
# for debug, run this script using #python parser.py runserver -d, it will listen by default on port 5000

# dependencies::
# pip install Flask
# sudo apt-get install python-dev
# pyCrpto package 
# wikipedia package
# pip install Flask-Mail

# HOWTO modify database
# root@dewalabs:~/wikip python
# Python 2.7.6 (default, Mar 22 2014, 22:59:56)
# [GCC 4.8.2] on linux2
# Type "help", "copyright", "credits" or "license" for more information.
# >>> from db import *
# >>> init()
# >>> quit()
# root@dewalabs:~/wikip sqlite3 data.sqlite
# SQLite version 3.8.2 2013-12-06 14:53:30
# Enter ".help" for instructions
# Enter SQL statements terminated with a ";"
# sqlite> .read users.sql
# 
# also look at
# http://stackoverflow.com/questions/75675/how-do-i-dump-the-data-of-some-sqlite3-tables
# especially
# .mode insert <target_table_name>
# .out file.sql 
# select * from emp
# 


from flask import Flask, request, session
import wikipedia
from flask import Response
from xml.sax.saxutils import escape
import StringIO
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from pkcs7 import PKCS7Encoder
import base64
from db import *
from flask import render_template
from time import time
from flask.ext.mail import Mail
from flask.ext.mail import Message
import requests
from werkzeug.datastructures import ImmutableOrderedMultiDict
from validate_email import validate_email
from sqlalchemy import desc, asc


API_KEY = "0c_87FjjjaS"
app = Flask ( __name__ , static_folder = 'static' , static_url_path = '' )
app.secret_key = 'ironmap_key_1234'
mailer = Mail(app)

def enc ( text ):
    key = 'ironmap_key_1234'
    # 16 byte initialization vector
    iv = '1234567812345678'

    aes = AES.new ( key, AES.MODE_CBC, iv )
    encoder = PKCS7Encoder ()

    # pad the plain text according to PKCS7
    pad_text = encoder.encode ( text )

    # encrypt the padding text
    cipher = aes.encrypt ( pad_text )

    # base64 encode the cipher text for transport
    enc_cipher = base64.urlsafe_b64encode ( cipher )
    return enc_cipher

def xmlencrypt ( text ):
    enc_cipher = enc ( text )
    return "<xml><![CDATA[" + enc_cipher + "]]></xml>"

# just like xmlencrypt () but saves to database for registration
def xmlgrant ( email, license_name ):
    result = fgrant ( email, license_name )
    return "<xml><license><![CDATA[" + result + "]]></license></xml>"

def fgrant ( email, license_name ):
    print "Granting for " + license_name + " (" + email + ")"
    time_str = str( time () )
    enc_cipher = enc ( str ( email ) + ":" + license_name + ":" + time_str[-3:] )
    new_user = User ( email = email, license = enc_cipher, active = True, creationtime = datetime.now () )
    db.session.add ( new_user )
    db.session.commit ()
    mail ( email, license_name, enc_cipher )
    return enc_cipher

def mail ( target_email, license_name, license ):
    msg = Message ( "License for Touchmapper",
                  sender="touchmapper@touchmapper.com",
                  recipients=[target_email] )

    msg.body = "Hi " + license_name + ", Thank you for the purchase. \r\n Your license for Touchmapper app is ready. Copy and paste the code below into the app when requested. Or simply tap Info menu, and then tap Registration.\r\n\r\n" + license + "\r\n\r\nTouchmapper team"
    msg.html = "Hi " + license_name + ", Thank you for the purchase. <br> Your license for Touchmapper app is ready. Copy and paste the code below into the app when requested. Or simply tap Info menu, and then tap Registration.<br><br>" + license + "<br><br>Touchmapper team"
    mailer.send(msg)

def dec ( cipher ):
    key = 'ironmap_key_1234'
    # 16 byte initialization vector
    iv = '1234567812345678'

    aes = AES.new ( key, AES.MODE_CBC, iv )
    encoder = PKCS7Encoder ()

    cipher = base64.urlsafe_b64decode ( str ( cipher ) )

    # decrypt the cipher
    pad_plaintext = aes.decrypt ( cipher )

    # base64 decode the cipher text for transport
    plaintext = encoder.decode ( pad_plaintext )
    return plaintext

def xmldecrypt ( cipher ):
    plaintext = dec ( cipher )
    return "<xml><![CDATA[" + plaintext + "]]></xml>"

def xmlrelease ( ):
    r = Release.query.order_by( desc(Release.time) ).first ()
    return "<xml><url>" + r.url + "</url><build>" + r.build + "</build><feature><![CDATA[" + r.feature + "]]></feature></xml>"


def xmlwiki ( title ):
    xml = unicode ( "<xml>" )
    try: 
        #this is non-ambiguous
        page = wikipedia.page ( title, auto_suggest = True, redirect = True )
        xml = xml + "<title>" + escape ( unicode ( page.title ) ) + "</title>"
        xml = xml + "<summary>" + escape ( unicode ( page.summary ) ) + "</summary>"
        for s in page.sections:
            soup = BeautifulSoup (s)
            title = soup.get_text ()
            section = unicode ( page.section ( title ) )
            xml = xml + "<section><title>" + escape ( unicode ( title ) ) + "</title>"
            xml = xml + "<content>" + escape ( section ) + "</content></section>"

        for l in page.images:
            xml = xml + "<image>" + escape ( l ) + "</image>"
        xml = xml + "</xml>"

    except wikipedia.exceptions.DisambiguationError as e:
        #this is ambiguous
        buf = StringIO.StringIO (e)
        LINES = buf.readlines ()
        LINES.pop(  0 )  # remove first line
        LINES.pop( -1 ) # remov last three lines as well
        LINES.pop( -1 )
        LINES.pop( -1 )
        xml = xml + "<title>" + escape ( title ) + "</title>"
        xml = xml + "<summary>article options(tap to browse)</summary>"

        for a in LINES:
            b = a.decode ('utf-8') 

            xml = xml + "<article>" + escape( b.strip () ) + "</article>"
        xml = xml + "</xml>"

    except ( wikipedia.exceptions.PageError, KeyError, TypeError ) as e:
        xml = xml + "<error /></xml>"

    return xml

def getsiteinfo ( url ):
    import requests
    r  = requests.get ( "http://" + url ) 
    data = r.text
    soup = BeautifulSoup(data)
    xml = unicode ( "<xml>" )

    # First get the meta description tag
    description = soup.find( 'meta', attrs = {' name':'og:description' } ) or soup.find( 'meta', attrs={ 'property':'description' } ) or soup.find ( 'meta', attrs={'name':'description'} )

    content_desc = ""
    # If description meta tag was found, then get the content attribute and save it to db entry
    if description:
        content_desc = description.get('content')
    xml = xml + escape ( content_desc ) + "</xml>"
    return xml

def openfile ( id ):
    try:
        file = open( './files/' + id + ".xml", 'r' )
        result = file.read ()
    except IOError:
        result = "<xml><error>IOError</error></xml>"
    return result

def sharefile ( content, id ):
    if id == '':
        id = getnewid ()
    filename = "files/" + id + ".xml"
    writefile ( filename, content )
    xml = unicode("<xml>")
    xml = xml + "<status>OK</status>"
    xml = xml + "<id>" + id + "</id>"
    xml = xml + "</xml>"
    return xml

def getnewid ():
    import uuid
    return str ( uuid.uuid1 () )

def writefile ( filename, content ):
    file = open ( filename, "w" )
    file.write ( content.encode ( 'utf-8' ) )
    file.close ()

def invalid ( license ):
    try:
        ip = request.remote_addr
        user = User.query.filter_by ( license = license ).first ()
        if ( user is None ):
            return True
        else:
            access = Access ( ip = ip, time = datetime.now (), user_id = user.id )
            db.session.add ( access )
            db.session.commit ()
            return not user.active         
    except:
        return True

'''
THESE ARE THE APP ROUTES.
'''
@app.route ( '/' )
def index ():
    return render_template( 'index.html' )

@app.route ( '/buy' )
def buy ():
    return render_template( 'buy.html')

@app.route ( '/download' )
def download ():
    return render_template( 'download.html')

@app.route ( '/success' )
def success ():
    return render_template( 'success.html')


@app.route ( '/cancel' )
def cancel ():
    return render_template( 'cancel.html' )


#@app.route ( '/' )
#def 
    #return redirect ( url_for ( 'static', filename = 'crossdomain.xml' ) )

# perform IPN listener. this must be set in paypal ("profile -> my selling tools -> instant payment notifications") before.
# you can test this using PP account/password
# betastamp_paypal@gmail.com / betastamper ==> PP balance 9999
# betastamp_paypal01@gmail.com / betastamper ==> PP balance 9999 

@app.route( '/ipn', methods = ['POST'] )
def ipn():
 
    arg = ''
    #: We use an ImmutableOrderedMultiDict item because it retains the order.
    request.parameter_storage_class = ImmutableOrderedMultiDict
    values = request.form
    for x, y in values.iteritems ():
        arg += "&{x}={y}".format ( x = x, y = y )
 
    validate_url = 'https://www.sandbox.paypal.com' \
                   '/cgi-bin/webscr?cmd=_notify-validate{arg}' \
                   .format ( arg = arg )
                  
    print 'Validating IPN using {url}'.format ( url = validate_url )
 
    r = requests.get( validate_url )
 
    if r.text == 'VERIFIED':
        print "PayPal transaction was verified successfully."

        try:
            # Do something with the verified transaction details.
            payer_email =  request.form.get ( 'payer_email' )
            payer_name =  request.form.get ( 'first_name' )
            print "Pulled {email} from transaction".format ( email = payer_email )
            txn_id =  request.form.get ( 'txn_id' )
            ipn = IPN ( payer_email = payer_email, txn_id = txn_id, creationtime = datetime.now () )
            db.session.add ( ipn )
            db.session.commit ()

            license_email = request.form.get ( 'option_selection1' )
            license_name = request.form.get ( 'option_selection2' )
            print license_name
            print license_email
            license = fgrant ( license_email, license_name )
            session['license'] = license
            session['license_email'] = license_email
            session['license_name'] = license_name
          
        except Exception as e:
            print  e

    else:
        print 'Paypal IPN string {arg} did not validate'.format ( arg = arg )
 
    return r.text

#use to retrive wiki structure and content about a particular title.
@app.route ( '/wiki/<title>/<license>')
def wiki ( title, license ):
    if ( invalid ( license ) ): 
        return Response ( "<xml><error>Invalid License</error></xml>", mimetype = 'text/xml' )
    else: 
        return Response ( xmlwiki ( title ), mimetype = 'text/xml' )

@app.route ( '/release' )
def release ():
    return Response ( xmlrelease ( ), mimetype = 'text/xml' )


#use to retrieve information about particular site/URL
@app.route ( '/site/<url>/<license>' )
def site ( url, license ):
    if ( invalid ( license ) ): 
        return Response ( "<xml><error>Invalid License</error></xml>", mimetype = 'text/xml' )
    else: 
        return Response ( getsiteinfo ( url ), mimetype = 'text/xml' )

#use to open shared document. only accept id. no need for license. 
@app.route ( '/open/<id>' )
def _open ( id ):
    return Response ( openfile ( id ), mimetype = 'text/xml' )

#use to share document. pass content as POST variable 'content', then it will give the ID to be use for subsequent update.
@app.route ( '/share/<license>', methods = [ 'POST' ] )
def share ( license ):
    if ( invalid ( license ) or ( license == "null" ) ): 
        return Response ( "<xml><error>Invalid License</error></xml>", mimetype = 'text/xml' )
    else:
        content = request.form [ 'content' ]
        id = request.form [ 'id' ]
        return Response ( sharefile ( content, id ), mimetype = 'text/xml' )



# @app.route('/save/', methods=['GET'])
# def site(url):
#     id = requests.args.get('id')
#     content = request.args.get('body')
#     return Response(savefile(id, content), mimetype='text/xml')

# these functions is for development and/or paypal code.

@app.route ( '/encrypt/<text>/<key>' )
def encrypt ( text, key ):
    if ( key == API_KEY ):
        return Response ( xmlencrypt ( text ), mimetype = 'text/xml' )
    else:
        return Response ( "<xml><error>Invalid Key</error></xml>", mimetype = 'text/xml' )

@app.route ( '/decrypt/<cipher>/<key>')
def decrypt ( cipher, key ):
    if ( key == API_KEY ):
        return Response ( xmldecrypt ( cipher ), mimetype = 'text/xml' )
    else:
        return Response ( "<xml><error>Invalid Key</error></xml>", mimetype = 'text/xml' )

@app.route ( '/grant/<email>/<license_name>/<key>' )
def grant ( email, license_name, key ):
    if ( key == API_KEY ):
        return Response ( xmlgrant ( email, license_name ), mimetype = 'text/xml' )
    else:
        return Response ( "<xml><error>Invalid Key</error></xml>", mimetype = 'text/xml' )


#print getsiteinfo("kompas.com")

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    app.run( host = '0.0.0.0', debug = True )