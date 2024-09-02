# This is a workaround

Djoser does not work fine with djmail.
GitHub similar issue with django mailer: https://github.com/sunscrapers/djoser/issues/609

# Workaround

To bypass the issue, we are importing our own `djoser_alf.urls`, which calls `djoser_alf.views` and the view is a replica of djoser views but
overriding the djmail by `override_settings(EMAIL_BACKEND=settings.DJMAIL_REAL_BACKEND)`

# Ideally

Ideally, we upgrade (or make a fix PR) djoser version which wouldn't have this issue.

# Attempts (without success):

## Use different versions of djoser and djmail

Downgrading djmail didn't have much success even going to very old versions
Downgrading djoser neither. Versions 1.X.X are not compatible with more recent rest framework versions, so we couldn't downgrade much.

## Use newer versions of python

The idea was to check if pickle was able to encode/decode *_io.BufferedReader*, but no success.

* Python 3.10 didn't work
* Python 3.11 was not supported for recent versions of aweber and virtru-sdk

And later checked the documentation and it doesn't seems pickle was improved in more recent versions.

# Versions

* Python 3.9.7
* djoser 2.2.0
    * django-templated-mail 1.1.1
* djmail 2.0.0
