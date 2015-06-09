import datetime
import time
import json

from dateutil.relativedelta import relativedelta

from django import http, db
from django.conf import settings
from django.views.generic.base import TemplateView, View
from django.utils import timezone
from aiot_dashboard.apps.db.models import Room, PowerCircuit, TsKwm, TsKwh
from django.db.models.aggregates import Sum, Max


class DisplayView(TemplateView):
    template_name = "display/display.html"

    def get_context_data(self, **kwargs):
        data = TemplateView.get_context_data(self, **kwargs)
        data['model_token'] = settings.BIMSYNC_TOKEN
        return data


# Base class for server side event update streams.
class SseUpdateView(View):
    last_poll = datetime.datetime(2010, 1, 1)

    def dispatch(self, request):
        response = http.StreamingHttpResponse(streaming_content=self.iterator(request=request), content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        return response

    def iterator(self, request):
        start = timezone.now()
        while timezone.now() - start < settings.SSE_MAX_TIME:
            data = self.get_updates()
            if data:
                yield "data: %s\n" % json.dumps(data)
                yield "\n"

            if settings.DEBUG:
                # Prevents a memory leak on dev
                db.reset_queries()

    def get_updates(self):
        time.sleep(1)
        return None


class DataSseView(SseUpdateView):
    rooms = []
    last_power = None

    def get_updates(self):
        if len(self.rooms) == 0:
            self.rooms = Room.get_active_rooms()

        data = self._build_rooms([])
        data = self._build_power(data)
        time.sleep(1)
        return data

    def _build_rooms(self, data=[]):
        for room in self.rooms:
            data.append({
                'type': 'room',
                'key': room.key,
                'name': room.name,
                'occupied': room.is_occupied(),
                'co2': room.current_co2(),
                'temperature': room.current_temperature(),
                'productivity': "%s%%" % room.current_productivity(),
                'deviations': {
                    'temperature': room.deviation_minutes('temperature'),
                    'co2': room.deviation_minutes('co2'),
                    'humidity': room.deviation_minutes('humidity')
                }
            })
        return data

    def _build_power(self, data=[]):
        if not self.last_power or datetime.datetime.utcnow() - self.last_power > datetime.timedelta(minutes=1):
            circuits = []
            for circuit in PowerCircuit.objects.all().prefetch_related('devices'):
                circuits.append({
                    'name': circuit.name,
                    'kwh': self._build_kwh_for_devices(circuit.devices.all())
                })
            data.append({
                'type': 'power',
                'circuits': circuits,
                'total': self._build_kwh_for_devices(None),
                'max_month': self._build_max_kwh()
            })
            self.last_power = datetime.datetime.utcnow()
        return data

    def _get_today(self):
        now = timezone.now()
        return datetime.datetime(now.year, now.month, now.day).replace(tzinfo=now.tzinfo)

    def _build_kwh_for_devices(self, devices=None):
        today = self._get_today()
        data = []

        for h in range(7, 18):
            dte = today + datetime.timedelta(hours=h)
            qs = TsKwm.objects.filter(datetime__gte=dte,
                                      datetime__lt=dte + datetime.timedelta(hours=1))
            if devices:
                qs = qs.filter(device_key__in=devices)
            val = qs.aggregate(Sum('value'))['value__sum']
            if not val:
                val = 0
            data.append([h, val])
        return data

    def _build_max_kwh(self):
        today = self._get_today()
        month_start = datetime.datetime(today.year, today.month, 1)
        qs = TsKwh.objects.filter(datetime__gte=month_start,
                                  datetime__lt=month_start + relativedelta(months=1))
        val = qs.aggregate(Max('value'))['value__max']
        return val if val else 0
