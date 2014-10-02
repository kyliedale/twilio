from unittest.mock import patch, MagicMock
from ..sms_block import TwilioSMS, TwilioRestException
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.common.signal.base import Signal
from nio.modules.threading import Event
from time import sleep


class EventSignal(Signal):
    def __init__(self, event=None):
        super().__init__()
        self._event = event or Event()


class FlavorSignal(Signal):
    def __init__(self, flavor):
        super().__init__()
        self.flavor = flavor


class EventFlavorSignal(Signal):
    def __init__(self, flavor, event=None):
        super().__init__()
        self._event = event or Event()
        self.flavor = flavor


class TestQueue(NIOBlockTestCase):

    def test_sms(self):
        e = Event()
        signals = [EventSignal(e)]
        blk = TwilioSMS()
        config = {
            'recipients': [
                {'name': 'Snoopy', 'number': '5558675309'}
            ],
            'message': 'hi'
        }
        self.configure_block(blk, config)
        blk._client.messages.create = MagicMock()
        blk.start()
        blk.process_signals(signals)
        sleep(1)
        blk._client.messages.create.assert_called_once_with(to='5558675309',
                                                            from_='',
                                                            body='Snoopy: hi')
        self.assertEqual(1, blk._client.messages.create.call_count)
        blk.stop()

    def test_sms_retry(self):
        e = Event()
        signals = [EventSignal(e)]
        blk = TwilioSMS()
        config = {
            'recipients': [
                {'name': 'Snoopy', 'number': '5558675309'}
            ],
            'message': 'hi'
        }
        self.configure_block(blk, config)
        blk._client.messages.create = MagicMock(
            side_effect=TwilioRestException(status=400, uri='bad')
        )
        blk._logger.error = MagicMock()
        blk.start()
        blk.process_signals(signals)
        sleep(1)
        self.assertEqual(2, blk._client.messages.create.call_count)
        self.assertEqual(3, blk._logger.error.call_count)
        blk.stop()

    def test_sms_exception(self):
        e = Event()
        signals = [EventSignal(e)]
        blk = TwilioSMS()
        config = {
            'recipients': [
                {'name': 'Snoopy', 'number': '5558675309'}
            ],
            'message': 'hi'
        }
        self.configure_block(blk, config)
        blk._client.messages.create = MagicMock(
            side_effect=Exception('could not create message')
        )
        blk._logger.error = MagicMock()
        blk.start()
        blk.process_signals(signals)
        sleep(1)
        self.assertEqual(1, blk._client.messages.create.call_count)
        self.assertEqual(1, blk._logger.error.call_count)
        blk._logger.error.assert_called_once_with(
            "Error sending SMS to Snoopy (5558675309): could not create message"
        )
        blk.stop()

    def test_message_exception(self):
        e = Event()
        signals = [EventSignal(e)]
        blk = TwilioSMS()
        config = {
            'recipients': [
                {'name': 'Snoopy', 'number': '5558675309'}
            ],
            'message': '{{"hi" + 1}}'
        }
        self.configure_block(blk, config)
        blk._logger.error = MagicMock()
        blk.start()
        blk.process_signals(signals)
        sleep(1)
        self.assertEqual(1, blk._logger.error.call_count)
        blk._logger.error.assert_called_once_with(
            "Message evaluation failed: "
            "TypeError: Can't convert 'int' object to str implicitly"
        )
        blk.stop()
