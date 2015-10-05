from jinja2 import Markup
import datetime


class momentjs(object):
    def __init__(self, timestamp):
        if isinstance(timestamp, int) and timestamp:
            self.timestamp = datetime.datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str) and timestamp:
            self.timestamp = datetime.datetime.fromtimestamp(int(timestamp))
        elif isinstance(timestamp, unicode) and timestamp:
            self.timestamp = datetime.datetime.fromtimestamp(int(float(timestamp)))
        elif isinstance(timestamp, datetime.datetime) and timestamp:
            self.timestamp = timestamp
        else:
            _rstr = ''
            try:
                _rstr = datetime.datetime.fromtimestamp(int(timestamp))
            except ValueError:
                _rstr = None
            self.timestamp = _rstr

    # Wrapper to call moment.js method
    def render(self, format):
        if self.timestamp:
            return Markup("<script>\ndocument.write(moment(\"%s\").%s);\n</script>" % (self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"), format))
        else:
            return Markup("Unknown")

    # Format time
    def format(self, fmt):
        return self.render("format(\"%s\")" % fmt)

    def calendar(self):
        return self.render("calendar()")

    def fromNow(self):
        return self.render("fromNow()")
