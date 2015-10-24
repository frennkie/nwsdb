# -*- coding: utf-8 -*-
"""Nmap Forms"""
# nmap Forms
from django import forms
from .models import OrgUnit

import re
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
#from django.core.validators import RegexValidator

#from crispy_forms.helper import FormHelper


SCAN_TYPE_CHOICES = (
    (1, "Connect Scan"),
    (2, "Syn Scan"),
    (3, "Ack Scan"),
    (4, "Window Scan"),
    (5, "Maimon Scan"),
    (6, "Null Scan"),
    (7, "Fin Scan"),
    (8, "Xmas Scan"),
    (9, "UDP Scan"),
)

class ScanForm(forms.Form):
    """ScanForm
        TODO look into:
        https://docs.djangoproject.com/en/1.8/topics/forms/modelforms/
        https://docs.djangoproject.com/en/1.8/ref/forms/api/
        required is True by default
    """

    def clean(self):
        """From clean (field validation is already done by now)"""
        cleaned_data = super(ScanForm, self).clean()
        top_ports = cleaned_data.get("top_ports")
        ports = cleaned_data.get("ports")
        if top_ports and ports:
            raise ValidationError(
                ("""Please use either Top Ports or Manual selection!
                 You specified both Top Ports (%(top_ports)s) and Manual
                 Selection (%(ports)s)"""),
                code="invalid",
                params={"top_ports": top_ports, "ports": ports},
            )
        # Always return the full collection of cleaned data.
        return cleaned_data

    targets = forms.CharField(label="Targets",
                              max_length=100,
                              help_text="""specify the ip, subnet or domain to scan""",
                              widget=forms.TextInput(
                                  attrs={"placeholder": "Targets",
                                         "autofocus": True}))

    def clean_targets(self):
        """demo mode only allows localhost, 127.0.0.1, ::1"""
        targets = self.cleaned_data['targets']
        if targets == "localhost" or targets == "127.0.0.1" or targets == "::1":
            return targets
        else:
            raise ValidationError(
                ("Demo mode: Only localhost is permitted! Not: %(targets)s"),
                code="invalid",
                params={"targets": targets},
            )


    comment = forms.CharField(label="Comment",
                              max_length=100,
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'placeholder': 'Comment'}))

    no_ping = forms.BooleanField(label="Do not ping target(s)",
                                 required=False)

    banner_detection = forms.BooleanField(label="Enable banner grabbing",
                                          required=False)

    os_detection = forms.BooleanField(label="Enable OS Detection",
                                      required=False)

    run_now = forms.BooleanField(label="Run now", initial=True, required=False)
    run_now.widget.attrs['disabled'] = True

    top_ports = forms.IntegerField(label="""Top Ports: Scan how many of the top ports""",
                                   required=False,
                                   help_text="""Specifiy either Top Ports (above)
                                       or use Manual Selection (below)""",
                                   validators=[MaxValueValidator(10000),
                                               MinValueValidator(1),],
                                   widget=forms.TextInput(
                                       attrs={"placeholder": """e.g. 10 or 100 (max: 10000)"""}))


    ports = forms.CharField(label="""Manual Selection: Specify ports (and ranges)""",
                            max_length=100,
                            required=False,
                            widget=forms.TextInput(attrs={'placeholder': 'e.g. 80,443,21-25'}))

    def clean_ports(self):
        """The ports field accepts comma seperated ports and also ranges
            declared as: low_port-high_port (e.g. 21-25)
            This function expands ranges and puts all into a sorted list
        """

        _ports = self.cleaned_data['ports']
        if len(_ports) == 0:
            return None

        _ports = _ports.replace(" ", "")

        if not re.match("^[0-9,-]*$", _ports):
            raise ValidationError(
                ("Invalid characters in field Ports: %(_ports)s"),
                code="invalid",
                params={"_ports": _ports},
            )

        _port_list = _ports.split(",")
        port_set = set()

        for item in _port_list:
            if item.count("-") == 0:
                port_set.add(str(item))
            elif item.count("-") == 1:
                _split = item.split("-")

                if len(_split[0]) < 1:
                    raise ValidationError(
                        ("Invalid negative port: %(port)s"),
                        code="invalid",
                        params={"port": item},
                    )

                _range = range(int(_split[0]), int(_split[1]) + 1)

                for port in _range:
                    port_set.add(str(port))

            else:
                raise ValidationError(
                    ("Invalid range in field Ports: %(port)s"),
                    code="invalid",
                    params={"port": item},
                )

        port_list = list(port_set)
        port_list.sort()

        for item in port_list:
            if int(item) > 65535:
                raise ValidationError(
                    ('Invalid port > 65535: %(port)s'),
                    code='invalid',
                    params={'port': item},
                )

        if len(port_list) > 10000:
            raise ValidationError(
                ("Too many Ports: %(port_count)s"),
                code="invalid",
                params={"port_count": len(port_list)},
            )

        ports = ",".join(port_list)

        return ports


    scan_type = forms.IntegerField(label="Scan Type",
                                   widget=forms.Select(
                                       choices=SCAN_TYPE_CHOICES))


    org_unit = forms.ModelChoiceField(queryset=OrgUnit.objects.all(),
                                      label="Org Unit",
                                      empty_label=None)


# EOF
