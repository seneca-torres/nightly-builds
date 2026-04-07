import unittest

from bot.security import CallbackError, make_callback_data, parse_and_verify_callback_data


class SecurityTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        data = make_callback_data(
            secret="secret",
            template_index=2,
            action_index=1,
            ttl_seconds=900,
            now=1_700_000_000,
        )
        parsed = parse_and_verify_callback_data(data, secret="secret", now=1_700_000_001)
        self.assertEqual(parsed.template_index, 2)
        self.assertEqual(parsed.action_index, 1)

    def test_expired(self) -> None:
        data = make_callback_data(
            secret="secret",
            template_index=0,
            action_index=0,
            ttl_seconds=60,
            now=100,
        )
        with self.assertRaises(CallbackError):
            parse_and_verify_callback_data(data, secret="secret", now=10_000)

    def test_tamper(self) -> None:
        data = make_callback_data(
            secret="secret",
            template_index=0,
            action_index=0,
            ttl_seconds=900,
            now=1_700_000_000,
        )
        tampered = data[:-1] + ("A" if data[-1] != "A" else "B")
        with self.assertRaises(CallbackError):
            parse_and_verify_callback_data(tampered, secret="secret", now=1_700_000_001)


if __name__ == "__main__":
    unittest.main()

