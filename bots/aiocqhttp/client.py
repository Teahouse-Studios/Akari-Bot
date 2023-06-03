import traceback

bot = CQHttp()
from aiocqhttp.event import Event


class EventModded(Event):
    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> 'Optional[Event]':
        """
        �� OneBot �¼����ݹ��� `Event` ����
        """
        try:
            e = EventModded(payload)
            _ = e.type, e.detail_type
            return e
        except KeyError:
            traceback.print_exc()
            return None

    @property
    def detail_type(self) -> str:
        """
        �¼��������ͣ��� `type` �Ĳ�ͬ����ͬ���� ``message`` ����Ϊ������
        ``private``��``group``��``discuss`` �ȡ�
        """
        if self.type == 'message_sent':
            return self['message_type']
        return self[f'{self.type}_type']


class CQHttpModded(CQHttp):

    async def _handle_event(self, payload: Dict[str, Any]) -> Any:
        ev = EventModded.from_payload(payload)
        if not ev:
            return

        event_name = ev.name
        self.logger.info(f'received event: {event_name}')

        if self._message_class and 'message' in ev:
            ev['message'] = self._message_class(ev['message'])
        results = list(
            filter(lambda r: r is not None, await
                   self._bus.emit(event_name, ev)))
        # return the first non-none result
        return results[0] if results else None


bot = CQHttpModded()
