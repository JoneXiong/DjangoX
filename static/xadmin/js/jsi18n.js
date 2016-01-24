
/* gettext identity library */

function gettext(msgid) { return msgid; }
function ngettext(singular, plural, count) { return (count == 1) ? singular : plural; }
function gettext_noop(msgid) { return msgid; }
function pgettext(context, msgid) { return msgid; }
function npgettext(context, singular, plural, count) { return (count == 1) ? singular : plural; }

function interpolate(fmt, obj, named) {
  if (named) {
    return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
  } else {
    return fmt.replace(/%s/g, function(match){return String(obj.shift())});
  }
}

/* formatting library */

var formats = new Array();

formats['DATETIME_FORMAT'] = 'Y-m-d H:i';
formats['DATE_FORMAT'] = 'Y-m-d';
formats['DECIMAL_SEPARATOR'] = '.';
formats['MONTH_DAY_FORMAT'] = 'F j';
formats['NUMBER_GROUPING'] = '0';
formats['TIME_FORMAT'] = 'H:i';
formats['FIRST_DAY_OF_WEEK'] = '0';
formats['TIME_INPUT_FORMATS'] = ['%H:%M:%S', '%H:%M'];
formats['THOUSAND_SEPARATOR'] = ',';
formats['DATE_INPUT_FORMATS'] = ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%b %d %Y', '%b %d, %Y', '%d %b %Y', '%d %b, %Y', '%B %d %Y', '%B %d, %Y', '%d %B %Y', '%d %B, %Y'];
formats['YEAR_MONTH_FORMAT'] = 'F Y';
formats['SHORT_DATE_FORMAT'] = 'm/d/Y';
formats['SHORT_DATETIME_FORMAT'] = 'm/d/Y P';
formats['DATETIME_INPUT_FORMATS'] = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S.%f', '%m/%d/%Y %H:%M', '%m/%d/%Y', '%m/%d/%y %H:%M:%S', '%m/%d/%y %H:%M:%S.%f', '%m/%d/%y %H:%M', '%m/%d/%y'];

function get_format(format_type) {
    var value = formats[format_type];
    if (typeof(value) == 'undefined') {
      return format_type;
    } else {
      return value;
    }
}
