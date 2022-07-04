from email import message
import os

from monitor.models import Log

from library import emailer

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def debug(source, level, msg):
    if level == 0:
        # Log.objects.create(
        #     source=source,
        #     level="Info",
        #     message="INFO: " + msg
        # )
        print("INFO: " + msg)
    elif level == 1:
        Log.objects.create(
            source=source,
            level="Warning",
            message="WARNING: " + msg
        )
        print("WARNING: " + msg)
    else:
        Log.objects.create(
            source=source,
            level="Error",
            message="ERROR: " + msg
        )
        print("ERROR: " + msg)

        ##########################################
        ################## Email #################
        ##########################################
        bodyText = "<h3><strong>Error Source: {} Robot</strong></h3>".format(
            source)
        bodyText += "<p style='color: red;'><strong>{}</strong></p><br/>".format(
            msg)
        emailer.send_email_html("IMS Monitor",
                                "murrell@decoratorsbest.com", "IMS Alert", bodyText)
